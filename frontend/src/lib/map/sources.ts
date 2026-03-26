import type { Map } from 'maplibre-gl';

const API = '/api/v1';

// Layer → source-id → endpoint mapping
const GEOJSON_SOURCES: Record<string, string> = {
	contributors:       `${API}/proxy/contributors_map.json`,
	supporting:         `${API}/proxy/supporting_map.json`,
	user_groups:        `${API}/layers/user_groups`,
	events:             `${API}/layers/events`,
	// Static file — update manually in frontend/static/data/upcoming_events.geojson
	upcoming_events:    '/data/upcoming_events.geojson',
};

export async function initSources(map: Map) {
	for (const [id, url] of Object.entries(GEOJSON_SOURCES)) {
		try {
			const res = await fetch(url);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const geojson = await res.json();
			map.addSource(id, { type: 'geojson', data: geojson });
		} catch (err) {
			console.warn(`[sources] failed to load ${id}:`, err);
			// Add empty source so layers don't error
			map.addSource(id, {
				type: 'geojson',
				data: { type: 'FeatureCollection', features: [] },
			});
		}
	}
}

/** Re-fetch a single layer's data and update the source */
export async function refreshLayers(map: Map, layerName: string) {
	const url = GEOJSON_SOURCES[layerName];
	if (!url) return;
	const src = map.getSource(layerName) as maplibregl.GeoJSONSource | undefined;
	if (!src) return;
	try {
		const res = await fetch(url);
		if (!res.ok) return;
		const geojson = await res.json();
		src.setData(geojson);
	} catch {
		// ignore
	}
}
