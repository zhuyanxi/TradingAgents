"""Job management: create, start, and stream real-time analysis events over SSE."""

import asyncio
import ast
import datetime
import json
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from cli.stats_handler import StatsCallbackHandler


# ---------------------------------------------------------------------------
# Utilities copied from cli/main.py to avoid pulling in heavy CLI deps
# ---------------------------------------------------------------------------

ANALYST_ORDER = ["market", "social", "news", "fundamentals"]
ANALYST_AGENT_NAMES = {
    "market": "Market Analyst",
    "social": "Social Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
}
ANALYST_REPORT_MAP = {
    "market": "market_report",
    "social": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
}

SECTION_TITLES = {
    "market_report":          "Market Analysis",
    "sentiment_report":       "Social Sentiment",
    "news_report":            "News Analysis",
    "fundamentals_report":    "Fundamentals Analysis",
    "investment_plan":        "Research Team Decision",
    "trader_investment_plan": "Trading Team Plan",
    "final_trade_decision":   "Portfolio Management Decision",
}

FIXED_AGENTS = {
    "Research Team":      ["Bull Researcher", "Bear Researcher", "Research Manager"],
    "Trading Team":       ["Trader"],
    "Risk Management":    ["Aggressive Analyst", "Neutral Analyst", "Conservative Analyst"],
    "Portfolio Management": ["Portfolio Manager"],
}

REPORT_SECTIONS_DEF = {
    "market_report":          ("market",       "Market Analyst"),
    "sentiment_report":       ("social",        "Social Analyst"),
    "news_report":            ("news",          "News Analyst"),
    "fundamentals_report":    ("fundamentals",  "Fundamentals Analyst"),
    "investment_plan":        (None,            "Research Manager"),
    "trader_investment_plan": (None,            "Trader"),
    "final_trade_decision":   (None,            "Portfolio Manager"),
}


def _is_empty(val: Any) -> bool:
    if val is None or val == "":
        return True
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return True
        try:
            return not bool(ast.literal_eval(s))
        except (ValueError, SyntaxError):
            return False
    return not bool(val)


def _extract_content(content: Any) -> Optional[str]:
    if _is_empty(content):
        return None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, dict):
        text = content.get("text", "")
        return text.strip() if not _is_empty(text) else None
    if isinstance(content, list):
        parts = [
            item.get("text", "").strip()
            if isinstance(item, dict) and item.get("type") == "text"
            else (item.strip() if isinstance(item, str) else "")
            for item in content
        ]
        result = " ".join(t for t in parts if t and not _is_empty(t))
        return result if result else None
    return str(content).strip() if not _is_empty(content) else None


def _classify_message(message) -> tuple[str, Optional[str]]:
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    content = _extract_content(getattr(message, "content", None))
    if isinstance(message, HumanMessage):
        if content and content.strip() == "Continue":
            return ("Control", content)
        return ("User", content)
    if isinstance(message, ToolMessage):
        return ("Data", content)
    if isinstance(message, AIMessage):
        return ("Agent", content)
    return ("System", content)


# ---------------------------------------------------------------------------
# Job model
# ---------------------------------------------------------------------------

@dataclass
class Job:
    job_id: str
    request: dict
    created_at: float = field(default_factory=time.time)
    status: str = "pending"     # pending | running | completed | error
    error: Optional[str] = None
    decision: Optional[str] = None
    complete_report: Optional[str] = None
    _loop: Optional[asyncio.AbstractEventLoop] = field(default=None, init=False, repr=False)
    _queue: Optional[asyncio.Queue] = field(default=None, init=False, repr=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _last_message_id: Optional[str] = field(default=None, init=False, repr=False)
    _agent_status: dict = field(default_factory=dict, init=False, repr=False)
    _report_sections: dict = field(default_factory=dict, init=False, repr=False)

    def _attach_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._queue = asyncio.Queue()

    def emit(self, event_type: str, data: Any):
        """Thread-safe SSE event emission."""
        if self._loop and self._queue and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._queue.put({"type": event_type, "data": data}), self._loop
            )

    def close_stream(self):
        """Signal end of SSE stream."""
        if self._loop and self._queue and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._queue.put(None), self._loop)


