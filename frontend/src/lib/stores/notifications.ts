import { writable } from 'svelte/store';

export interface Notification {
	id: string;
	title: string;
	body?: string;
	color?: string;
}

function createNotificationsStore() {
	const { subscribe, update } = writable<Notification[]>([]);

	function notify(n: Omit<Notification, 'id'>, ttl = 4000) {
		const id = crypto.randomUUID();
		update(list => [...list, { id, ...n }]);
		setTimeout(() => {
			update(list => list.filter(x => x.id !== id));
		}, ttl);
	}

	function dismiss(id: string) {
		update(list => list.filter(x => x.id !== id));
	}

	return { subscribe, notify, dismiss };
}

export const notifications = createNotificationsStore();
