<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { Separator, Dialog, ScrollArea } from 'bits-ui';
  import { marked } from 'marked';
  import { api } from '$lib/api';
  import AgentStatus from '$lib/components/AgentStatus.svelte';
  import MessageLog from '$lib/components/MessageLog.svelte';
  import ReportViewer from '$lib/components/ReportViewer.svelte';
  import StatsBar from '$lib/components/StatsBar.svelte';
  import type {
    DashboardState,
    SSEEvent,
    AgentStatusEvent,
    MessageEvent,
    ToolCallEvent,
    ReportUpdateEvent,
    StatsEvent,
    InitEvent,
    CompleteEvent,
  } from '$lib/types';

  interface Props {
    data: { jobId: string };
  }
  let { data }: Props = $props();

  // ── Dashboard state ────────────────────────────────────────────────────────
  let state = $state<DashboardState>({
    jobId: data.jobId,
    ticker: '',
    analysisDate: '',
    status: 'connecting',
    agentStatus: {},
    messages: [],
    toolCalls: [],
    reportSections: {},
    reportTitles: {},
    stats: null,
    decision: null,
    completeReport: null,
    errorMessage: null,
  });

  let showFullReport = $state(false);
  let activeReportTab = $state('');

  // ── SSE connection ─────────────────────────────────────────────────────────
  let es: EventSource | null = null;

  function connect() {
    es = api.streamJobEvents(data.jobId);

    es.onmessage = (raw) => {
      try {
        const event = JSON.parse(raw.data) as SSEEvent;
        handleEvent(event);
      } catch { /* ignore malformed */ }
    };

    es.onerror = () => {
      if (state.status !== 'completed') {
        state.status = 'error';
        state.errorMessage = 'Connection to server lost.';
      }
      es?.close();
    };
  }

  function handleEvent(event: SSEEvent) {
    switch (event.type) {
      case 'init': {
        const d = event.data as InitEvent;
        state.ticker = d.ticker;
        state.analysisDate = d.analysis_date;
        state.agentStatus = { ...d.agent_status };
        state.reportSections = Object.fromEntries(d.report_sections.map(s => [s, '']));
        state.status = 'running';
        break;
      }

      case 'agent_status': {
        const d = event.data as AgentStatusEvent;
        state.agentStatus = { ...state.agentStatus, [d.agent]: d.status };
        break;
      }

      case 'message': {
        const d = event.data as MessageEvent;
        state.messages = [d, ...state.messages].slice(0, 100);
        break;
      }

      case 'tool_call': {
        const d = event.data as ToolCallEvent;
        state.toolCalls = [d, ...state.toolCalls].slice(0, 100);
        break;
      }

      case 'report_update': {
        const d = event.data as ReportUpdateEvent;
        state.reportSections = { ...state.reportSections, [d.section]: d.content };
        state.reportTitles = { ...state.reportTitles, [d.section]: d.title };
        break;
      }

      case 'stats': {
        state.stats = event.data as StatsEvent;
        break;
      }

      case 'complete': {
        const d = event.data as CompleteEvent;
        state.status = 'completed';
        state.decision = d.decision;
        state.completeReport = d.complete_report;
        es?.close();
        break;
      }

      case 'error': {
        const d = event.data as { message: string };
        state.status = 'error';
        state.errorMessage = d.message;
        es?.close();
        break;
      }
    }
  }

  onMount(() => { connect(); });
  onDestroy(() => { es?.close(); });

  // ── Derived helpers ────────────────────────────────────────────────────────
  let completedReports = $derived(
    Object.values(state.reportSections).filter(v => v && v.length > 0).length
  );
  let totalReports = $derived(Object.keys(state.reportSections).length);

  let decisionColor = $derived(
    !state.decision            ? 'text-gray-400'
    : /buy/i.test(state.decision)  ? 'text-green-400'
    : /sell/i.test(state.decision) ? 'text-red-400'
    : 'text-yellow-400'
  );

  function renderMd(md: string): string {
    try { return marked.parse(md) as string; } catch { return md; }
  }
</script>

