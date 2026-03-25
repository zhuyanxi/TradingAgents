<script lang="ts">
  import type { StatsEvent } from '$lib/types';

  interface Props {
    stats: StatsEvent | null;
    agentStatus: Record<string, string>;
    totalReports: number;
    completedReports: number;
    jobStatus: string;
    ticker: string;
    analysisDate: string;
  }
  let { stats, agentStatus, totalReports, completedReports, jobStatus, ticker, analysisDate }: Props = $props();

  let agentsDone = $derived(Object.values(agentStatus).filter(s => s === 'completed').length);
  let agentsTotal = $derived(Object.keys(agentStatus).length);

  function fmt(n: number): string {
    return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
  }

  function fmtTime(sec: number): string {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = Math.floor(sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  let statusColor = $derived(
    jobStatus === 'completed' ? 'text-green-400 bg-green-900/30 border-green-700'
    : jobStatus === 'error'   ? 'text-red-400 bg-red-900/30 border-red-700'
    : jobStatus === 'running' ? 'text-blue-400 bg-blue-900/30 border-blue-700 animate-pulse'
    : 'text-gray-400 bg-gray-800 border-gray-700'
  );
</script>

<div class="flex items-center justify-between gap-4 px-4 py-2 bg-gray-900 border-t border-gray-800 text-xs font-mono flex-wrap">
  <!-- Left: ticker + date + status -->
  <div class="flex items-center gap-3">
    <span class="font-bold text-green-400">{ticker}</span>
    <span class="text-gray-500">{analysisDate}</span>
    <span class="px-2 py-0.5 rounded border text-xs {statusColor}">{jobStatus}</span>
  </div>

  <!-- Centre: stats -->
  <div class="flex items-center gap-4 text-gray-400">
    <span>Agents: <span class="text-gray-200">{agentsDone}/{agentsTotal}</span></span>
    {#if stats}
      <span>LLM: <span class="text-gray-200">{stats.llm_calls}</span></span>
      <span>Tools: <span class="text-gray-200">{stats.tool_calls}</span></span>
      <span>Tokens: <span class="text-green-300">{fmt(stats.tokens_in)}↑</span> <span class="text-yellow-300">{fmt(stats.tokens_out)}↓</span></span>
      <span>Reports: <span class="text-gray-200">{completedReports}/{totalReports}</span></span>
      <span>⏱ <span class="text-gray-200">{fmtTime(stats.elapsed)}</span></span>
    {/if}
  </div>
</div>
