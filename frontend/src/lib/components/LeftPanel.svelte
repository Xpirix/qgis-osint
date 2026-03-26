<script lang="ts">
	import { layerState, type LayerName } from '$lib/stores/layers';
	import { statsStore } from '$lib/stores/stats';
	import { LAYER_COLOURS, LAYER_LABELS, LAYER_ICONS } from '$lib/utils/colours';
	import SustainingMembersPanel from '$lib/components/SustainingMembersPanel.svelte';

	const LAYERS: LayerName[] = [
		'contributors', 'supporting', 'user_groups', 'events', 'upcoming_events'
	];

	function toggleLayer(name: LayerName) {
		layerState.update(s => ({
			...s,
			[name]: { ...s[name], visible: !s[name].visible }
		}));
	}

	const stats = $derived($statsStore);

	let collapsed = $state(false);
</script>

<!-- Three independent glass panels stacked on the left -->
<div class="left-col" class:collapsed>

	<!-- ── Panel 1: Layer toggles ───────────────────────────────────── -->
	<div class="nano-panel">
		<div class="nano-header">
			<span class="nh-icon">◈</span>
			<span class="nh-title">LAYERS</span>
			<span class="nh-id">SYS/LAY/001</span>
		</div>
		<div class="nano-body">
			{#each LAYERS as layer}
				{@const state = $layerState[layer]}
				<button
					class="layer-toggle"
					class:active={state.visible}
					onclick={() => toggleLayer(layer)}
					style="--layer-color: {LAYER_COLOURS[layer]}"
					title={LAYER_LABELS[layer]}
				>
					<span class="toggle-dot" class:on={state.visible}></span>
					<span class="toggle-icon">{LAYER_ICONS[layer]}</span>
					<span class="toggle-label">{LAYER_LABELS[layer]}</span>
				</button>
			{/each}
		</div>
	</div>

	<!-- ── Panel 2: Intelligence stats ─────────────────────────────── -->
	<div class="nano-panel">
		<div class="nano-header">
			<span class="nh-icon">◈</span>
			<span class="nh-title">INTEL</span>
			<span class="nh-id">SYS/INT/002</span>
		</div>
		<div class="nano-body nano-body--stats">
			<div class="stat-row">
				<span class="stat-label">Contributors</span>
				<span class="stat-value" style="color: var(--layer-contributors)">
					{stats.contributors_geo_located ?? '…'} / {stats.contributors_total ?? 809}
				</span>
			</div>
			<div class="stat-row">
				<span class="stat-label">User Groups</span>
				<span class="stat-value" style="color: var(--layer-usergroups)">{stats.user_groups ?? 38}</span>
			</div>
			<div class="stat-row">
				<span class="stat-label">Members</span>
				<span class="stat-value" style="color: var(--layer-members)">{stats.sustaining_members ?? '…'}</span>
			</div>
			<div class="stat-row">
				<span class="stat-label">Plugins</span>
				<span class="stat-value" style="color: var(--layer-analytics)">{stats.plugin_count?.toLocaleString() ?? '…'}</span>
			</div>
			{#if stats.plugin_downloads_total}
			<div class="stat-row">
				<span class="stat-label">↓ Downloads</span>
				<span class="stat-value" style="color: #fb923c">{stats.plugin_downloads_total.toLocaleString()}</span>
			</div>
			{/if}
			{#if stats.qgis_opens_yesterday}
			<div class="stat-row">
				<span class="stat-label">Users/day</span>
				<span class="stat-value" style="color: #38bdf8">{stats.qgis_opens_yesterday.toLocaleString()}</span>
			</div>
			{/if}
			<div class="stat-row">
				<span class="stat-label">Open QEPs</span>
				<span class="stat-value" style="color: var(--qgis-lemon)">{stats.open_qeps ?? '…'}</span>
			</div>
			{#if stats.github_stars}
			<div class="stat-row">
				<span class="stat-label">★ Stars</span>
				<span class="stat-value" style="color: #f4e03a">{stats.github_stars?.toLocaleString()}</span>
			</div>
			{/if}
		</div>
	</div>

	<!-- ── Panel 3: Release versions ───────────────────────────────── -->
	<div class="nano-panel">
		<div class="nano-header">
			<span class="nh-icon">◈</span>
			<span class="nh-title">RELEASE</span>
			<span class="nh-id">SYS/VER/003</span>
		</div>
		<div class="nano-body nano-body--release">
			<div class="ver-label">LATEST</div>
			<div class="ver-badge ver-latest">
				<span class="ver-num">QGIS {stats.latest_release ?? '…'}</span>
				{#if stats.latest_release_name}<span class="ver-name">{stats.latest_release_name}</span>{/if}
			</div>
			<div class="ver-label" style="margin-top:6px">LTR</div>
			<div class="ver-badge ver-ltr">
				<span class="ver-num ver-ltr-num">QGIS {stats.ltr_release ?? '…'}</span>
				{#if stats.ltr_release_name}<span class="ver-name">{stats.ltr_release_name}</span>{/if}
			</div>
		</div>
	</div>

	<!-- ── Panel 4: Sustaining Members list ────────────────────────── -->
	<SustainingMembersPanel />

</div>

<!-- Collapse/expand tab — always visible at the panel's right edge -->
<button
	class="panel-tab"
	class:is-collapsed={collapsed}
	onclick={() => (collapsed = !collapsed)}
	title={collapsed ? 'Expand panels' : 'Collapse panels'}
	aria-label={collapsed ? 'Expand left panels' : 'Collapse left panels'}
>›</button>

<style>
	/* ── Column container ─────────────────────────────────────────── */
	.left-col {
		position: fixed;
		left: 16px;
		top: 60px;
		bottom: 56px;
		width: 220px;
		z-index: 100;
		display: flex;
		flex-direction: column;
		gap: 8px;
		pointer-events: none; /* let gaps be click-through */
		transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.left-col.collapsed {
		transform: translateX(calc(-100% - 20px));
	}

	/* ── Collapse toggle tab ─────────────────────────────────────── */
	.panel-tab {
		position: fixed;
		top: 50%;
		transform: translateY(-50%);
		z-index: 101;
		left: calc(16px + 220px + 4px); /* right edge of column + 4px gap */
		width: 18px;
		height: 44px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		background: rgba(17, 28, 43, 0.82);
		backdrop-filter: blur(18px) saturate(140%);
		border: 1px solid rgba(88, 150, 50, 0.28);
		border-left: none;
		border-radius: 0 8px 8px 0;
		box-shadow: 3px 0 12px rgba(0,0,0,0.35);
		color: var(--qgis-light-green);
		font-family: var(--font-mono);
		font-size: 13px;
		line-height: 1;
		transition:
			left 0.3s cubic-bezier(0.4, 0, 0.2, 1),
			background 0.15s ease,
			border-color 0.15s ease;
	}

	.panel-tab.is-collapsed {
		left: 0;
		border-left: 1px solid rgba(88, 150, 50, 0.28);
		border-radius: 0 8px 8px 0;
	}

	.panel-tab:hover {
		background: rgba(17, 28, 43, 0.96);
		border-color: rgba(88, 150, 50, 0.55);
		box-shadow: 3px 0 16px rgba(147, 176, 35, 0.25);
		color: #c6e04a;
	}

	.panel-tab:focus-visible {
		outline: 1px solid var(--qgis-light-green);
		outline-offset: 2px;
	}

	/* ── Individual glass panel ──────────────────────────────────── */
	.nano-panel {
		background: rgba(17, 28, 43, 0.78);
		border: 1px solid rgba(88, 150, 50, 0.22);
		border-radius: 14px;
		backdrop-filter: blur(18px) saturate(140%);
		box-shadow:
			0 8px 32px rgba(0, 0, 0, 0.5),
			0 0 0 1px rgba(88, 150, 50, 0.07),
			inset 0 1px 0 rgba(147, 176, 35, 0.09);
		overflow: hidden;
		pointer-events: all;
	}

	/* ── Panel header ────────────────────────────────────────────── */
	.nano-header {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 12px 7px;
		border-bottom: 1px solid rgba(88, 150, 50, 0.15);
	}

	.nh-icon {
		color: var(--qgis-light-green);
		font-size: 11px;
	}

	.nh-title {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 10px;
		letter-spacing: 2px;
		color: var(--qgis-light-green);
		text-shadow: 0 0 8px rgba(147, 176, 35, 0.3);
		flex: 1;
	}

	.nh-id {
		font-family: var(--font-mono);
		font-size: 8px;
		color: var(--hud-text-dim);
		opacity: 0.6;
	}

	/* ── Panel body ──────────────────────────────────────────────── */
	.nano-body {
		padding: 4px 6px;
	}

	.nano-body--stats {
		padding: 3px 12px 6px;
	}

	.nano-body--release {
		padding: 8px 12px 10px;
	}

	/* ── Layer toggles ───────────────────────────────────────────── */
	.layer-toggle {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 5px 8px;
		background: transparent;
		border: none;
		border-radius: 7px;
		cursor: pointer;
		text-align: left;
		transition: background 0.2s;
		color: var(--hud-text-dim);
	}

	.layer-toggle:hover {
		background: rgba(88, 150, 50, 0.08);
		color: var(--hud-text);
	}

	.layer-toggle.active {
		color: var(--hud-text);
	}

	.toggle-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: rgba(88, 150, 50, 0.3);
		border: 1px solid rgba(88, 150, 50, 0.4);
		flex-shrink: 0;
		transition: all 0.2s;
	}

	.toggle-dot.on {
		background: var(--layer-color, var(--qgis-dark-green));
		border-color: var(--layer-color, var(--qgis-dark-green));
		box-shadow: 0 0 6px var(--layer-color, var(--qgis-dark-green));
	}

	.toggle-icon {
		font-size: 12px;
		width: 16px;
		text-align: center;
	}

	.toggle-label {
		font-family: var(--font-label);
		font-size: 11px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* ── Stats rows ──────────────────────────────────────────────── */
	.stat-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 4px 0;
		border-bottom: 1px solid rgba(88, 150, 50, 0.07);
	}

	.stat-row:last-child {
		border-bottom: none;
	}

	.stat-label {
		font-size: 11px;
		color: var(--hud-text-dim);
	}

	.stat-value {
		font-family: var(--font-mono);
		font-size: 11px;
		font-weight: 600;
		text-shadow: 0 0 6px currentColor;
	}

	/* ── Version badges ──────────────────────────────────────────── */
	.ver-label {
		font-family: var(--font-mono);
		font-size: 8px;
		letter-spacing: 1.5px;
		color: var(--hud-text-dim);
		margin-bottom: 3px;
	}

	.ver-badge {
		display: flex;
		align-items: baseline;
		gap: 6px;
		padding: 5px 9px;
		border-radius: 7px;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.07);
	}

	.ver-latest {
		border-color: rgba(147, 176, 35, 0.3);
		background: rgba(147, 176, 35, 0.06);
	}

	.ver-ltr {
		border-color: rgba(94, 163, 244, 0.25);
		background: rgba(94, 163, 244, 0.05);
	}

	.ver-num {
		font-family: var(--font-mono);
		font-size: 12px;
		font-weight: 700;
		color: var(--qgis-light-green);
		text-shadow: 0 0 8px rgba(147, 176, 35, 0.5);
	}

	.ver-ltr-num {
		color: #5ea3f4;
		text-shadow: 0 0 8px rgba(94, 163, 244, 0.4);
	}

	.ver-name {
		font-family: var(--font-mono);
		font-size: 9px;
		color: var(--hud-text-dim);
		font-style: italic;
	}
</style>
