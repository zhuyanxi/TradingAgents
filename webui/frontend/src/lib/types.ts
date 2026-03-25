// Shared TypeScript types

export interface Provider {
  value: string;
  label: string;
  url: string;
}

export interface ModelOption {
  value: string;
  label: string;
}

export interface DepthOption {
  value: number;
  label: string;
  description: string;
}

export interface AnalystOption {
  value: string;
  label: string;
}

export interface ThinkingOption {
  value: string;
  label: string;
}

// ── Wizard form state ────────────────────────────────────────────────────────

export interface WizardState {
  ticker: string;
  analysis_date: string;
  analysts: string[];
  research_depth: number;
  llm_provider: string;
  backend_url: string;
  shallow_thinker: string;
  deep_thinker: string;
  google_thinking_level: string | null;
  openai_reasoning_effort: string | null;
  anthropic_effort: string | null;
}

// ── SSE event payloads ───────────────────────────────────────────────────────

export type AgentStatus = 'pending' | 'in_progress' | 'completed' | 'error';

export interface AgentStatusEvent {
  agent: string;
  status: AgentStatus;
}

export interface MessageEvent {
  timestamp: string;
  kind: 'User' | 'Agent' | 'Tool' | 'Data' | 'Control' | 'System';
  content: string;
}

export interface ToolCallEvent {
  timestamp: string;
  tool: string;
  args: string;
}

export interface ReportUpdateEvent {
  section: string;
  title: string;
  content: string;
}

export interface StatsEvent {
  llm_calls: number;
  tool_calls: number;
  tokens_in: number;
  tokens_out: number;
  elapsed: number;
}

export interface InitEvent {
  agent_status: Record<string, AgentStatus>;
  report_sections: string[];
  ticker: string;
  analysis_date: string;
}

export interface CompleteEvent {
  decision: string;
  ticker: string;
  analysis_date: string;
  complete_report: string;
}

export interface SSEEvent {
  type: 'init' | 'agent_status' | 'message' | 'tool_call' | 'report_update' | 'stats' | 'complete' | 'error';
  data: InitEvent | AgentStatusEvent | MessageEvent | ToolCallEvent | ReportUpdateEvent | StatsEvent | CompleteEvent | { message: string };
}

// ── Dashboard state ──────────────────────────────────────────────────────────

export interface DashboardState {
  jobId: string;
  ticker: string;
  analysisDate: string;
  status: 'connecting' | 'running' | 'completed' | 'error';
  agentStatus: Record<string, AgentStatus>;
  messages: MessageEvent[];
  toolCalls: ToolCallEvent[];
  reportSections: Record<string, string>;
  reportTitles: Record<string, string>;
  stats: StatsEvent | null;
  decision: string | null;
  completeReport: string | null;
  errorMessage: string | null;
}