# ---------------------------------------------------------------------------
# Global job store
# ---------------------------------------------------------------------------

_jobs: Dict[str, Job] = {}
_jobs_lock = threading.Lock()


def get_job(job_id: str) -> Optional[Job]:
    with _jobs_lock:
        return _jobs.get(job_id)


def create_job(request: dict) -> str:
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, request=request)
    with _jobs_lock:
        _jobs[job_id] = job
    return job_id


def start_job(job_id: str, loop: asyncio.AbstractEventLoop):
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    job._attach_loop(loop)
    job.status = "running"
    t = threading.Thread(target=_run_analysis, args=(job,), daemon=True)
    job._thread = t
    t.start()


# ---------------------------------------------------------------------------
# Analysis runner (executes in a background thread)
# ---------------------------------------------------------------------------

def _run_analysis(job: Job):
    try:
        req = job.request

        # Build config
        config = DEFAULT_CONFIG.copy()
        config["max_debate_rounds"] = req["research_depth"]
        config["max_risk_discuss_rounds"] = req["research_depth"]
        config["quick_think_llm"] = req["shallow_thinker"]
        config["deep_think_llm"] = req["deep_thinker"]
        config["backend_url"] = req["backend_url"]
        config["llm_provider"] = req["llm_provider"]
        config["google_thinking_level"] = req.get("google_thinking_level")
        config["openai_reasoning_effort"] = req.get("openai_reasoning_effort")
        config["anthropic_effort"] = req.get("anthropic_effort")

        # Normalize analyst order
        selected_set = set(req["analysts"])
        analyst_keys = [a for a in ANALYST_ORDER if a in selected_set]

        # Build initial agent status
        agent_status: dict[str, str] = {}
        for key in analyst_keys:
            agent_status[ANALYST_AGENT_NAMES[key]] = "pending"
        for team_agents in FIXED_AGENTS.values():
            for agent in team_agents:
                agent_status[agent] = "pending"
        job._agent_status = agent_status

        # Build active report sections
        report_sections: dict[str, Optional[str]] = {}
        for section, (analyst_key, _) in REPORT_SECTIONS_DEF.items():
            if analyst_key is None or analyst_key in selected_set:
                report_sections[section] = None
        job._report_sections = report_sections

        # Emit initial state
        job.emit("init", {
            "agent_status": dict(agent_status),
            "report_sections": list(report_sections.keys()),
            "ticker": req["ticker"],
            "analysis_date": req["analysis_date"],
        })

        stats_handler = StatsCallbackHandler()

        graph = TradingAgentsGraph(
            analyst_keys,
            config=config,
            debug=False,
            callbacks=[stats_handler],
        )

        init_state = graph.propagator.create_initial_state(req["ticker"], req["analysis_date"])
        graph_args = graph.propagator.get_graph_args(callbacks=[stats_handler])

        start_time = time.time()
        trace: list = []

        for chunk in graph.graph.stream(init_state, **graph_args):
            # ── Messages & tool calls ──────────────────────────────────────
            messages = chunk.get("messages", [])
            if messages:
                last = messages[-1]
                msg_id = getattr(last, "id", None)
                if msg_id and msg_id != job._last_message_id:
                    job._last_message_id = msg_id
                    msg_type, content = _classify_message(last)
                    if content and content.strip():
                        job.emit("message", {
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                            "kind": msg_type,
                            "content": content[:500],   # cap for SSE payload size
                        })
                    if hasattr(last, "tool_calls") and last.tool_calls:
                        for tc in last.tool_calls:
                            name = tc["name"] if isinstance(tc, dict) else tc.name
                            args = tc["args"] if isinstance(tc, dict) else tc.args
                            job.emit("tool_call", {
                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                "tool": name,
                                "args": str(args)[:200],
                            })

            # ── Analyst statuses ───────────────────────────────────────────
            _update_analyst_statuses(job, chunk, analyst_keys)

            # ── Investment debate (Research Team) ──────────────────────────
            if chunk.get("investment_debate_state"):
                debate = chunk["investment_debate_state"]
                bull  = debate.get("bull_history",  "").strip()
                bear  = debate.get("bear_history",  "").strip()
                judge = debate.get("judge_decision","").strip()

                if bull or bear:
                    _set_research_team_status(job, "in_progress")

                if bull:
                    _emit_report(job, "investment_plan",
                                 f"### Bull Researcher Analysis\n{bull}")
                if bear:
                    _emit_report(job, "investment_plan",
                                 f"### Bear Researcher Analysis\n{bear}")
                if judge:
                    _emit_report(job, "investment_plan",
                                 f"### Research Manager Decision\n{judge}")
                    _set_research_team_status(job, "completed")
                    _update_agent(job, "Trader", "in_progress")

            # ── Trader ─────────────────────────────────────────────────────
            if chunk.get("trader_investment_plan"):
                _emit_report(job, "trader_investment_plan",
                             chunk["trader_investment_plan"])
                if agent_status.get("Trader") != "completed":
                    _update_agent(job, "Trader", "completed")
                    _update_agent(job, "Aggressive Analyst", "in_progress")

            # ── Risk debate ────────────────────────────────────────────────
            if chunk.get("risk_debate_state"):
                risk  = chunk["risk_debate_state"]
                agg   = risk.get("aggressive_history",  "").strip()
                con   = risk.get("conservative_history","").strip()
                neu   = risk.get("neutral_history",     "").strip()
                judge = risk.get("judge_decision",      "").strip()

                if agg:
                    _maybe_activate(job, "Aggressive Analyst")
                    _emit_report(job, "final_trade_decision",
                                 f"### Aggressive Analyst Analysis\n{agg}")
                if con:
                    _maybe_activate(job, "Conservative Analyst")
                    _emit_report(job, "final_trade_decision",
                                 f"### Conservative Analyst Analysis\n{con}")
                if neu:
                    _maybe_activate(job, "Neutral Analyst")
                    _emit_report(job, "final_trade_decision",
                                 f"### Neutral Analyst Analysis\n{neu}")
                if judge:
                    for a in ["Aggressive Analyst", "Conservative Analyst",
                              "Neutral Analyst", "Portfolio Manager"]:
                        _update_agent(job, a, "completed")
                    _emit_report(job, "final_trade_decision",
                                 f"### Portfolio Manager Decision\n{judge}")

            # ── Stats heartbeat ────────────────────────────────────────────
            stats = stats_handler.get_stats()
            stats["elapsed"] = round(time.time() - start_time, 1)
            job.emit("stats", stats)

            trace.append(chunk)

        # ── Post-stream ────────────────────────────────────────────────────
        final_state = trace[-1] if trace else {}
        decision = graph.process_signal(final_state.get("final_trade_decision", ""))

        # Final report sections from accumulated state
        for section in list(report_sections):
            if section in final_state and final_state[section]:
                _emit_report(job, section, final_state[section])

        for agent in list(agent_status):
            _update_agent(job, agent, "completed")

        complete_report = _build_report(final_state, req["ticker"])
        job.status = "completed"
        job.decision = decision
        job.complete_report = complete_report

        job.emit("complete", {
            "decision": decision,
            "ticker": req["ticker"],
            "analysis_date": req["analysis_date"],
            "complete_report": complete_report,
        })

    except Exception as exc:
        job.status = "error"
        job.error = str(exc)
        job.emit("error", {"message": str(exc), "traceback": traceback.format_exc()})
    finally:
        job.close_stream()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _update_agent(job: Job, agent: str, status: str):
    if agent in job._agent_status and job._agent_status[agent] != status:
        job._agent_status[agent] = status
        job.emit("agent_status", {"agent": agent, "status": status})


