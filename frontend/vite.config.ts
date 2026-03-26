import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	// Target ES2022+ so esbuild uses native class fields instead of __publicField
	// helpers, which MapLibre GL v5 requires.
	optimizeDeps: {
		esbuildOptions: { target: 'es2022' },
	},
	build: {
		target: 'es2022',
	},
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
