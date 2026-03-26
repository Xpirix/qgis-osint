import type { Map } from 'maplibre-gl';
import { feedPush } from '$lib/stores/feeds';
import { statsApply } from '$lib/stores/stats';
import { layerState } from '$lib/stores/layers';
import { notifications } from '$lib/stores/notifications';
import { refreshLayers } from '$lib/map/sources';

let es: EventSource | null = null;
let map: Map | null = null;

interface SSEEvent {
	type: string;
	payload: Record<string, unknown>;
}

function handleEvent(evt: SSEEvent) {
	switch (evt.type) {
		// All feed items use 'feed_item' from the backend workers
		case 'feed_item':
		case 'commit':
		case 'release':
		case 'qep':
		case 'rss':
		case 'plugin':
		case 'hub': {
			const channel = evt.payload.channel as string ?? 'commits';
			feedPush(channel, {
				id: (evt.payload.id as string) ?? crypto.randomUUID(),
				channel,
				title: (evt.payload.title as string) ?? '',
				url: evt.payload.url as string | undefined,
				published: evt.payload.published as string | undefined,
				timestamp: evt.payload.timestamp as string | undefined,
				tag: evt.payload.tag as string | undefined,
				tag_color: evt.payload.tag_color as string | undefined,
				author: evt.payload.author as string | undefined,
				repo: evt.payload.repo as string | undefined,
			});
			break;
		}

		// stats_update is the event name from backend workers
		case 'stats_update':
		case 'stats':
			statsApply(evt.payload as Record<string, number>);
			break;

		case 'layer_update': {
			const layerName = evt.payload.layer as string;
			if (map) refreshLayers(map, layerName);
			// Flash the layer toggle briefly
			layerState.update(s => s); // force reactivity tick
			notifications.notify({
				title: `Layer updated: ${layerName}`,
				color: '#93b023',
			});
			break;
		}

		case 'ping':
			break;

		default:
			console.debug('[SSE] unknown event', evt.type);
	}
}

export function connectSSE(mapInstance: Map) {
	map = mapInstance;
	if (es) return; // already connected

	es = new EventSource('/api/v1/stream');

	es.addEventListener('message', (e: MessageEvent) => {
		try {
			const parsed: SSEEvent = JSON.parse(e.data);
			handleEvent(parsed);
		} catch {
			// silently ignore malformed frames
		}
	});

	es.addEventListener('error', () => {
		// Browser auto-reconnects; just log
		console.warn('[SSE] connection error – browser will retry');
	});
}

export function disconnectSSE() {
	es?.close();
	es = null;
	map = null;
}