def _maybe_activate(job: Job, agent: str):
    if job._agent_status.get(agent) not in ("in_progress", "completed"):
        _update_agent(job, agent, "in_progress")


def _set_research_team_status(job: Job, status: str):
    for a in ["Bull Researcher", "Bear Researcher", "Research Manager"]:
        _update_agent(job, a, status)


def _emit_report(job: Job, section: str, content: str):
    if section in job._report_sections:
        job._report_sections[section] = content
        job.emit("report_update", {
            "section": section,
            "title": SECTION_TITLES.get(section, section),
            "content": content,
        })


def _update_analyst_statuses(job: Job, chunk: dict, analyst_keys: list):
    found_active = False
    for key in analyst_keys:
        agent_name = ANALYST_AGENT_NAMES[key]
        report_key = ANALYST_REPORT_MAP[key]
        if chunk.get(report_key):
            _emit_report(job, report_key, chunk[report_key])
        has_report = bool(job._report_sections.get(report_key))
        if has_report:
            _update_agent(job, agent_name, "completed")
        elif not found_active:
            _update_agent(job, agent_name, "in_progress")
            found_active = True
        else:
            _update_agent(job, agent_name, "pending")
    if not found_active and analyst_keys:
        if job._agent_status.get("Bull Researcher") == "pending":
            _update_agent(job, "Bull Researcher", "in_progress")


