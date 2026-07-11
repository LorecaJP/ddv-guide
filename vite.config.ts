import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { VitePWA } from 'vite-plugin-pwa'

// GitHub Pages（プロジェクトページ）でもローカルでも動くよう相対ベース。
// もし https://<user>.github.io/ddv-guide/ で公開するなら base を '/ddv-guide/' に変更。
export default defineConfig({
  base: './',
  plugins: [
    svelte(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/apple-touch-icon.png', 'icons/favicon-64.png'],
      manifest: {
        name: 'DDV 攻略メモ（個人用）',
        short_name: 'DDV攻略メモ',
        description: 'Disney Dreamlight Valley 自分用の攻略メモ',
        lang: 'ja',
        theme_color: '#17141f',
        background_color: '#17141f',
        display: 'standalone',
        orientation: 'portrait',
        start_url: './',
        scope: './',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // アプリ本体＋データ(JSONはJSにバンドル済み)をプリキャッシュ
        globPatterns: ['**/*.{js,css,html,woff2}'],
        // 画像はオンデマンドでキャッシュ（オフラインでも一度見た画像は表示）
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.destination === 'image',
            handler: 'CacheFirst',
            options: {
              cacheName: 'ddv-images',
              expiration: { maxEntries: 400, maxAgeSeconds: 60 * 60 * 24 * 60 },
            },
          },
        ],
        maximumFileSizeToCacheInBytes: 6 * 1024 * 1024,
      },
      devOptions: { enabled: false },
    }),
  ],
})
