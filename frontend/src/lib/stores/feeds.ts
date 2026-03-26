import { writable } from 'svelte/store';

export interface FeedItem {
	id: string;
	channel: string;
	title: string;
	url?: string;
	published?: string;
	timestamp?: string;
	description?: string;
	tag?: string;
	tag_color?: string;
	author?: string;
	repo?: string;
}

export type FeedsStore = Record<string, FeedItem[]>;

export const feedsStore = writable<FeedsStore>({
	commits:     [],
	news:        [],
	blog:        [],
	planet:      [],
	plugins:     [],
	hub:         [],
	qeps:        [],
	changelog:   [],
	mailing_dev: [],
	mailing_user:[],
});

/** Prepend a new item to the given channel (keep at most 50).
 *
 * - New IDs are prepended as before.
 * - If the ID already exists but the incoming item has a strictly newer
 *   timestamp (e.g. a plugin that just released a new version), the stored
 *   entry is replaced and bubbled to the top so it's visible immediately.
 */
export function feedPush(channel: string, item: FeedItem) {
	feedsStore.update(state => {
		const existing = state[channel] ?? [];
		const existingIdx = existing.findIndex(i => i.id === item.id);

		if (existingIdx === -1) {
			// Genuinely new item — prepend
			return { ...state, [channel]: [item, ...existing].slice(0, 50) };
		}

		// Already known — only update if the incoming timestamp is strictly newer
		const prevTs = existing[existingIdx].timestamp ?? existing[existingIdx].published ?? '';
		const newTs  = item.timestamp ?? item.published ?? '';
		if (!newTs || newTs <= prevTs) return state;

		// Replace and move to front so the update is visible at the top
		const without = existing.filter((_, i) => i !== existingIdx);
		return { ...state, [channel]: [item, ...without].slice(0, 50) };
	});
}