def _build_report(final_state: dict, ticker: str) -> str:
    parts = [
        f"# Trading Analysis Report: {ticker}",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    analyst_map = [
        ("market_report",       "Market Analyst"),
        ("sentiment_report",    "Social Analyst"),
        ("news_report",         "News Analyst"),
        ("fundamentals_report", "Fundamentals Analyst"),
    ]
    analysts = [(n, final_state[k]) for k, n in analyst_map if final_state.get(k)]
    if analysts:
        parts.append("## I. Analyst Team Reports")
        for name, content in analysts:
            parts.append(f"### {name}\n{content}")

    if final_state.get("investment_debate_state"):
        d = final_state["investment_debate_state"]
        parts.append("## II. Research Team Decision")
        if d.get("bull_history"):
            parts.append(f"### Bull Researcher\n{d['bull_history']}")
        if d.get("bear_history"):
            parts.append(f"### Bear Researcher\n{d['bear_history']}")
        if d.get("judge_decision"):
            parts.append(f"### Research Manager\n{d['judge_decision']}")

    if final_state.get("trader_investment_plan"):
        parts.append(f"## III. Trading Team Plan\n\n### Trader\n{final_state['trader_investment_plan']}")

    if final_state.get("risk_debate_state"):
        r = final_state["risk_debate_state"]
        parts.append("## IV. Risk Management")
        for key, name in [
            ("aggressive_history",  "Aggressive Analyst"),
            ("conservative_history","Conservative Analyst"),
            ("neutral_history",     "Neutral Analyst"),
        ]:
            if r.get(key):
                parts.append(f"### {name}\n{r[key]}")
        if r.get("judge_decision"):
            parts.append(f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{r['judge_decision']}")

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# SSE async generator
# ---------------------------------------------------------------------------

async def stream_job_events(job_id: str, http_request):
    """Async generator that yields SSE-formatted dicts."""
    loop = asyncio.get_event_loop()
    job = get_job(job_id)
    if not job:
        yield {"data": json.dumps({"type": "error", "data": {"message": "Job not found"}})}
        return

    if job.status == "pending":
        start_job(job_id, loop)

    while True:
        try:
            disconnected = await http_request.is_disconnected()
            if disconnected:
                break
        except Exception:
            break

        try:
            event = await asyncio.wait_for(job._queue.get(), timeout=1.0)
            if event is None:       # sentinel → stream ended
                break
            yield {"data": json.dumps(event)}
        except asyncio.TimeoutError:
            yield {"comment": "keep-alive"}   # SSE keep-alive comment
