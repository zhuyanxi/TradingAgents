<script lang="ts">
  import { Tabs, ScrollArea } from 'bits-ui';
  import { marked } from 'marked';

  interface Props {
    sections: Record<string, string>;       // section key → markdown content
    titles: Record<string, string>;         // section key → display title
    activeSection?: string;
  }
  let { sections, titles, activeSection = $bindable('') }: Props = $props();

  // Only show tabs that have content
  let availableSections = $derived(
    Object.entries(sections)
      .filter(([_, v]) => !!v)
      .map(([k]) => k)
  );

  // Auto-switch to the latest section
  $effect(() => {
    if (availableSections.length > 0) {
      activeSection = availableSections[availableSections.length - 1];
    }
  });

  function renderMd(content: string): string {
    try {
      return marked.parse(content) as string;
    } catch {
      return content;
    }
  }
</script>

{#if availableSections.length === 0}
  <div class="flex items-center justify-center h-full text-gray-600 text-sm italic">
    Waiting for analysis report…
  </div>
{:else}
  <Tabs.Root bind:value={activeSection} class="flex flex-col h-full">
    <!-- Tab list -->
    <Tabs.List class="flex gap-1 overflow-x-auto pb-1 border-b border-gray-800 flex-shrink-0 flex-wrap">
      {#each availableSections as sec}
        <Tabs.Trigger
          value={sec}
          class="px-3 py-1.5 text-xs font-medium rounded-t whitespace-nowrap
                 data-[state=active]:bg-green-900/40 data-[state=active]:text-green-300 data-[state=active]:border-b-2 data-[state=active]:border-green-500
                 data-[state=inactive]:text-gray-500 data-[state=inactive]:hover:text-gray-300
                 transition-colors"
        >
          {titles[sec] ?? sec}
        </Tabs.Trigger>
      {/each}
    </Tabs.List>

    <!-- Tab content -->
    {#each availableSections as sec}
      <Tabs.Content value={sec} class="flex-1 overflow-hidden mt-2">
        <ScrollArea.Root class="h-full w-full">
          <ScrollArea.Viewport class="h-full w-full pr-2">
            <div class="prose-dark">
              <!-- eslint-disable-next-line svelte/no-at-html-tags -->
              {@html renderMd(sections[sec])}
            </div>
          </ScrollArea.Viewport>
          <ScrollArea.Scrollbar orientation="vertical" class="flex h-full w-1.5 touch-none select-none border-l border-l-transparent p-px">
            <ScrollArea.Thumb class="relative flex-1 rounded-full bg-gray-700" />
          </ScrollArea.Scrollbar>
        </ScrollArea.Root>
      </Tabs.Content>
    {/each}
  </Tabs.Root>
{/if}
