"""FastAPI application entry point for the TradingAgents WebUI backend."""

# import os
from pathlib import Path
from .models import AnalysisRequest
from .providers import ANALYSTS, DEPTH_OPTIONS, PROVIDERS, SHALLOW_MODELS, DEEP_MODELS, THINKING_CONFIG
from .jobs import create_job, get_job, stream_job_events

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Load .env from project root (two levels up from this file)
_root = Path(__file__).resolve().parents[2]
load_dotenv(_root / ".env")


app = FastAPI(title="TradingAgents WebUI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Static configuration endpoints ────────────────────────────────────────────

@app.get("/api/config/providers")
def get_providers():
    return {"providers": PROVIDERS}


@app.get("/api/config/models/{provider}")
def get_models(provider: str):
    p = provider.lower()
    return {
        "shallow": SHALLOW_MODELS.get(p, []),
        "deep": DEEP_MODELS.get(p, []),
    }


@app.get("/api/config/thinking/{provider}")
def get_thinking_config(provider: str):
    return {"options": THINKING_CONFIG.get(provider.lower(), [])}


@app.get("/api/config/depth-options")
def get_depth_options():
    return {"options": DEPTH_OPTIONS}


@app.get("/api/config/analysts")
def get_analysts():
    return {"analysts": ANALYSTS}


# ── Analysis endpoints ─────────────────────────────────────────────────────────

@app.post("/api/analyze")
def start_analysis(body: AnalysisRequest):
    # Sanitise ticker
    body.ticker = body.ticker.strip().upper()
    job_id = create_job(body.model_dump())
    return {"job_id": job_id, "status": "pending"}


@app.get("/api/analyze/{job_id}/status")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job.status,
        "error": job.error,
        "decision": job.decision,
    }


@app.get("/api/analyze/{job_id}/report")
def job_report(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=202, detail="Analysis not yet complete")
    return {"complete_report": job.complete_report, "decision": job.decision}


@app.get("/api/analyze/{job_id}/stream")
async def stream_analysis(job_id: str, request: Request):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return EventSourceResponse(stream_job_events(job_id, request))
