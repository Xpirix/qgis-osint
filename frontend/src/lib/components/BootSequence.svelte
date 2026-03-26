<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{ booted: void }>();

	const BOOT_LINES = [
		{ text: '  ██████╗  ██████╗ ██╗███████╗      ██████╗ ███████╗██╗███╗   ██╗████████╗', delay: 50 },
		{ text: ' ██╔═══██╗██╔════╝ ██║██╔════╝     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝', delay: 50 },
		{ text: ' ██║   ██║██║  ███╗██║███████╗     ██║   ██║███████╗██║██╔██╗ ██║   ██║   ', delay: 50 },
		{ text: ' ██║▄▄ ██║██║   ██║██║╚════██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║   ', delay: 50 },
		{ text: ' ╚██████╔╝╚██████╔╝██║███████║     ╚██████╔╝███████║██║██║ ╚████║   ██║   ', delay: 50 },
		{ text: '  ╚══▀▀═╝  ╚═════╝ ╚═╝╚══════╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝   ', delay: 50 },
		{ text: '', delay: 100 },
		{ text: '  ◈ QGIS OSINT MATRIX  //  GEOSPATIAL INTELLIGENCE DASHBOARD  //  v1.0.0', delay: 80 },
		{ text: '', delay: 100 },
		{ text: '  [INIT] Loading geospatial intelligence modules...', delay: 150 },
		{ text: '  [INIT] Connecting to QGIS ecosystem data feeds...', delay: 200 },
		{ text: '  [MAP]  Loading CartoDB Dark Matter basemap...', delay: 250 },
		{ text: '  [DB]   Querying PostGIS spatial layers...', delay: 200 },
		{ text: '  [SSE]  Establishing live feed connection...', delay: 180 },
		{ text: '  [FEED] GitHub commit stream: ONLINE', delay: 150 },
		{ text: '  [FEED] QGIS News/Blog/Planet: ONLINE', delay: 120 },
		{ text: '  [FEED] Plugin repository feed: ONLINE', delay: 120 },
		{ text: '  [LAYER] Contributors map: LOADING', delay: 180 },
		{ text: '  [LAYER] User groups: READY', delay: 120 },
		{ text: '  [LAYER] Sustaining members: READY', delay: 120 },
		{ text: '', delay: 100 },
		{ text: '  ◈ ALL SYSTEMS NOMINAL — LAUNCHING INTERFACE', delay: 300 },
	];

	let lines: string[] = $state([]);
	let visible = $state(true);
	let cursor = $state(true);

	onMount(async () => {
		// Blink cursor
		const blinkInterval = setInterval(() => { cursor = !cursor; }, 530);

		let totalDelay = 0;
		for (let i = 0; i < BOOT_LINES.length; i++) {
			totalDelay += BOOT_LINES[i].delay;
			const idx = i;
			setTimeout(() => {
				lines = [...lines, BOOT_LINES[idx].text];
			}, totalDelay);
		}

		// Fade out after all lines
		setTimeout(() => {
			clearInterval(blinkInterval);
			cursor = false;
			visible = false;
			setTimeout(() => dispatch('booted'), 600);
		}, totalDelay + 800);
	});
</script>

{#if visible}
	<div class="boot" class:fade-out={!visible}>
		<div class="terminal">
			{#each lines as line}
				<div class="line">{line || '\u00a0'}</div>
			{/each}
			{#if cursor}
				<span class="cursor">▋</span>
			{/if}
		</div>
	</div>
{/if}

<style>
	.boot {
		position: fixed;
		inset: 0;
		background: #080e16;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9999;
		transition: opacity 0.6s ease;
	}

	.boot.fade-out {
		opacity: 0;
	}

	.terminal {
		font-family: 'Share Tech Mono', 'Courier New', monospace;
		font-size: clamp(9px, 1.1vw, 13px);
		color: #93b023;
		text-shadow: 0 0 8px rgba(147, 176, 35, 0.6);
		line-height: 1.5;
		max-width: 90vw;
		animation: fade-in 0.3s ease;
		white-space: pre;
	}

	.line {
		display: block;
		animation: slide-in 0.15s ease;
	}

	.cursor {
		display: inline-block;
		color: #93b023;
		animation: none;
	}

	@keyframes fade-in {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes slide-in {
		from { opacity: 0; transform: translateX(-4px); }
		to { opacity: 1; transform: translateX(0); }
	}
</style>
