<script lang="ts">
  import { route, navigate } from './lib/router'
  import { CATEGORIES } from './lib/schema'
  import Hub from './routes/Hub.svelte'
  import CharactersZukan from './routes/CharactersZukan.svelte'
  import RecipesTable from './routes/RecipesTable.svelte'
  import MaterialsTable from './routes/MaterialsTable.svelte'
  import CompanionsZukan from './routes/CompanionsZukan.svelte'
  import DataTable from './routes/DataTable.svelte'
  import ArticleList from './routes/ArticleList.svelte'
  import LinkList from './routes/LinkList.svelte'
  import Dashboard from './routes/Dashboard.svelte'

  const LINK_CATEGORIES = ['tips', 'faq', 'bugs']
  import CategoryPlaceholder from './routes/CategoryPlaceholder.svelte'

  const current = $derived($route.category)
  const meta = $derived(CATEGORIES.find((c) => c.key === current) ?? null)
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
  {:else if current === 'companions'}
    <CompanionsZukan />
  {:else if LINK_CATEGORIES.includes(current)}
    <LinkList storeKey={current} />
  {:else if meta?.display === 'dashboard'}
    <Dashboard />
  {:else if meta?.display === 'article'}
    <ArticleList storeKey={current} />
  {:else if meta?.display === 'table'}
    <DataTable storeKey={current} />
  {:else if meta}
    <CategoryPlaceholder {meta} />
  {:else}
    <CategoryPlaceholder meta={null} />
  {/if}
</main>

<footer class="foot container">
  個人利用・非公開。画像・データ出典: Disney Dreamlight Valley Wiki (Fandom)。画像は個人参照用。
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
</style>
