<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import BootSequence from '$lib/components/BootSequence.svelte';
	import MapCanvas from '$lib/components/MapCanvas.svelte';
	import HudChrome from '$lib/components/HudChrome.svelte';
	import LeftPanel from '$lib/components/LeftPanel.svelte';
	import RightPanel from '$lib/components/RightPanel.svelte';
	import BottomBar from '$lib/components/BottomBar.svelte';
	import Notification from '$lib/components/Notification.svelte';
	import { connectSSE } from '$lib/stores/sse';
	import { statsStore } from '$lib/stores/stats';
	import { feedsStore } from '$lib/stores/feeds';

	let booted = $state(false);
	let mapInstance: maplibregl.Map | null = $state(null);

	function onBooted() {
		booted = true;
	}

	function onMapReady(map: maplibregl.Map) {
		mapInstance = map;
		connectSSE(map);
	}

	// Load initial stats + all feeds on mount in parallel so panels aren't empty
	onMount(async () => {
		const FEED_CHANNELS = ['commits', 'news', 'blog', 'planet', 'plugins', 'hub', 'qeps'] as const;
		const [statsR, ...feedRs] = await Promise.allSettled([
			fetch('/api/v1/stats'),
			...FEED_CHANNELS.map(ch => fetch(`/api/v1/feeds/${ch}?limit=30`)),
		]);

		if (statsR.status === 'fulfilled' && statsR.value.ok) {
			try {
				const data = await statsR.value.json();
				statsStore.update(s => ({ ...s, ...data }));
			} catch (_) {}
		}

		for (let i = 0; i < FEED_CHANNELS.length; i++) {
			const r = feedRs[i];
			if (r.status === 'fulfilled' && r.value.ok) {
				try {
					const items = await r.value.json();
					if (Array.isArray(items) && items.length > 0) {
						feedsStore.update(s => ({ ...s, [FEED_CHANNELS[i]]: items }));
					}
				} catch (_) {}
			}
		}
	});
</script>

<svelte:head>
	<title>QGIS OSINT Matrix</title>
</svelte:head>

{#if !booted}
	<BootSequence on:booted={onBooted} />
{/if}

<div class="dashboard" class:visible={booted}>
	<!-- Full-screen WebGL map -->
	<MapCanvas on:ready={(e) => onMapReady(e.detail)} />

	<!-- HUD overlay chrome -->
	<HudChrome />

	<!-- Left panel: layer controls + mini stats -->
	<LeftPanel />

	<!-- Right panel: live feed tracks -->
	<RightPanel />

	<!-- Bottom stats bar -->
	<BottomBar />

	<!-- Toast notifications -->
	<Notification />
</div>

<style>
	.dashboard {
		position: fixed;
		inset: 0;
		opacity: 0;
		pointer-events: none;
		transition: opacity 0.8s ease;
	}
	.dashboard.visible {
		opacity: 1;
		pointer-events: all;
	}
</style>
