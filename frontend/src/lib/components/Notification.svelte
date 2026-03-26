<script lang="ts">
	import { notifications } from '$lib/stores/notifications';
</script>

<div class="notifications-layer" aria-live="polite">
	{#each $notifications as n (n.id)}
		<div
			class="toast"
			style="--toast-color: {n.color ?? '#93b023'}"
			role="alert"
		>
			<span class="toast-dot"></span>
			<div class="toast-body">
				<div class="toast-title">{n.title}</div>
				{#if n.body}
					<div class="toast-body-text">{n.body}</div>
				{/if}
			</div>
			<button
				class="toast-close"
				onclick={() => notifications.dismiss(n.id)}
				aria-label="Dismiss"
			>×</button>
		</div>
	{/each}
</div>

<style>
	.notifications-layer {
		position: fixed;
		bottom: 64px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 9999;
		display: flex;
		flex-direction: column-reverse;
		gap: 6px;
		pointer-events: none;
	}

	.toast {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 14px;
		background: rgba(15,24,38,0.92);
		backdrop-filter: blur(18px);
		border: 1px solid rgba(88,150,50,0.25);
		border-left: 3px solid var(--toast-color);
		border-radius: 8px;
		box-shadow: 0 4px 20px rgba(0,0,0,0.5);
		min-width: 260px;
		max-width: 400px;
		pointer-events: all;
		animation: slidein 0.2s ease-out;
	}

	@keyframes slidein {
		from { opacity: 0; transform: translateY(10px); }
		to   { opacity: 1; transform: translateY(0); }
	}

	.toast-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--toast-color);
		box-shadow: 0 0 6px var(--toast-color);
		flex-shrink: 0;
	}

	.toast-body {
		flex: 1;
	}

	.toast-title {
		font-size: 12px;
		color: #e2e8f0;
		font-weight: 600;
	}

	.toast-body-text {
		font-size: 11px;
		color: var(--hud-text-dim);
		margin-top: 2px;
	}

	.toast-close {
		background: transparent;
		border: none;
		color: var(--hud-text-dim);
		font-size: 16px;
		cursor: pointer;
		padding: 0 2px;
		line-height: 1;
		flex-shrink: 0;
	}

	.toast-close:hover {
		color: #e2e8f0;
	}
</style>
