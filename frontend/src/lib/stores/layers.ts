import { writable } from 'svelte/store';

export type LayerName =
	| 'contributors'
	| 'supporting'
	| 'user_groups'
	| 'events'
	| 'upcoming_events';

export interface LayerState {
	visible: boolean;
}

export type LayersStore = Record<LayerName, LayerState>;

const defaults: LayersStore = {
	contributors:    { visible: true },
	supporting:      { visible: true },
	user_groups:     { visible: true },
	events:          { visible: true },
	upcoming_events: { visible: true },
};

export const layerState = writable<LayersStore>(defaults);
