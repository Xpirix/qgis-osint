<script lang="ts">
	import { onMount } from 'svelte';

	interface Member {
		name: string;
		tier: string;
		country: string;
		website: string;
		logo_url: string;
	}

	const TIER_ORDER = ['flagship', 'large', 'medium', 'small'];

	const TIER_COLORS: Record<string, string> = {
		flagship: '#f0e64a',
		large:    '#fb923c',
		medium:   '#94a3b8',
		small:    '#52525b',
	};

	const TIER_LABELS: Record<string, string> = {
		flagship: 'FLAGSHIP',
		large:    'LARGE',
		medium:   'MEDIUM',
		small:    'SMALL',
	};

	let members = $state<Member[]>([]);
	let loading  = $state(true);
	let open     = $state(true);

	const grouped = $derived(
		TIER_ORDER
			.map(tier => ({ tier, items: members.filter(m => m.tier === tier) }))
			.filter(g => g.items.length > 0)
	);

	onMount(async () => {
		try {
			const res = await fetch('/api/v1/layers/members');
			if (res.ok) {
				const fc = await res.json();
				members = (fc.features ?? [])
					.map((f: { properties: Member }) => f.properties)
					.sort((a: Member, b: Member) => {
						const ti = TIER_ORDER.indexOf(a.tier);
						const tj = TIER_ORDER.indexOf(b.tier);
						return ti !== tj ? ti - tj : a.name.localeCompare(b.name);
					});
			}
		} catch { /* ignore */ }
		loading = false;
	});
</script>

<div class="nano-panel">
	<button class="nano-header" onclick={() => (open = !open)}>
		<span class="nh-icon">◈</span>
		<span class="nh-title">SUSTAINING MEMBERS</span>
		<span class="nh-count">{members.length || '…'}</span>
		<span class="nh-chevron">{open ? '▴' : '▾'}</span>
	</button>

	{#if open}
		<div class="members-body">
			{#if loading}
				<div class="members-empty">Loading…</div>
			{:else if grouped.length === 0}
				<div class="members-empty">No data yet</div>
			{:else}
				{#each grouped as group}
					<div class="tier-label" style="--tc: {TIER_COLORS[group.tier]}">
						{TIER_LABELS[group.tier]}
					</div>
					{#each group.items as m}
						<a
							href={m.website || '#'}
							target="_blank"
							rel="noopener noreferrer"
							class="member-row"
							title="{m.name} · {m.country}"
						>
							{#if m.logo_url}
								<img class="member-logo" src={m.logo_url} alt="" loading="lazy" />
							{:else}
								<span
									class="member-logo-ph"
									style="background:{TIER_COLORS[m.tier]}22; border-color:{TIER_COLORS[m.tier]}55"
								>{m.name[0] ?? '?'}</span>
							{/if}
							<span class="member-name">{m.name}</span>
							{#if m.country}<span class="member-country">{m.country}</span>{/if}
						</a>
					{/each}
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
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
		min-height: 0;
		flex-shrink: 1;
	}

	.nano-header {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 12px 7px;
		border-bottom: 1px solid rgba(88, 150, 50, 0.15);
		width: 100%;
		background: none;
		border: none;
		border-bottom: 1px solid rgba(88, 150, 50, 0.15);
		border-radius: 0;
		cursor: pointer;
		color: inherit;
		font: inherit;
		text-align: left;
	}
	.nano-header:hover { background: rgba(88, 150, 50, 0.06); }

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
	.nh-count {
		font-family: var(--font-mono);
		font-size: 9px;
		color: #fb923c;
	}
	.nh-chevron {
		font-size: 9px;
		color: var(--hud-text-dim, #475569);
		margin-left: 2px;
	}

	.members-body {
		max-height: 260px;
		overflow-y: auto;
		padding: 4px 0;
		scrollbar-width: thin;
		scrollbar-color: rgba(88, 150, 50, 0.3) transparent;
	}

	.tier-label {
		padding: 5px 12px 2px;
		font-family: var(--font-mono);
		font-size: 8px;
		letter-spacing: 1.5px;
		color: var(--tc);
		opacity: 0.85;
	}

	.member-row {
		display: flex;
		align-items: center;
		gap: 7px;
		padding: 3px 12px;
		text-decoration: none;
		transition: background 0.12s;
	}
	.member-row:hover { background: rgba(88, 150, 50, 0.08); }

	.member-logo {
		width: 18px;
		height: 18px;
		border-radius: 3px;
		object-fit: contain;
		flex-shrink: 0;
		background: rgba(255, 255, 255, 0.05);
	}
	.member-logo-ph {
		width: 18px;
		height: 18px;
		border-radius: 3px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 9px;
		font-weight: 700;
		color: #94a3b8;
		flex-shrink: 0;
		border: 1px solid;
	}

	.member-name {
		font-size: 9pt;
		color: #cbd5e1;
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.member-country {
		font-family: var(--font-mono);
		font-size: 9pt;
		color: #475569;
		flex-shrink: 0;
	}

	.members-empty {
		padding: 12px;
		font-size: 10px;
		color: #475569;
		text-align: center;
	}
</style>
