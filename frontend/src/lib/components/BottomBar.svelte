<script lang="ts">
	import { statsStore } from '$lib/stores/stats';
	import { compactNumber } from '$lib/utils/format';

	const stats = $derived($statsStore);

	const METRICS = [
		{ key: 'contributors_total',    label: 'Contributors', color: '#93b023', icon: '◉' },
		{ key: 'user_groups',           label: 'User Groups',  color: '#38bdf8', icon: '▲'  },
		{ key: 'sustaining_members',    label: 'Members',      color: '#fb923c', icon: '■'  },
		{ key: 'plugin_count',          label: 'Plugins',      color: '#34d399', icon: '◆'  },
		{ key: 'hub_resources',         label: 'Hub Items',    color: '#f4e03a', icon: '★'  },
		{ key: 'github_stars',          label: 'GitHub ★',    color: '#e879f9', icon: '⊛'  },
	] as const;
</script>

<footer class="bottom-bar glass-panel">
	{#each METRICS as m}
		{@const val = stats[m.key]}
		<div class="metric" style="--metric-color: {m.color}">
			<span class="metric-icon">{m.icon}</span>
			<div class="metric-body">
				<span class="metric-value">{compactNumber(val as number | undefined)}</span>
				<span class="metric-label">{m.label}</span>
			</div>
		</div>
	{/each}
</footer>

<style>
	.bottom-bar {
		position: fixed;
		bottom: 16px;
		left: 50%;
		transform: translateX(-50%);
		height: 50px;
		z-index: 100;
		display: flex;
		align-items: center;
		padding: 0 16px;
		gap: 0;
    max-width: fit-content;
	}

	.metric {
		display: flex;
		align-items: center;
		gap: 7px;
		flex: 1;
		padding: 0 10px;
		border-right: 1px solid rgba(88,150,50,0.12);
	}

	.metric:last-child {
		border-right: none;
	}

	.metric-icon {
		font-size: 11px;
		color: var(--metric-color);
		text-shadow: 0 0 6px var(--metric-color);
	}

	.metric-body {
		display: flex;
		flex-direction: column;
		gap: 0;
		line-height: 1.1;
	}

	.metric-value {
		font-family: var(--font-mono);
		font-size: 13px;
		font-weight: 700;
		color: var(--metric-color);
		text-shadow: 0 0 8px var(--metric-color);
	}

	.metric-label {
		font-size: 9px;
		color: var(--hud-text-dim);
		letter-spacing: 0.5px;
		white-space: nowrap;
	}
</style>
