<script lang="ts">
	import { onMount } from 'svelte';

	let time = $state('');
	let date = $state('');

	onMount(() => {
		const tick = () => {
			const now = new Date();
			const hh = now.getUTCHours().toString().padStart(2, '0');
			const mm = now.getUTCMinutes().toString().padStart(2, '0');
			const ss = now.getUTCSeconds().toString().padStart(2, '0');
			time = `${hh}:${mm}:${ss}`;
			const d = now.toISOString().slice(0, 10);
			date = d;
		};
		tick();
		const id = setInterval(tick, 1000);
		return () => clearInterval(id);
	});
</script>

<!-- Top bar -->
<div class="top-bar">
	<div class="title">
		<span class="diamond">◈</span>
		<span class="name">QGIS OSINT MATRIX</span>
	</div>
	<div class="right">
		<span class="date">{date}</span>
		<span class="clock">{time} UTC</span>
		<span class="live-dot" title="Live"></span>
	</div>
</div>

<!-- Corner brackets -->
<div class="corner tl"></div>
<div class="corner tr"></div>
<div class="corner bl"></div>
<div class="corner br"></div>

<!-- Vignette -->
<div class="vignette" aria-hidden="true"></div>

<!-- Scanning beam -->
<div class="scan-beam" aria-hidden="true"></div>

<style>
	.top-bar {
		position: fixed;
		top: 12px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 200;
		display: flex;
		align-items: center;
		gap: 24px;
		padding: 8px 20px;
		background: rgba(17, 28, 43, 0.82);
		backdrop-filter: blur(18px) saturate(140%);
		border: 1px solid rgba(88, 150, 50, 0.25);
		border-radius: 12px;
		box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(147,176,35,0.1);
		white-space: nowrap;
	}

	.title {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.diamond {
		color: var(--qgis-light-green);
		font-size: 14px;
	}

	.name {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 15px;
		letter-spacing: 3px;
		color: var(--qgis-light-green);
		text-shadow: 0 0 12px rgba(147, 176, 35, 0.4);
	}

	.right {
		display: flex;
		align-items: center;
		gap: 12px;
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--hud-text-dim);
	}

	.clock {
		color: var(--hud-accent);
		font-size: 13px;
		text-shadow: 0 0 8px rgba(147,176,35,0.3);
	}

	.live-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: #4caf50;
		box-shadow: 0 0 6px #4caf50;
		animation: pulse-live 2s ease-in-out infinite;
	}

	/* HUD corner brackets */
	.corner {
		position: fixed;
		z-index: 150;
		width: 24px;
		height: 24px;
		pointer-events: none;
	}

	.tl { top: 10px; left: 10px; border-top: 2px solid var(--qgis-dark-green); border-left: 2px solid var(--qgis-dark-green); }
	.tr { top: 10px; right: 10px; border-top: 2px solid var(--qgis-dark-green); border-right: 2px solid var(--qgis-dark-green); }
	.bl { bottom: 10px; left: 10px; border-bottom: 2px solid var(--qgis-dark-green); border-left: 2px solid var(--qgis-dark-green); }
	.br { bottom: 10px; right: 10px; border-bottom: 2px solid var(--qgis-dark-green); border-right: 2px solid var(--qgis-dark-green); }

	.vignette {
		position: fixed;
		inset: 0;
		z-index: 1;
		pointer-events: none;
		background: radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.55) 100%);
	}

	/* Scanning beam */
	.scan-beam {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		z-index: 2;
		pointer-events: none;
		background: linear-gradient(
			90deg,
			transparent 0%,
			rgba(147, 176, 35, 0.0) 20%,
			rgba(147, 176, 35, 0.7) 50%,
			rgba(147, 176, 35, 0.0) 80%,
			transparent 100%
		);
		box-shadow: 0 0 12px rgba(147,176,35,0.4), 0 0 2px rgba(147,176,35,0.8);
		animation: scan-down 10s linear infinite;
	}

	@keyframes scan-down {
		0%   { top: 0;        opacity: 0; }
		3%   { opacity: 1; }
		97%  { opacity: 0.6; }
		100% { top: 100vh;   opacity: 0; }
	}

	@keyframes pulse-live {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(0.85); }
	}
</style>
