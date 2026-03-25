<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';

  let { children } = $props();
</script>

<div class="min-h-screen bg-gray-950 flex flex-col">
  <!-- Header -->
  <header class="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2 group">
        <span class="text-green-400 font-bold text-lg tracking-tight group-hover:text-green-300 transition-colors">
          TradingAgents
        </span>
        <span class="text-gray-500 text-sm">WebUI</span>
      </a>
      <nav class="flex items-center gap-1 text-sm">
        <a
          href="/"
          class="px-3 py-1.5 rounded text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition-colors
                 {$page?.url?.pathname === '/' ? 'text-gray-100 bg-gray-800' : ''}"
        >
          Configure
        </a>
      </nav>
    </div>
  </header>

  <!-- Page content -->
  <main class="flex-1 flex flex-col">
    {@render children()}
  </main>

  <!-- Footer -->
  <footer class="border-t border-gray-800 py-3 px-4 text-center text-xs text-gray-600">
    TradingAgents — Multi-Agents LLM Financial Trading Framework ·
    <a href="https://github.com/TauricResearch" class="hover:text-gray-400 transition-colors" target="_blank" rel="noopener">
      Tauric Research
    </a>
  </footer>
</div>
