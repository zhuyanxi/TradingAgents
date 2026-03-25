<script lang="ts">
  import { goto } from '$app/navigation';
  import { Checkbox, RadioGroup, Select, Separator } from 'bits-ui';
  import { api } from '$lib/api';
  import type { WizardState, Provider, ModelOption, DepthOption, AnalystOption, ThinkingOption } from '$lib/types';

  // ── Remote config data ────────────────────────────────────────────────────
  let providers = $state<Provider[]>([]);
  let depthOptions = $state<DepthOption[]>([]);
  let analystOptions = $state<AnalystOption[]>([]);
  let shallowModels = $state<ModelOption[]>([]);
  let deepModels = $state<ModelOption[]>([]);
  let thinkingOptions = $state<ThinkingOption[]>([]);

  // ── Wizard step (1–7) ─────────────────────────────────────────────────────
  let step = $state(1);
  const TOTAL_STEPS = 7;

  // ── Form state ────────────────────────────────────────────────────────────
  let ticker = $state('');
  let analysisDate = $state(new Date().toISOString().slice(0, 10));
  let selectedAnalysts = $state<string[]>(['market', 'news', 'fundamentals']);
  let researchDepth = $state<number>(1);
  let selectedProvider = $state<Provider | null>(null);
  let shallowModel = $state('');
  let deepModel = $state('');
  let thinkingValue = $state('');

  // ── UI state ──────────────────────────────────────────────────────────────
  let loading = $state(false);
  let submitError = $state('');
  let validationError = $state('');

  // ── Load config data on mount ─────────────────────────────────────────────
  $effect(() => {
    Promise.all([
      api.getProviders(),
      api.getDepthOptions(),
      api.getAnalysts(),
    ]).then(([p, d, a]) => {
      providers = p;
      depthOptions = d;
      analystOptions = a;
      if (p.length > 0 && !selectedProvider) {
        selectedProvider = p[0];
        loadModels(p[0].value);
      }
      if (d.length > 0) researchDepth = d[0].value;
    });
  });

  async function loadModels(providerValue: string) {
    const m = await api.getModels(providerValue);
    shallowModels = m.shallow;
    deepModels = m.deep;
    shallowModel = m.shallow[0]?.value ?? '';
    deepModel = m.deep[0]?.value ?? '';
    const tc = await api.getThinkingOptions(providerValue);
    thinkingOptions = tc;
    thinkingValue = tc[0]?.value ?? '';
  }

  function onProviderChange(value: string) {
    const p = providers.find(p => p.value === value);
    if (p) {
      selectedProvider = p;
      loadModels(p.value);
    }
  }

  // ── Validation ─────────────────────────────────────────────────────────────
  function validate(): boolean {
    validationError = '';
    if (step === 1) {
      if (!ticker.trim()) { validationError = 'Please enter a ticker symbol.'; return false; }
      if (!/^\d{4}-\d{2}-\d{2}$/.test(analysisDate)) { validationError = 'Date must be YYYY-MM-DD.'; return false; }
    }
    if (step === 2 && selectedAnalysts.length === 0) {
      validationError = 'Select at least one analyst.'; return false;
    }
    if (step === 5 && !selectedProvider) {
      validationError = 'Please select an LLM provider.'; return false;
    }
    return true;
  }

  function next() { if (validate()) step = Math.min(step + 1, TOTAL_STEPS); }
  function back() { step = Math.max(step - 1, 1); validationError = ''; }

  function toggleAnalyst(value: string) {
    if (selectedAnalysts.includes(value)) {
      selectedAnalysts = selectedAnalysts.filter(a => a !== value);
    } else {
      selectedAnalysts = [...selectedAnalysts, value];
    }
  }

  // ── Submit ─────────────────────────────────────────────────────────────────
  async function submit() {
    if (!selectedProvider) return;
    loading = true;
    submitError = '';
    try {
      const payload: WizardState = {
        ticker: ticker.trim().toUpperCase(),
        analysis_date: analysisDate,
        analysts: selectedAnalysts,
        research_depth: researchDepth,
        llm_provider: selectedProvider.value,
        backend_url: selectedProvider.url,
        shallow_thinker: shallowModel,
        deep_thinker: deepModel,
        google_thinking_level:     selectedProvider.value === 'google'     ? thinkingValue : null,
        openai_reasoning_effort:   selectedProvider.value === 'openai'    ? thinkingValue : null,
        anthropic_effort:          selectedProvider.value === 'anthropic'  ? thinkingValue : null,
      };
      const { job_id } = await api.startAnalysis(payload);
      await goto(`/analyze/${job_id}`);
    } catch (err: any) {
      submitError = err?.message ?? 'Failed to start analysis.';
    } finally {
      loading = false;
    }
  }

  let needsThinking = $derived(
    selectedProvider?.value === 'openai' ||
    selectedProvider?.value === 'anthropic' ||
    selectedProvider?.value === 'google'
  );

  let stepTitles = [
    'Ticker & Date',
    'Analyst Team',
    'Research Depth',
    'LLM Provider',
    'Thinking Models',
    'Thinking Config',
    'Review & Launch',
  ];
  let effectiveSteps = $derived(needsThinking ? TOTAL_STEPS : TOTAL_STEPS - 1);
