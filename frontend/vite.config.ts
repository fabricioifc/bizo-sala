import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      pwaAssets: { config: true },
      manifest: {
        name: 'Bizo Sala',
        short_name: 'Bizo Sala',
        description: 'Chamada, conteúdo, carga horária e notas das turmas',
        lang: 'pt-BR',
        theme_color: '#059669',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
      },
      workbox: {
        // Inclui fontes (Rawline e Font Awesome) para a interface funcionar offline
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
        // Fontes SVG legadas do Font Awesome (~1 MB): navegadores atuais usam woff2
        globIgnores: ['**/fa-*.svg'],
        // A API nunca é servida pelo cache do service worker
        navigateFallbackDenylist: [/^\/api/],
      },
    }),
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: { '/api': process.env.API_URL ?? 'http://localhost:8000' },
    // Bind mount do Windows não propaga eventos de arquivo para o container
    watch: { usePolling: process.env.VITE_POLLING === 'true' },
  },
  test: {
    environment: 'jsdom',
  },
})
