<script lang="ts">
	import FeedTrack from './FeedTrack.svelte';

	const FEEDS = [
		{ id: 'commits', channels: ['commits'],              label: 'COMMITS',   id_tag: 'SYS/FEED/001', color: '#93b023' },
		{ id: 'signal',  channels: ['news', 'blog', 'planet'], label: 'SIGNAL',    id_tag: 'SYS/FEED/002', color: '#38bdf8' },
		{ id: 'plugins', channels: ['plugins', 'hub'],         label: 'RESOURCES', id_tag: 'SYS/FEED/003', color: '#34d399' },
	];

	let collapsed = $state(false);
</script>

<!-- Four independent feed panels stacked on the right -->
<div class="right-col" class:collapsed>
	{#each FEEDS as feed}
		<div class="nano-panel">
			<div class="nano-header">
				<span class="nh-icon" style="color: {feed.color}">◈</span>
				<span class="nh-title" style="color: {feed.color}; text-shadow: 0 0 8px {feed.color}44">{feed.label}</span>
				<span class="live-dot" style="background: {feed.color}; box-shadow: 0 0 6px {feed.color}"></span>
				<span class="nh-id">{feed.id_tag}</span>
			</div>
			<div class="feed-body">
				<FeedTrack channels={feed.channels} color={feed.color} />
			</div>
		</div>
	{/each}
</div>

<!-- Collapse/expand tab — always visible at the panel's left edge -->
<button
	class="panel-tab"
	class:is-collapsed={collapsed}
	onclick={() => (collapsed = !collapsed)}
	title={collapsed ? 'Expand panels' : 'Collapse panels'}
	aria-label={collapsed ? 'Expand right panels' : 'Collapse right panels'}
>‹</button>

<style>
	/* ── Column container ─────────────────────────────────────────── */
	.right-col {
		position: fixed;
		right: 16px;
		top: 60px;
		bottom: 56px;
		width: 300px;
		z-index: 100;
		display: flex;
		flex-direction: column;
		gap: 8px;
		pointer-events: none;
		transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.right-col.collapsed {
		transform: translateX(calc(100% + 20px));
	}

	/* ── Collapse toggle tab ─────────────────────────────────────── */
	.panel-tab {
		position: fixed;
		top: 50%;
		transform: translateY(-50%);
		z-index: 101;
		right: calc(16px + 300px); /* left edge of column */
		width: 18px;
		height: 44px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		background: rgba(17, 28, 43, 0.82);
		backdrop-filter: blur(18px) saturate(140%);
		border: 3px solid rgba(255, 242, 0, 0.28);
		border-right: none;
		border-radius: 8px 0 0 8px;
		box-shadow: -3px 0 12px rgba(0,0,0,0.35);
		color: var(--qgis-lemon);
		font-family: var(--font-mono);
		font-size: 19pt;
		font-weight: bold;
		line-height: 1;
		transition:
			right 0.3s cubic-bezier(0.4, 0, 0.2, 1),
			background 0.15s ease,
			border-color 0.15s ease;
	}

	.panel-tab.is-collapsed {
		right: 0;
		border-right: 1px solid rgba(255, 242, 0, 0.28);
		border-radius: 8px 0 0 8px;
	}

	.panel-tab:hover {
		background: rgba(17, 28, 43, 0.96);
		border-color: rgba(255, 242, 0, 0.55);
		box-shadow: -3px 0 16px rgba(255, 242, 0, 0.25);
	}

	.panel-tab:focus-visible {
		outline: 1px solid var(--qgis-light-green);
		outline-offset: 2px;
	}

	/* ── Individual glass panel ──────────────────────────────────── */
	.nano-panel {
		flex: 1;
		min-height: 0;
		background: rgba(17, 28, 43, 0.78);
		border: 1px solid rgba(88, 150, 50, 0.22);
		border-radius: 14px;
		backdrop-filter: blur(18px) saturate(140%);
		box-shadow:
			0 8px 32px rgba(0, 0, 0, 0.5),
			0 0 0 1px rgba(88, 150, 50, 0.07),
			inset 0 1px 0 rgba(147, 176, 35, 0.09);
		overflow: hidden;
		display: flex;
		flex-direction: column;
		pointer-events: all;
	}

	/* ── Panel header ────────────────────────────────────────────── */
	.nano-header {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 12px 7px;
		border-bottom: 1px solid rgba(88, 150, 50, 0.15);
		flex-shrink: 0;
	}

	.nh-icon {
		font-size: 11px;
	}

	.nh-title {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 10px;
		letter-spacing: 2px;
		flex: 1;
	}

	.live-dot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		animation: live-pulse 2s infinite;
		flex-shrink: 0;
	}

	@keyframes live-pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.35; }
	}

	.nh-id {
		font-family: var(--font-mono);
		font-size: 8px;
		color: var(--hud-text-dim);
		opacity: 0.6;
	}

	/* ── Feed body ───────────────────────────────────────────────── */
	.feed-body {
		flex: 1;
		min-height: 0;
		overflow: hidden;
	}
</style>