<div class="flex flex-col h-screen overflow-hidden">

  <!-- ── Main dashboard area ──────────────────────────────────────────────── -->
  <div class="flex flex-1 overflow-hidden">

    <!-- Left sidebar: agent status -->
    <aside class="w-52 flex-shrink-0 bg-gray-900 border-r border-gray-800 p-3 overflow-y-auto">
      <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Agents</p>
      <AgentStatus agentStatus={state.agentStatus} />

      {#if state.decision}
        <Separator.Root class="bg-gray-800 h-px my-4" />
        <div class="text-center">
          <p class="text-xs text-gray-500 mb-1">Decision</p>
          <p class="text-lg font-extrabold {decisionColor}">{state.decision}</p>
        </div>
      {/if}
    </aside>

    <!-- Centre: report + messages -->
    <div class="flex-1 flex flex-col overflow-hidden">

      <!-- Report viewer (top 60%) -->
      <div class="flex-1 overflow-hidden p-3">
        <ReportViewer
          sections={state.reportSections}
          titles={state.reportTitles}
          bind:activeSection={activeReportTab}
        />
      </div>

      <Separator.Root class="bg-gray-800 h-px flex-shrink-0" />

      <!-- Message log (bottom 40%) -->
      <div class="h-52 flex-shrink-0 p-3 overflow-hidden">
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Messages & Tools
        </p>
        <div class="h-[calc(100%-1.5rem)] overflow-hidden">
          <MessageLog messages={state.messages} toolCalls={state.toolCalls} />
        </div>
      </div>
    </div>
  </div>

  <!-- ── Stats bar (footer) ──────────────────────────────────────────────── -->
  <StatsBar
    stats={state.stats}
    agentStatus={state.agentStatus}
    {totalReports}
    {completedReports}
    jobStatus={state.status}
    ticker={state.ticker}
    analysisDate={state.analysisDate}
  />

  <!-- ── Action bar (when complete) ─────────────────────────────────────── -->
  {#if state.status === 'completed'}
    <div class="bg-green-900/20 border-t border-green-800/40 px-4 py-3 flex items-center justify-between flex-wrap gap-2">
      <div class="flex items-center gap-3">
        <span class="text-green-400 font-bold">✓ Analysis complete</span>
        {#if state.decision}
          <span class="px-3 py-1 rounded-full border text-sm font-bold {decisionColor}
                       {/buy/i.test(state.decision) ? 'border-green-600 bg-green-900/30'
                        : /sell/i.test(state.decision) ? 'border-red-600 bg-red-900/30'
                        : 'border-yellow-600 bg-yellow-900/30'}">
            {state.decision}
          </span>
        {/if}
      </div>
      <div class="flex gap-2">
        <button
          onclick={() => { showFullReport = true; }}
          class="px-4 py-1.5 text-sm rounded-lg border border-gray-700 text-gray-300 hover:border-gray-500 hover:text-white transition-colors"
        >
          View Full Report
        </button>
        <button
          onclick={() => goto('/')}
          class="px-4 py-1.5 text-sm rounded-lg bg-green-700 hover:bg-green-600 text-white transition-colors"
        >
          New Analysis
        </button>
      </div>
    </div>
  {/if}

  <!-- ── Error bar ────────────────────────────────────────────────────────── -->
  {#if state.status === 'error'}
    <div class="bg-red-900/20 border-t border-red-800/50 px-4 py-3 flex items-center justify-between gap-2">
      <span class="text-red-400 text-sm">⚠ {state.errorMessage ?? 'Analysis failed'}</span>
      <button
        onclick={() => goto('/')}
        class="px-4 py-1.5 text-sm rounded-lg border border-red-700 text-red-300 hover:bg-red-900/30 transition-colors"
      >
        Back
      </button>
    </div>
  {/if}
</div>

<!-- ── Full report dialog ──────────────────────────────────────────────────── -->
<Dialog.Root bind:open={showFullReport}>
  <Dialog.Portal>
    <Dialog.Overlay class="fixed inset-0 bg-black/70 backdrop-blur-sm z-40" />
    <Dialog.Content
      class="fixed inset-4 md:inset-10 z-50 bg-gray-900 border border-gray-700 rounded-xl
             shadow-2xl flex flex-col overflow-hidden"
    >
      <div class="flex items-center justify-between px-5 py-3 border-b border-gray-800 flex-shrink-0">
        <Dialog.Title class="text-base font-semibold text-white">
          Complete Report — {state.ticker} {state.analysisDate}
        </Dialog.Title>
        <Dialog.Close
          class="text-gray-500 hover:text-white transition-colors px-2 py-1 rounded hover:bg-gray-800"
        >
          ✕
        </Dialog.Close>
      </div>

      <ScrollArea.Root class="flex-1 overflow-hidden">
        <ScrollArea.Viewport class="h-full w-full p-5">
          <div class="prose-dark">
            {#if state.completeReport}
              <!-- eslint-disable-next-line svelte/no-at-html-tags -->
              {@html renderMd(state.completeReport)}
            {:else}
              <p class="text-gray-500 italic">No report available.</p>
            {/if}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar orientation="vertical" class="flex h-full w-2 touch-none select-none p-0.5">
          <ScrollArea.Thumb class="relative flex-1 rounded-full bg-gray-700" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
