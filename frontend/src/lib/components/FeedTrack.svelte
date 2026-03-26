<script lang="ts">
	import { feedsStore } from '$lib/stores/feeds';
	import { relativeTime, truncate } from '$lib/utils/format';
	import type { FeedItem } from '$lib/stores/feeds';

	let { channels, color } = $props<{ channels: string[]; color: string }>();

	const items = $derived((() => {
		const seen = new Set<string>();
		const merged: FeedItem[] = [];
		for (const ch of channels) {
			for (const item of ($feedsStore[ch] ?? [])) {
				if (!seen.has(item.id)) {
					seen.add(item.id);
					merged.push(item);
				}
			}
		}
		return merged.sort((a, b) =>
			(b.published ?? b.timestamp ?? '').localeCompare(a.published ?? a.timestamp ?? '')
		);
	})());
</script>

<div class="feed-track">
	{#if items.length === 0}
		<div class="empty">
			<span class="empty-dot" style="color: {color}">◈</span>
			<span>Awaiting data stream…</span>
		</div>
	{:else}
		{#each items as item (item.id)}
			<article class="feed-item" style="--item-color: {color}">
				<div class="item-meta">
					{#if item.tag}
						<span
							class="item-tag"
							style="--tag-c: {item.tag_color ?? color}"
						>{item.tag}</span>
					{/if}
					<span class="item-time">{relativeTime(item.published)}</span>
					{#if item.repo}
						<span class="item-repo">{item.repo}</span>
					{/if}
				</div>
				<div class="item-title">
					{#if item.url}
						<a href={item.url} target="_blank" rel="noopener" class="item-link">
							{truncate(item.title)}
						</a>
					{:else}
						{truncate(item.title)}
					{/if}
				</div>
				{#if item.author}
					<div class="item-author">by {item.author}</div>
				{/if}
			</article>
		{/each}
	{/if}
</div>

<style>
	.feed-track {
		height: 100%;
		overflow-y: auto;
		padding: 4px 0;
		scrollbar-width: thin;
		scrollbar-color: rgba(88,150,50,0.3) transparent;
	}

	.feed-track::-webkit-scrollbar { width: 3px; }
	.feed-track::-webkit-scrollbar-track { background: transparent; }
	.feed-track::-webkit-scrollbar-thumb { background: rgba(88,150,50,0.3); border-radius: 2px; }

	.empty {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 20px 14px;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--hud-text-dim);
	}

	.empty-dot {
		font-size: 14px;
		animation: breathe 2s infinite;
	}

	@keyframes breathe {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}

	.feed-item {
		padding: 8px 14px;
		border-left: 2px solid transparent;
		transition: border-color 0.2s, background 0.15s;
		cursor: default;
	}

	.feed-item:hover {
		border-left-color: var(--item-color);
		background: rgba(255,255,255,0.03);
	}

	.item-meta {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 3px;
	}

	.item-tag {
		font-family: var(--font-mono);
		font-size: 9px;
		letter-spacing: 0.5px;
		border: 1px solid var(--tag-c, currentColor);
		border-radius: 3px;
		padding: 1px 5px;
		color: var(--tag-c, currentColor);
		background: color-mix(in srgb, var(--tag-c, currentColor) 18%, transparent);
		font-weight: 700;
	}

	.item-time {
		font-family: var(--font-mono);
		font-size: 9px;
		color: var(--hud-text-dim);
		flex: 1;
	}

	.item-repo {
		font-family: var(--font-mono);
		font-size: 9px;
		color: var(--hud-text-dim);
		opacity: 0.7;
	}

	.item-title {
		font-size: 12px;
		color: var(--hud-text);
		line-height: 1.4;
	}

	.item-link {
		color: inherit;
		text-decoration: none;
	}

	.item-link:hover {
		color: var(--item-color);
		text-decoration: underline;
	}

	.item-author {
		font-size: 10px;
		color: var(--hud-text-dim);
		margin-top: 2px;
	}
</style>
