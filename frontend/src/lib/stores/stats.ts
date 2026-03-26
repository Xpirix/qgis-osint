import { writable } from 'svelte/store';

export interface Stats {
	contributors_total?: number;
	contributors_geo_located?: number;
	user_groups?: number;
	sustaining_members?: number;
	plugin_count?: number;
	plugin_downloads_total?: number;
	qgis_opens_30d?: number;
	qgis_opens_yesterday?: number;
	hub_resources?: number;
	hub_styles?: number;
	hub_models?: number;
	hub_geopackages?: number;
	hub_3d_objects?: number;
	github_stars?: number;
	github_forks?: number;
	open_issues?: number;
	open_qeps?: number;
	latest_release?: string;
	latest_release_name?: string;
	ltr_release?: string;
	ltr_release_name?: string;
	latest_release_date?: string;
	[key: string]: unknown;
}

// Sensible offline defaults so the UI is never empty
const DEFAULTS: Stats = {
	contributors_total: 809,
	contributors_geo_located: 0,
	user_groups: 38,
	sustaining_members: 0,
	plugin_count: 1000,
	hub_resources: 0,
	github_stars: 0,
	github_forks: 0,
	open_issues: 0,
	open_qeps: 0,
	latest_release: '4.0',
	latest_release_name: 'Norrköping',
	ltr_release: '3.44',
	ltr_release_name: 'Solothurn',
};

export const statsStore = writable<Stats>({ ...DEFAULTS });

/** Merge a partial update into the stats store */
export function statsApply(patch: Partial<Stats>) {
	statsStore.update(s => ({ ...s, ...patch }));
}
