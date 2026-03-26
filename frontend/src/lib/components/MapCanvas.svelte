<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { get } from 'svelte/store';
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { initSources } from '$lib/map/sources';
	import { initLayers, initUpcomingEventMarkers } from '$lib/map/layers';
	import { setupPopups } from '$lib/map/popup';
	import { layerState } from '$lib/stores/layers';

	const dispatch = createEventDispatcher<{ ready: maplibregl.Map }>();

	let mapContainer: HTMLDivElement;
	let map: maplibregl.Map;
	let upcomingMarkers: maplibregl.Marker[] = [];

	let cursorLon = $state<number | null>(null);
	let cursorLat = $state<number | null>(null);

	function formatCoord(val: number, posChar: string, negChar: string): string {
		return `${Math.abs(val).toFixed(4)}°${val >= 0 ? posChar : negChar}`;
	}

	// Watch layer visibility changes — also toggle halo/pulse companion layers
	$effect(() => {
		const state = $layerState;
		if (!map) return;
		Object.entries(state).forEach(([layerName, s]) => {
			// upcoming_events are HTML markers — show/hide the DOM elements directly
			if (layerName === 'upcoming_events') {
				const display = s.visible ? '' : 'none';
				for (const marker of upcomingMarkers) {
					marker.getElement().style.display = display;
				}
				return;
			}
			const visibility = s.visible ? 'visible' : 'none';
			if (map.getLayer(layerName)) {
				map.setLayoutProperty(layerName, 'visibility', visibility);
			}
			// Toggle glow halo and pulse rings together with parent layer
			for (const suffix of ['-halo', '-pulse', '-outline', '-label']) {
				const auxId = layerName + suffix;
				if (map.getLayer(auxId)) {
					map.setLayoutProperty(auxId, 'visibility', visibility);
				}
			}
		});
	});

	onMount(() => {
		map = new maplibregl.Map({
			container: mapContainer,
			style: {
				version: 8,
				sources: {
					'carto-dark': {
						type: 'raster',
						tiles: [
							'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
							'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
							'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'
						],
						tileSize: 256,
						attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>'
					}
				},
				layers: [
					{
						id: 'background',
						type: 'background',
						paint: { 'background-color': '#111c2b' }
					},
					{
						id: 'carto-dark-tiles',
						type: 'raster',
						source: 'carto-dark',
						paint: { 'raster-opacity': 0.85 }
					}
				]
			},
			center: [10, 30],
			zoom: 2,
			minZoom: 1.5,
			maxZoom: 18,
			renderWorldCopies: false,
			attributionControl: false
		});

		map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
		map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

		map.on('load', async () => {
			await initSources(map);
			initLayers(map);
			setupPopups(map);
			upcomingMarkers = await initUpcomingEventMarkers(map);
			// Apply any layer toggle that happened before markers were ready
			const initVisible = get(layerState).upcoming_events?.visible ?? true;
			if (!initVisible) {
				for (const m of upcomingMarkers) m.getElement().style.display = 'none';
			}
			dispatch('ready', map);
		});

		map.on('mousemove', (e) => {
			cursorLon = e.lngLat.lng;
			cursorLat = e.lngLat.lat;
		});

		// Use a DOM-level listener — MapLibre's map-level 'mouseleave' is
		// intended for layer-specific use and can mis-fire on the map canvas.
		map.getCanvas().addEventListener('mouseleave', () => {
			cursorLon = null;
			cursorLat = null;
		});
	});

	onDestroy(() => {
		if (map) map.remove();
	});
</script>

<div class="map-container" bind:this={mapContainer}></div>

<div class="coords-readout" class:visible={cursorLon !== null}>
	<span class="coords-icon">◎</span>
	{#if cursorLon !== null && cursorLat !== null}
		<span class="coords-val">{formatCoord(cursorLat, 'N', 'S')}</span>
		<span class="coords-sep">·</span>
		<span class="coords-val">{formatCoord(cursorLon, 'E', 'W')}</span>
	{:else}
		<span class="coords-val coords-idle">— / —</span>
	{/if}
</div>

<style>
	.map-container {
		position: fixed;
		inset: 0;
		width: 100%;
		height: 100%;
		z-index: 0;
	}

	.coords-readout {
		position: fixed;
		/* Centre-bottom: between both panel columns, above the stats bar */
		bottom: 74px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 110;
		display: flex;
		align-items: center;
		gap: 5px;
		padding: 4px 10px;
		background: rgba(17, 28, 43, 0.78);
		backdrop-filter: blur(18px) saturate(140%);
		border: 1px solid rgba(88, 150, 50, 0.22);
		border-radius: 8px;
		box-shadow: 0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(147,176,35,0.08);
		font-family: var(--font-mono);
		font-size: 11px;
		opacity: 0;
		transition: opacity 0.15s ease;
		pointer-events: none;
		white-space: nowrap;
	}

	.coords-readout.visible {
		opacity: 1;
	}

	.coords-icon {
		color: var(--qgis-light-green);
		text-shadow: 0 0 6px var(--qgis-light-green);
		font-size: 10px;
	}

	.coords-val {
		color: var(--hud-text);
		letter-spacing: 0.3px;
	}

	.coords-idle {
		color: var(--hud-text-dim);
	}

	.coords-sep {
		color: var(--hud-text-dim);
		font-size: 9px;
	}

	/* Scanline overlay */
	.map-container::after {
		content: '';
		position: absolute;
		inset: 0;
		background: repeating-linear-gradient(
			0deg,
			transparent,
			transparent 2px,
			rgba(0, 0, 0, 0.03) 2px,
			rgba(0, 0, 0, 0.03) 4px
		);
		pointer-events: none;
		z-index: 1;
	}
</style>