</script>

<div class="max-w-2xl mx-auto px-4 py-10 w-full">

  <!-- Title -->
  <div class="mb-8 text-center">
    <h1 class="text-2xl font-bold text-white mb-1">Configure Analysis</h1>
    <p class="text-gray-500 text-sm">Set up your multi-agent trading analysis in {effectiveSteps} steps</p>
  </div>

  <!-- Step indicator -->
  <div class="flex items-center justify-center gap-1 mb-8">
    {#each Array.from({ length: effectiveSteps }, (_, i) => i + 1) as s}
      <div class="flex items-center gap-1">
        <div
          class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border transition-colors
                 {s < step ? 'bg-green-600 border-green-600 text-white'
                 : s === step ? 'border-green-500 text-green-400 bg-green-900/30'
                 : 'border-gray-700 text-gray-600 bg-transparent'}"
        >
          {s < step ? '✓' : s}
        </div>
        {#if s < effectiveSteps}
          <div class="w-6 h-px {s < step ? 'bg-green-600' : 'bg-gray-700'}"></div>
        {/if}
      </div>
    {/each}
  </div>

  <!-- Card -->
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl">

    <!-- Step label -->
    <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Step {step}</p>
    <h2 class="text-lg font-semibold text-white mb-4">{stepTitles[step - 1]}</h2>

    <Separator.Root class="bg-gray-800 h-px mb-5" />

    <!-- ── STEP 1: Ticker & Date ── -->
    {#if step === 1}
      <div class="flex flex-col gap-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1" for="ticker">Ticker Symbol</label>
          <input
            id="ticker"
            type="text"
            bind:value={ticker}
            placeholder="e.g. SPY, NVDA, CNC.TO, 7203.T"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white
                   placeholder-gray-600 focus:outline-none focus:border-green-600 focus:ring-1 focus:ring-green-600 uppercase"
            oninput={(e) => { ticker = (e.target as HTMLInputElement).value.toUpperCase(); }}
          />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1" for="date">Analysis Date</label>
          <input
            id="date"
            type="date"
            bind:value={analysisDate}
            max={new Date().toISOString().slice(0, 10)}
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white
                   focus:outline-none focus:border-green-600 focus:ring-1 focus:ring-green-600"
          />
          <p class="text-xs text-gray-600 mt-1">Must not be in the future</p>
        </div>
      </div>

    <!-- ── STEP 2: Analysts ── -->
    {:else if step === 2}
      <div class="flex flex-col gap-3">
        <p class="text-sm text-gray-400 mb-1">Select the analyst agents for this run:</p>
        {#each analystOptions as analyst}
          {@const checked = selectedAnalysts.includes(analyst.value)}
          <Checkbox.Root
            {checked}
            onCheckedChange={() => toggleAnalyst(analyst.value)}
            class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                   {checked ? 'border-green-600 bg-green-900/20' : 'border-gray-700 bg-gray-800/40 hover:border-gray-600'}"
          >
            <div
              class="w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 transition-colors
                     {checked ? 'bg-green-600 border-green-600' : 'border-gray-600'}"
            >
              <Checkbox.Indicator class="text-white text-xs">✓</Checkbox.Indicator>
            </div>
            <span class="text-sm {checked ? 'text-white' : 'text-gray-400'}">{analyst.label}</span>
          </Checkbox.Root>
        {/each}
      </div>

    <!-- ── STEP 3: Depth ── -->
    {:else if step === 3}
      <RadioGroup.Root bind:value={() => String(researchDepth), (v) => (researchDepth = Number(v))} class="flex flex-col gap-3">
        {#each depthOptions as opt}
          {@const checked = researchDepth === opt.value}
          <RadioGroup.Item
            value={String(opt.value)}
            class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors text-left
                   {checked ? 'border-green-600 bg-green-900/20' : 'border-gray-700 bg-gray-800/40 hover:border-gray-600'}"
          >
            <div class="mt-0.5 w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center
                        {checked ? 'border-green-500' : 'border-gray-500'}">
              <RadioGroup.Indicator class="w-2 h-2 rounded-full bg-green-500" />
            </div>
            <div>
              <p class="text-sm font-medium {checked ? 'text-white' : 'text-gray-300'}">{opt.label}</p>
              <p class="text-xs text-gray-500 mt-0.5">{opt.description}</p>
            </div>
          </RadioGroup.Item>
        {/each}
      </RadioGroup.Root>

    <!-- ── STEP 4: Provider ── -->
    {:else if step === 4}
      <RadioGroup.Root
        bind:value={() => selectedProvider?.value ?? '', (v) => { onProviderChange(v); }}
        class="flex flex-col gap-2"
      >
        {#each providers as prov}
          {@const checked = selectedProvider?.value === prov.value}
          <RadioGroup.Item
            value={prov.value}
            class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                   {checked ? 'border-green-600 bg-green-900/20' : 'border-gray-700 bg-gray-800/40 hover:border-gray-600'}"
          >
            <div class="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center
                        {checked ? 'border-green-500' : 'border-gray-500'}">
              <RadioGroup.Indicator class="w-2 h-2 rounded-full bg-green-500" />
            </div>
            <div class="flex-1 min-w-0">
              <span class="text-sm font-medium {checked ? 'text-white' : 'text-gray-300'}">{prov.label}</span>
              <span class="ml-2 text-xs text-gray-600 truncate">{prov.url}</span>
            </div>
          </RadioGroup.Item>
        {/each}
      </RadioGroup.Root>

    <!-- ── STEP 5: Models ── -->
    {:else if step === 5}
      <div class="flex flex-col gap-5">
        <!-- Shallow / Quick -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Quick-Thinking Model</label>
          <Select.Root
            type="single"
            value={shallowModel}
            onValueChange={(v) => (shallowModel = v ?? '')}
          >
            <Select.Trigger
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white
                     flex items-center justify-between focus:outline-none focus:border-green-600 hover:border-gray-600"
            >
              <Select.Value placeholder="Select model…" />
              <span class="text-gray-500 ml-2">▾</span>
            </Select.Trigger>
            <Select.Content
              class="bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden"
            >
              <Select.Viewport class="p-1">
                {#each shallowModels as m}
                  <Select.Item
                    value={m.value}
                    class="flex items-center gap-2 px-3 py-2 text-sm rounded cursor-pointer
                           hover:bg-gray-700 text-gray-300 hover:text-white
                           data-[highlighted]:bg-gray-700 data-[highlighted]:text-white"
                  >
                    <Select.ItemIndicator class="text-green-400">✓</Select.ItemIndicator>
                    {m.label}
                  </Select.Item>
                {/each}
              </Select.Viewport>
            </Select.Content>
          </Select.Root>
        </div>

        <!-- Deep -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Deep-Thinking Model</label>
          <Select.Root
            type="single"
            value={deepModel}
            onValueChange={(v) => (deepModel = v ?? '')}
          >
            <Select.Trigger
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white
                     flex items-center justify-between focus:outline-none focus:border-green-600 hover:border-gray-600"
            >
              <Select.Value placeholder="Select model…" />
              <span class="text-gray-500 ml-2">▾</span>
            </Select.Trigger>
            <Select.Content
              class="bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden"
            >
              <Select.Viewport class="p-1">
                {#each deepModels as m}
                  <Select.Item
                    value={m.value}
                    class="flex items-center gap-2 px-3 py-2 text-sm rounded cursor-pointer
                           hover:bg-gray-700 text-gray-300 hover:text-white
                           data-[highlighted]:bg-gray-700 data-[highlighted]:text-white"
                  >
                    <Select.ItemIndicator class="text-green-400">✓</Select.ItemIndicator>
                    {m.label}
                  </Select.Item>
                {/each}
              </Select.Viewport>
            </Select.Content>
          </Select.Root>
        </div>
      </div>

    <!-- ── STEP 6: Thinking Config ── -->
    {:else if step === 6}
      {#if thinkingOptions.length > 0}
        <div>
          <p class="text-sm text-gray-400 mb-3">
            Configure {selectedProvider?.label} reasoning behaviour:
          </p>
          <RadioGroup.Root bind:value={thinkingValue} class="flex flex-col gap-2">
            {#each thinkingOptions as opt}
              {@const checked = thinkingValue === opt.value}
              <RadioGroup.Item
                value={opt.value}
                class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                       {checked ? 'border-green-600 bg-green-900/20' : 'border-gray-700 bg-gray-800/40 hover:border-gray-600'}"
              >
                <div class="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center
                            {checked ? 'border-green-500' : 'border-gray-500'}">
                  <RadioGroup.Indicator class="w-2 h-2 rounded-full bg-green-500" />
                </div>
                <span class="text-sm {checked ? 'text-white' : 'text-gray-300'}">{opt.label}</span>
              </RadioGroup.Item>
            {/each}
          </RadioGroup.Root>
        </div>
      {:else}
        <p class="text-sm text-gray-500 italic">
          No extra thinking configuration needed for {selectedProvider?.label ?? 'this provider'}.
        </p>
      {/if}

    <!-- ── STEP 7: Review ── -->
    {:else if step === 7}
      <div class="flex flex-col gap-3 text-sm">
        {#each [
          ['Ticker',        ticker.toUpperCase()],
          ['Date',          analysisDate],
          ['Analysts',      selectedAnalysts.join(', ') || '—'],
          ['Depth',         depthOptions.find(d => d.value === researchDepth)?.label ?? researchDepth],
          ['Provider',      selectedProvider?.label ?? '—'],
          ['Quick Model',   shallowModel],
          ['Deep Model',    deepModel],
          needsThinking && thinkingValue
            ? ['Thinking',  thinkingValue]
            : null,
        ].filter(Boolean) as row}
          <div class="flex justify-between border-b border-gray-800 pb-2">
            <span class="text-gray-500">{row![0]}</span>
            <span class="text-gray-200 text-right max-w-xs truncate">{row![1]}</span>
          </div>
        {/each}
      </div>

      {#if submitError}
        <p class="mt-4 text-sm text-red-400">{submitError}</p>
      {/if}
    {/if}

    <!-- Validation error -->
    {#if validationError}
      <p class="mt-3 text-sm text-yellow-400">{validationError}</p>
    {/if}

    <!-- Navigation -->
    <div class="mt-6 flex justify-between items-center">
      <button
        onclick={back}
        disabled={step === 1}
        class="px-4 py-2 text-sm rounded-lg border border-gray-700 text-gray-400
               hover:border-gray-600 hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        ← Back
      </button>

      {#if step < effectiveSteps}
        <button
          onclick={next}
          class="px-5 py-2 text-sm rounded-lg bg-green-700 hover:bg-green-600 text-white font-medium transition-colors"
        >
          Next →
        </button>
      {:else}
        <button
          onclick={submit}
          disabled={loading}
          class="px-5 py-2 text-sm rounded-lg bg-green-600 hover:bg-green-500 text-white font-semibold
                 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {#if loading}
            <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            Starting…
          {:else}
            🚀 Launch Analysis
          {/if}
        </button>
      {/if}
    </div>
  </div>
</div>
