import maplibregl, { type Map } from 'maplibre-gl';

// ── colour palette per source ──────────────────────────────────────────────
const C = {
	contributors:    '#93b023',
	supporting:      '#f4e03a',
	user_groups:     '#38bdf8',
	events:          '#e879f9',
	upcoming_events: '#ee7913',
};

// ── Avatar size constants ──────────────────────────────────────────────────
const AVATAR_SIZE = 64;   // sprite pixel size
const AVATAR_INNER = 56;  // photo circle diameter
const RING_WIDTH = 2;     // coloured ring width

/**
 * Create a circular avatar sprite from a URL.
 * Returns an ImageData-like object { width, height, data } for map.addImage().
 */

async function makeAvatarSprite(
	url: string,
	ringColor = '#93b023',
): Promise<ImageData | null> {
	try {
		const res = await fetch(url);
		if (!res.ok) throw new Error('proxy fail');
		const blob = await res.blob();
		const bmp = await createImageBitmap(blob);

		const size = AVATAR_SIZE;
		const inner = AVATAR_INNER;
		const canvas = new OffscreenCanvas(size, size);
		const ctx = canvas.getContext('2d')!;
		const cx = size / 2;

		// Outer glow ring
		ctx.beginPath();
		ctx.arc(cx, cx, cx - 1, 0, Math.PI * 2);
		ctx.fillStyle = ringColor + '33'; // ~20% opacity glow
		ctx.fill();

		// Coloured border ring
		ctx.beginPath();
		ctx.arc(cx, cx, cx - 1, 0, Math.PI * 2);
		ctx.strokeStyle = ringColor;
		ctx.lineWidth = RING_WIDTH;
		ctx.stroke();

		// Clip to circle and draw photo
		ctx.save();
		ctx.beginPath();
		ctx.arc(cx, cx, inner / 2, 0, Math.PI * 2);
		ctx.clip();
		const offset = (size - inner) / 2;
		ctx.drawImage(bmp, offset, offset, inner, inner);
		ctx.restore();

		return ctx.getImageData(0, 0, size, size);
	} catch {
		return null;
	}
}

/**
 * Register the styleimagemissing handler so MapLibre loads avatar sprites
 * on demand when a symbol layer requests an image named "avatar:<avatarUrl>".
 */
export function registerAvatarLoader(map: Map) {
	map.on('styleimagemissing', async (e) => {
		const id: string = e.id;
		let avatarUrl: string;
		let ringColor: string;

		if (id.startsWith('supp-avatar:')) {
			avatarUrl = id.slice('supp-avatar:'.length);
			ringColor = C.supporting;
		} else if (id.startsWith('avatar:')) {
			avatarUrl = id.slice('avatar:'.length);
			ringColor = C.contributors;
		} else {
			return;
		}

		if (!avatarUrl) return;
		// Add placeholder immediately so the event doesn't fire again
		const placeholder = new ImageData(AVATAR_SIZE, AVATAR_SIZE);
		map.addImage(id, placeholder, { pixelRatio: 1 });
		const sprite = await makeAvatarSprite(avatarUrl, ringColor);
		if (sprite && map.hasImage(id)) {
			map.updateImage(id, sprite);
		}
	});
}

