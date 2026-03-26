import type { LayerName } from '$lib/stores/layers';

export const LAYER_COLOURS: Record<LayerName, string> = {
	contributors:    '#93b023',
	supporting:      '#f4e03a',
	user_groups:     '#38bdf8',
	events:          '#e879f9',
	upcoming_events: '#ee7913',
};

export const LAYER_LABELS: Record<LayerName, string> = {
	contributors:    'Contributors',
	supporting:      'Supporting',
	user_groups:     'User Groups',
	events:          'Events',
	upcoming_events: 'Conf Events',
};

export const LAYER_ICONS: Record<LayerName, string> = {
	contributors:    '●',
	supporting:      '◆',
	user_groups:     '▲',
	events:          '★',
	upcoming_events: '◉',
};

// CSS custom property names (for use in app.css :root)
export const LAYER_CSS_VARS: Record<LayerName, string> = {
	contributors:    '--layer-contributors',
	supporting:      '--layer-supporting',
	user_groups:     '--layer-usergroups',
	events:          '--layer-events',
	upcoming_events: '--layer-events',
};
