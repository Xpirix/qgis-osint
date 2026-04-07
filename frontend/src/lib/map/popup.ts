import type { Map, Popup } from 'maplibre-gl';
import maplibregl from 'maplibre-gl';

const LAYER_IDS = [
	'contributors', 'supporting', 'user_groups', 'user_groups-outline',
	'events',
];

// ── HTML builders per layer ────────────────────────────────────────────────

function contributors(props: Record<string, unknown>) {
	const avatarUrl = escape(props.avatar_url ?? '');
	const login = escape(props.login ?? '');
	const name = escape(props.name ?? props.login ?? 'Unknown');
	return `
		<div class="popup-header">
			${avatarUrl ? `<img class="popup-avatar" src="${avatarUrl}" alt="" width="36" height="36" loading="lazy">` : ''}
			<div class="popup-header-text">
				<span class="popup-badge" style="--badge: #93b023">CONTRIBUTOR</span>
				<strong>${name}</strong>
			</div>
		</div>
		<div class="popup-body">
			<div class="popup-row"><span class="popup-key">Contributions</span>
				<span class="popup-val">${props.total_contributions ?? '—'}</span></div>
			${login ? `<div class="popup-row"><span class="popup-key">GitHub</span>
				<a href="https://github.com/${login}" target="_blank" class="popup-link">
					@${login}</a></div>` : ''}
		</div>`;
}

function supporting(props: Record<string, unknown>) {
	const roles = Array.isArray(props.roles) ? (props.roles as string[]).slice(0, 2).join(', ') : '';
	return `
		<div class="popup-header">
			<span class="popup-badge" style="--badge: #f4e03a">SUPPORTER</span>
			<strong>${escape(props.name ?? 'Unknown')}</strong>
		</div>
		<div class="popup-body">
			${roles ? `<div class="popup-row"><span class="popup-key">Roles</span>
				<span class="popup-val">${escape(roles)}</span></div>` : ''}
			<div class="popup-row"><span class="popup-key">Since</span>
				<span class="popup-val">${props.start_date ? String(props.start_date).slice(0, 4) : '—'}</span></div>
			${props.link ? `<div class="popup-row"><span class="popup-key">Link</span>
				<a href="${escape(props.link)}" target="_blank" class="popup-link">Visit ↗</a></div>` : ''}
		</div>`;
}

function user_groups(props: Record<string, unknown>) {
	return `
		<div class="popup-header">
			<span class="popup-badge" style="--badge: #38bdf8">USER GROUP</span>
			<strong>${escape(props.name ?? 'Unknown')}</strong>
		</div>
		<div class="popup-body">
			<div class="popup-row"><span class="popup-key">Country</span>
				<span class="popup-val">${escape(props.country_name ?? props.country ?? '—')}</span></div>
			${props.year ? `<div class="popup-row"><span class="popup-key">Since</span>
				<span class="popup-val">${props.year}</span></div>` : ''}
			${props.website ? `<div class="popup-row"><span class="popup-key">Website</span>
				<a href="${escape(props.website)}" target="_blank" class="popup-link">Visit ↗</a></div>` : ''}
		</div>`;
}

function events(props: Record<string, unknown>) {
	return `
		<div class="popup-header">
			<span class="popup-badge" style="--badge: #e879f9">HACKFEST</span>
			<strong>${escape(props.name ?? 'Unknown')}</strong>
		</div>
		<div class="popup-body">
			<div class="popup-row"><span class="popup-key">Location</span>
				<span class="popup-val">${escape(props.city ?? '—')}</span></div>
			<div class="popup-row"><span class="popup-key">Date</span>
				<span class="popup-val">${escape(props.date ?? props.date_start ?? '—')}</span></div>
			${props.notes ? `<div class="popup-row"><span class="popup-key">Notes</span>
				<span class="popup-val">${escape(props.notes)}</span></div>` : ''}
		</div>`;
}

function upcoming_events(props: Record<string, unknown>) {
	const isPast = props.status === 'past';
	const color = isPast ? '#94a3b8' : '#ee7913';
	return `
		<div class="popup-header">
			<span class="popup-badge" style="--badge: ${color}">${isPast ? 'PAST' : 'EVENT'}</span>
			<strong>${escape(props.name ?? 'Unknown')}</strong>
		</div>
		<div class="popup-body">
			${props.image ? `<img src="${escape(props.image)}" alt="${escape(props.name ?? '')}" style="width:100%;border-radius:4px;margin-bottom:8px;display:block;opacity:0.9">` : ''}
			<div class="popup-row"><span class="popup-key">Dates</span>
				<span class="popup-val">${escape(props.dates ?? '—')}</span></div>
			<div class="popup-row"><span class="popup-key">Location</span>
				<span class="popup-val">${escape(props.city ?? '—')}, ${escape(props.country ?? '')}</span></div>
			${props.venue && props.venue !== props.city
				? `<div class="popup-row"><span class="popup-key">Venue</span>
				<span class="popup-val">${escape(props.venue)}</span></div>` : ''}
			${props.url ? `<div class="popup-row"><span class="popup-key">Website</span>
				<a href="${escape(props.url)}" target="_blank" class="popup-link">Visit ↗</a></div>` : ''}
		</div>`;
}

