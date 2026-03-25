<script lang="ts">
  import type { MessageEvent, ToolCallEvent } from '$lib/types';
  import { ScrollArea } from 'bits-ui';

  interface Props {
    messages: MessageEvent[];
    toolCalls: ToolCallEvent[];
  }
  let { messages, toolCalls }: Props = $props();

  // Merge and sort newest-first
  let combined = $derived(
    [
      ...messages.map(m => ({ ts: m.timestamp, type: 'msg', kind: m.kind, text: m.content })),
      ...toolCalls.map(t => ({ ts: t.timestamp, type: 'tool', kind: 'Tool', text: `${t.tool}: ${t.args}` })),
    ]
      .sort((a, b) => (a.ts > b.ts ? -1 : 1))
      .slice(0, 60)
  );

  function kindColor(kind: string): string {
    if (kind === 'Agent')   return 'text-green-400';
    if (kind === 'Tool')    return 'text-yellow-400';
    if (kind === 'Data')    return 'text-cyan-400';
    if (kind === 'User')    return 'text-blue-400';
    if (kind === 'Control') return 'text-purple-400';
    return 'text-gray-400';
  }
</script>

<ScrollArea.Root class="h-full w-full">
  <ScrollArea.Viewport class="h-full w-full">
    <div class="flex flex-col-reverse gap-0.5 font-mono text-xs">
      {#each combined as item (item.ts + item.text.slice(0, 20))}
        <div class="flex gap-2 py-0.5 border-b border-gray-800/40">
          <span class="text-gray-600 flex-shrink-0">{item.ts}</span>
          <span class="{kindColor(item.kind)} w-12 flex-shrink-0">{item.kind}</span>
          <span class="text-gray-300 break-all leading-relaxed">{item.text}</span>
        </div>
      {/each}
    </div>
  </ScrollArea.Viewport>
  <ScrollArea.Scrollbar orientation="vertical" class="flex h-full w-1.5 touch-none select-none border-l border-l-transparent p-px">
    <ScrollArea.Thumb class="relative flex-1 rounded-full bg-gray-700" />
  </ScrollArea.Scrollbar>
</ScrollArea.Root>
