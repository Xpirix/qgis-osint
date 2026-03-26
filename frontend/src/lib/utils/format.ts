import { formatDistanceToNow, format } from 'date-fns';

export function relativeTime(iso: string | undefined): string {
	if (!iso) return '—';
	try {
		return formatDistanceToNow(new Date(iso), { addSuffix: true });
	} catch {
		return iso;
	}
}

export function shortDate(iso: string | undefined): string {
	if (!iso) return '—';
	try {
		return format(new Date(iso), 'dd MMM yyyy');
	} catch {
		return iso;
	}
}

export function compactNumber(n: number | undefined): string {
	if (n === undefined || n === null) return '—';
	if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
	if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
	return String(n);
}

export function truncate(s: string, len = 72): string {
	return s.length > len ? s.slice(0, len) + '…' : s;
}