export function initLayers(map: Map) {

	// Register avatar loader for contributor symbols
	registerAvatarLoader(map);

	// ── User groups — filled country polygon (just above basemap) ──────────
	map.addLayer({
		id: 'user_groups',
		type: 'fill',
		source: 'user_groups',
		paint: {
			'fill-color': C.user_groups,
			'fill-opacity': 0.22,
		},
	});

	// ── User groups — country outline ───────────────────────────────────────
	map.addLayer({
		id: 'user_groups-outline',
		type: 'line',
		source: 'user_groups',
		paint: {
			'line-color': C.user_groups,
			'line-width': 1.5,
			'line-opacity': 0.85,
		},
	});

	// ── Events outer pulse ring (animated) ─────────────────────────────────
	map.addLayer({
		id: 'events-pulse',
		type: 'circle',
		source: 'events',
		paint: {
			'circle-radius': 10,
			'circle-color': C.events,
			'circle-opacity': 0.22,
			'circle-blur': 0.6,
			'circle-stroke-width': 0,
		},
	});

	// ── Events ─────────────────────────────────────────────────────────────
	map.addLayer({
		id: 'events',
		type: 'circle',
		source: 'events',
		paint: {
			'circle-radius': 8,
			'circle-color': C.events,
			'circle-opacity': 0.95,
			'circle-stroke-color': 'rgba(232,121,249,0.65)',
			'circle-stroke-width': 2,
		},
	});

	// ── Supporting contributors halo ──────────────────────────────────────
	map.addLayer({
		id: 'supporting-halo',
		type: 'circle',
		source: 'supporting',
		paint: {
			'circle-radius': 20,
			'circle-color': C.supporting,
			'circle-opacity': 0.12,
			'circle-blur': 1.0,
			'circle-stroke-width': 0,
		},
	});

	// ── Supporting contributors — avatar symbol layer ───────────────────────
	map.addLayer({
		id: 'supporting',
		type: 'symbol',
		source: 'supporting',
		layout: {
			'icon-image': [
				'concat',
				'supp-avatar:https://www.qgis.org',
				['coalesce', ['get', 'avatar_img'], ''],
			],
			'icon-size': 0.58,
			'icon-allow-overlap': true,
			'icon-ignore-placement': true,
			'icon-anchor': 'center',
		},
	});

	// ── Contributors halo (glow ring behind avatar) ────────────────────────
	map.addLayer({
		id: 'contributors-halo',
		type: 'circle',
		source: 'contributors',
		paint: {
			'circle-radius': [
				'interpolate', ['linear'],
				['coalesce', ['get', 'total_contributions'], 1],
				1, 14, 50, 20, 500, 30, 5000, 46,
			],
			'circle-color': C.contributors,
			'circle-opacity': 0.18,
			'circle-blur': 0.8,
			'circle-stroke-width': 0,
		},
	});

	// ── Contributors — avatar symbol layer (highest contributors on top) ───
	// Icon size is driven by contribution tier (0.42 → 0.92 of the 64px sprite)
	map.addLayer({
		id: 'contributors',
		type: 'symbol',
		source: 'contributors',
		layout: {
			'icon-image': [
				'concat',
				'avatar:',
				['coalesce', ['get', 'avatar_url'], ''],
			],
			'icon-size': [
				'interpolate', ['linear'],
				['coalesce', ['get', 'total_contributions'], 1],
				1,   0.42,
				50,  0.56,
				500, 0.72,
				5000, 0.92,
			],
			'icon-allow-overlap': true,
			'icon-ignore-placement': true,
			'icon-anchor': 'center',
			// Higher contributions render on top of lower ones
			'symbol-sort-key': ['coalesce', ['get', 'total_contributions'], 0],
		},
	});

	// ── Animate events pulse ring ────────────────────────────────────────────
	let phase = 0;
	const animateEventsPulse = () => {
		try {
			if (!map.getLayer('events-pulse')) return;
			phase = (phase + 0.022) % (Math.PI * 2);
			const t = (1 + Math.sin(phase)) / 2; // 0→1
			map.setPaintProperty('events-pulse', 'circle-radius', 8 + 22 * t);
			map.setPaintProperty('events-pulse', 'circle-opacity', 0.28 * (1 - t));
			requestAnimationFrame(animateEventsPulse);
		} catch {
			// Map was removed — animation naturally stops
		}
	};
	requestAnimationFrame(animateEventsPulse);
}

// ── Upcoming event alert-card HTML markers ─────────────────────────────────

const EVENT_COLOURS: Record<string, string> = {
	'QGIS User Conference 2026': '#93b023',
	'FOSS4G 2026':               '#38bdf8',
	'FOSS4G Europe 2026':        '#a855f7',
	'FOSS4G Asia 2026':          '#4b5563',
	'FOSS4G North America 2026': '#ee7913',
};

const esc = (s: string) =>
	s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export async function initUpcomingEventMarkers(map: maplibregl.Map): Promise<maplibregl.Marker[]> {
	const res = await fetch('/data/upcoming_events.geojson');
	const fc = await res.json() as { features: Array<{ geometry: { coordinates: [number, number] }, properties: Record<string, string> }> };
	const markers: maplibregl.Marker[] = [];

	for (const feature of fc.features) {
		const p        = feature.properties;
		const isPast   = p.status === 'past';
		const color    = isPast ? '#4b5563' : (EVENT_COLOURS[p.name] ?? '#ee7913');

		const el = document.createElement('div');
		el.className = 'ue-marker' + (isPast ? ' is-past' : '');
		el.style.setProperty('--ue-color', color);
		el.innerHTML = `
			<div class="ue-card">
				<button class="ue-close" title="Dismiss">&#215;</button>
				<div class="ue-header">!! CONF !!</div>
				<div class="ue-title">${esc(p.name)}</div>
				<div class="ue-meta">${esc(p.city)} · ${esc(p.country)}</div>
				<div class="ue-dates">${esc(p.dates)}</div>
				<a class="ue-footer" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">[REGISTER ↗]</a>
			</div>
			<div class="ue-stem"></div>
			<div class="ue-dot"></div>`;

		// Close toggles card + stem down to just the dot
		el.querySelector('.ue-close')!.addEventListener('click', (e) => {
			e.stopPropagation();
			(el.querySelector('.ue-card') as HTMLElement).classList.toggle('ue-hidden');
			(el.querySelector('.ue-stem') as HTMLElement).classList.toggle('ue-hidden');
		});

		const [lng, lat] = feature.geometry.coordinates;
		const marker = new maplibregl.Marker({ element: el, anchor: 'bottom', offset: [0, -4] })
			.setLngLat([lng, lat])
			.addTo(map);

		markers.push(marker);
	}

	return markers;
}