function generic(badge: string, color: string, props: Record<string, unknown>) {
	return `
		<div class="popup-header">
			<span class="popup-badge" style="--badge: ${color}">${badge}</span>
			<strong>${escape(props.name ?? 'Unknown')}</strong>
		</div>
		<div class="popup-body">
			${props.country ? `<div class="popup-row"><span class="popup-key">Country</span>
				<span class="popup-val">${escape(props.country)}</span></div>` : ''}
			${props.website ? `<div class="popup-row"><span class="popup-key">Website</span>
				<a href="${escape(props.website)}" target="_blank" class="popup-link">Visit ↗</a></div>` : ''}
		</div>`;
}

function escape(v: unknown): string {
	return String(v ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function buildHTML(layerId: string, props: Record<string, unknown>): string {
	switch (layerId) {
		case 'contributors':     return contributors(props);
		case 'supporting':       return supporting(props);
		case 'user_groups':
		case 'user_groups-outline': return user_groups(props);
		case 'events':           return events(props);
		case 'upcoming_events':  return upcoming_events(props);
		default:                 return generic('POINT', '#93b023', props);
	}
}

const CSS = `
<style>
.maplibregl-popup-content {
	background: rgba(15,24,38,0.92) !important;
	backdrop-filter: blur(18px);
	border: 1px solid rgba(88,150,50,0.25);
	border-radius: 10px;
	padding: 0;
	color: #e2e8f0;
	min-width: 200px;
	box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.maplibregl-popup-tip { border-top-color: rgba(15,24,38,0.92) !important; }
.popup-header {
	padding: 10px 14px 6px;
	border-bottom: 1px solid rgba(88,150,50,0.15);
	display: flex;
	flex-direction: row;
	align-items: center;
	gap: 10px;
}
.popup-avatar {
	width: 36px;
	height: 36px;
	border-radius: 50%;
	object-fit: cover;
	border: 1px solid rgba(147,176,35,0.3);
	flex-shrink: 0;
}
.popup-logo {
	border-radius: 6px;
	object-fit: contain;
	background: rgba(255,255,255,0.06);
}
.popup-header-text {
	display: flex;
	flex-direction: column;
	gap: 3px;
	min-width: 0;
}
.popup-badge {
	font-family: monospace;
	font-size: 9px;
	letter-spacing: 1.5px;
	color: var(--badge);
	text-shadow: 0 0 6px var(--badge);
}
.popup-header strong {
	font-size: 13px;
	font-weight: 700;
	color: #f1f5f9;
}
.popup-body { padding: 6px 14px 10px; }
.popup-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 8px;
	padding: 3px 0;
}
.popup-key { font-size: 11px; color: #64748b; }
.popup-val { font-size: 11px; color: #94a3b8; font-family: monospace; }
.popup-link { font-size: 11px; color: #93b023; text-decoration: none; }
.popup-link:hover { text-decoration: underline; }
</style>
`;

// Point layers take priority over polygon layers when features overlap
const POINT_LAYER_IDS = ['contributors', 'supporting', 'events'];
const POLYGON_LAYER_IDS = ['user_groups', 'user_groups-outline'];

let activePopup: Popup | null = null;

export function setupPopups(map: Map) {
	// Inject shared CSS once
	if (!document.getElementById('popup-css')) {
		const el = document.createElement('div');
		el.id = 'popup-css';
		el.innerHTML = CSS;
		document.head.appendChild(el.firstElementChild!);
	}

	// Single handler: query all interactive layers then pick the best feature.
	// Point/symbol features always win over polygon features so that a contributor
	// or event pin above a user-group country polygon gets its own popup.
	map.on('click', (e) => {
		if ((e.originalEvent.target as Element)?.closest('.ue-marker')) return;
		const features = map.queryRenderedFeatures(e.point, { layers: LAYER_IDS });
		if (!features.length) return;

		const feature =
			features.find(f => POINT_LAYER_IDS.includes(f.layer.id)) ??
			features.find(f => POLYGON_LAYER_IDS.includes(f.layer.id));
		if (!feature) return;

		const layerId = feature.layer.id;
		const props = (feature.properties ?? {}) as Record<string, unknown>;
		const geo = feature.geometry as GeoJSON.Geometry;

		let lng: number, lat: number;
		if (geo.type === 'Point') {
			[lng, lat] = (geo as GeoJSON.Point).coordinates as [number, number];
		} else {
			lng = e.lngLat.lng;
			lat = e.lngLat.lat;
		}

		activePopup?.remove();
		activePopup = new maplibregl.Popup({ closeButton: true, maxWidth: '300px' })
			.setLngLat([lng, lat])
			.setHTML(buildHTML(layerId, props))
			.addTo(map);
	});

	// Cursor feedback — still register per-layer so pointer appears on hover
	for (const layerId of LAYER_IDS) {
		map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer'; });
		map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = ''; });
	}
}
