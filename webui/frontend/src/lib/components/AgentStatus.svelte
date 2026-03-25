<script lang="ts">
  import type { AgentStatus } from '$lib/types';

  interface Props {
    agentStatus: Record<string, AgentStatus>;
  }
  let { agentStatus }: Props = $props();

  const TEAMS: { name: string; agents: string[] }[] = [
    { name: 'Analysts',     agents: ['Market Analyst', 'Social Analyst', 'News Analyst', 'Fundamentals Analyst'] },
    { name: 'Research',     agents: ['Bull Researcher', 'Bear Researcher', 'Research Manager'] },
    { name: 'Trading',      agents: ['Trader'] },
    { name: 'Risk Mgmt',    agents: ['Aggressive Analyst', 'Neutral Analyst', 'Conservative Analyst'] },
    { name: 'Portfolio',    agents: ['Portfolio Manager'] },
  ];

  function statusColor(s: AgentStatus | undefined): string {
    if (s === 'completed')  return 'text-green-400';
    if (s === 'in_progress') return 'text-blue-400 animate-pulse';
    if (s === 'error')      return 'text-red-400';
    return 'text-gray-500';
  }

  function statusDot(s: AgentStatus | undefined): string {
    if (s === 'completed')  return 'bg-green-400';
    if (s === 'in_progress') return 'bg-blue-400 animate-pulse';
    if (s === 'error')      return 'bg-red-400';
    return 'bg-gray-600';
  }
</script>

<div class="flex flex-col gap-4">
  {#each TEAMS as team}
    {@const visibleAgents = team.agents.filter(a => a in agentStatus)}
    {#if visibleAgents.length > 0}
      <div>
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
          {team.name}
        </p>
        <div class="flex flex-col gap-1">
          {#each visibleAgents as agent}
            {@const s = agentStatus[agent]}
            <div class="flex items-center gap-2 py-0.5">
              <span class="w-2 h-2 rounded-full flex-shrink-0 {statusDot(s)}"></span>
              <span class="text-sm {statusColor(s)} truncate">{agent}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/each}
</div>
