<script lang="ts">
  import { route, navigate } from './lib/router'
  import { CATEGORIES } from './lib/schema'
  import Hub from './routes/Hub.svelte'
  import CharactersZukan from './routes/CharactersZukan.svelte'
  import RecipesTable from './routes/RecipesTable.svelte'
  import MaterialsTable from './routes/MaterialsTable.svelte'
  import CraftingTable from './routes/CraftingTable.svelte'
  import ItemTable from './routes/ItemTable.svelte'
  import CompanionsZukan from './routes/CompanionsZukan.svelte'
  import MountsZukan from './routes/MountsZukan.svelte'
  import DataTable from './routes/DataTable.svelte'
  import LinkList from './routes/LinkList.svelte'
  import Dashboard from './routes/Dashboard.svelte'
  import CategoryPlaceholder from './routes/CategoryPlaceholder.svelte'

  const current = $derived($route.category)
  const meta = $derived(CATEGORIES.find((c) => c.key === current) ?? null)

  // スーパーリロード: SW・キャッシュを全消去して最新を取得（スマホで強制更新できない対策）
  let reloading = $state(false)
  async function superReload() {
    if (reloading) return
    reloading = true
    try {
      if ('serviceWorker' in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations()
        await Promise.all(regs.map((r) => r.unregister()))
      }
      if ('caches' in window) {
        const keys = await caches.keys()
        await Promise.all(keys.map((k) => caches.delete(k)))
      }
    } catch {
      /* 失敗しても再読み込みは行う */
    }
    // クエリにタイムスタンプを付けてHTTPキャッシュも回避（ハッシュ以降のルートは維持）
    const u = new URL(location.href)
    u.searchParams.set('_r', String(Date.now()))
    location.replace(u.toString())
  }
</script>

<header class="topbar">
  <div class="container bar">
    <button class="brand" onclick={() => navigate(null)}>
      <span class="mark">✦</span>
      <span>DDV 攻略メモ</span>
    </button>
    {#if meta}
      <nav class="crumbs">
        <button onclick={() => navigate(null)}>トップ</button>
        <span class="sep">/</span>
        <span class="here">{meta.emoji} {meta.name_ja}</span>
      </nav>
    {/if}
  </div>
</header>

<main class="container">
  {#if !current}
    <Hub />
  {:else if current === 'characters'}
    <CharactersZukan />
  {:else if current === 'recipes'}
    <RecipesTable />
  {:else if current === 'materials'}
    <MaterialsTable />
  {:else if current === 'crafting'}
    <CraftingTable />
  {:else if current === 'flowers'}
    <ItemTable storeKey="flowers" title="花" sub="種類ごと・名前タップで採取エリア"
      catOrder={['フォーリングペンステモン', 'ライジングペンステモン', 'タンポポ', 'デイジー', 'アジサイ', 'ヒマワリ', 'ベルフラワー', 'ヒメユリ', 'スワンプミルクウィード', 'アナナス', 'ヤネバンダイソウ', 'パッションリリー', 'キンレンカ', 'インパチェンス', 'バラ', '極楽鳥花', '発光する花', 'ウツボカズラ', 'ハエトリグサ', 'ガラスのような花', 'サボテンの花', 'ブックフラワー', 'エターナル・ポピー', 'クロッカス', 'シルクの花', 'スズラン', 'ジギタリス', 'アザミ']}
      placeholder="🌸" ownLabel="入手" />
  {:else if current === 'hourglass'}
    <ItemTable storeKey="hourglass" title="砂時計" sub="A Rift in Time の時渦アイテム。名前タップで入手条件"
      catOrder={['時空歪曲パーツ', 'カケラ', 'ギフト']}
      placeholder="⏳" ownLabel="入手" />
  {:else if current === 'companions'}
    <CompanionsZukan />
  {:else if current === 'mounts'}
    <MountsZukan />
  {:else if meta?.display === 'links'}
    <LinkList storeKey={current} />
  {:else if meta?.display === 'dashboard'}
    <Dashboard />
  {:else if meta?.display === 'table'}
    <DataTable storeKey={current} />
  {:else if meta}
    <CategoryPlaceholder {meta} />
  {:else}
    <CategoryPlaceholder meta={null} />
  {/if}
</main>

<footer class="foot container">
  <div class="foot-reload">
    <button class="reload-btn" onclick={superReload} disabled={reloading}>
      {reloading ? '更新中…' : '🔄 スーパーリロード'}
    </button>
    <span class="reload-note">最新に更新されない時に押してください（キャッシュを消去して再読み込み）</span>
  </div>
  <p class="foot-cred">個人運営の攻略メモ。データ・画像出典: Disney Dreamlight Valley Wiki (Fandom, CC BY-SA)。</p>
</footer>

<style>
  .topbar {
    position: sticky;
    top: 0;
    z-index: 10;
    background: color-mix(in srgb, var(--c-bg) 88%, transparent);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--c-line);
    padding-top: env(safe-area-inset-top); /* iPhone ノッチ回避 */
  }
  .bar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px 18px;
    min-height: 60px;
    padding-top: 8px;
    padding-bottom: 8px;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    background: none;
    border: 0;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 20px;
    color: var(--c-ink);
    padding: 0;
  }
  .brand .mark { color: var(--c-accent); }
  .crumbs {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: var(--c-ink-soft);
  }
  .crumbs button {
    background: none;
    border: 0;
    color: var(--c-ink-soft);
    padding: 0;
  }
  .crumbs .here { color: var(--c-ink); font-weight: 600; }
  .crumbs .sep { opacity: 0.5; }
  main { padding: 28px 20px 60px; min-height: 60vh; }
  .foot {
    padding: 24px 20px 48px;
    color: var(--c-ink-soft);
    font-size: 12px;
    border-top: 1px solid var(--c-line);
  }
  .foot-reload {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 12px;
    margin-bottom: 14px;
  }
  .reload-btn {
    flex: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--c-surface);
    border: 1px solid var(--c-line);
    border-radius: 999px;
    padding: 8px 16px;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 14px;
    color: var(--c-ink);
    box-shadow: 0 1px 0 var(--c-shadow);
  }
  .reload-btn:hover:not(:disabled) { border-color: var(--c-accent); color: var(--c-accent); }
  .reload-btn:disabled { opacity: 0.6; }
  .reload-note { font-size: 11px; color: var(--c-ink-soft); line-height: 1.4; }
  .foot-cred { margin: 0; }
</style>
