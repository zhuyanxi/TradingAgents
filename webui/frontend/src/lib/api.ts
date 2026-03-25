import type { Provider, ModelOption, DepthOption, AnalystOption, ThinkingOption, WizardState } from './types';

// In dev the vite proxy forwards /api/* to the backend.
// In production (Docker), set the PUBLIC_API_BASE env variable to the
// backend URL that the browser can reach (e.g. http://localhost:8000).
const API_BASE =
  typeof window !== 'undefined' && (window as any).__API_BASE__
    ? (window as any).__API_BASE__
    : '';   // empty → relative URL, handled by vite proxy / SvelteKit

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

// ── Config ───────────────────────────────────────────────────────────────────

export const api = {
  async getProviders(): Promise<Provider[]> {
    const r = await get<{ providers: Provider[] }>('/api/config/providers');
    return r.providers;
  },

  async getModels(provider: string): Promise<{ shallow: ModelOption[]; deep: ModelOption[] }> {
    return get(`/api/config/models/${provider}`);
  },

  async getDepthOptions(): Promise<DepthOption[]> {
    const r = await get<{ options: DepthOption[] }>('/api/config/depth-options');
    return r.options;
  },

  async getAnalysts(): Promise<AnalystOption[]> {
    const r = await get<{ analysts: AnalystOption[] }>('/api/config/analysts');
    return r.analysts;
  },

  async getThinkingOptions(provider: string): Promise<ThinkingOption[]> {
    const r = await get<{ options: ThinkingOption[] }>(`/api/config/thinking/${provider}`);
    return r.options;
  },

  // ── Analysis ────────────────────────────────────────────────────────────────

  async startAnalysis(state: WizardState): Promise<{ job_id: string }> {
    return post('/api/analyze', state);
  },

  async getJobStatus(jobId: string): Promise<{ status: string; error?: string; decision?: string }> {
    return get(`/api/analyze/${jobId}/status`);
  },

  streamJobEvents(jobId: string): EventSource {
    return new EventSource(`${API_BASE}/api/analyze/${jobId}/stream`);
  },
};
