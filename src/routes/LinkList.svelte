<script lang="ts">
  import { seedAll } from '../lib/db/seed'
  import { getAll } from '../lib/db/idb'
  import { CATEGORIES } from '../lib/schema'

  let { storeKey }: { storeKey: string } = $props()
  const meta = $derived(CATEGORIES.find((c) => c.key === storeKey))
  const titleKey = $derived(storeKey === 'faq' ? 'question' : 'title')

  let rows = $state<Record<string, any>[]>([])
  let loading = $state(true)

  async function load() {
    loading = true
    await seedAll()
    rows = await getAll<Record<string, any>>(storeKey)
    loading = false
  }
  $effect(() => {
    storeKey
    load()
  })
</script>

<div class="head">
  <h1>{meta?.emoji} {meta?.name_ja}</h1>
  <p class="sub">
    参照サイトの該当ページへのリンク集です（本文はリンク先で読めます）。
  </p>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else if rows.length === 0}
  <div class="empty"><p>リンクがありません。</p></div>
{:else}
  <ul class="list">
    {#each rows as r (r.id)}
      <li class="item">
        <a class="link" href={r.link || r.source_url} target="_blank" rel="noopener noreferrer">
          <div class="txt">
            <span class="ttl">{r[titleKey]}</span>
            <span class="src">{r.source || '参照元'} ↗</span>
          </div>
          <span class="go">開く</span>
        </a>
      </li>
    {/each}
  </ul>
  <p class="note muted">
    ※ これらの記事の文章は転載せず、参照元ページへリンクしています（著作権への配慮）。リンクをタップすると新しいタブで開きます。
  </p>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 18px; font-size: 14px; }
  .empty { padding: 40px; text-align: center; border: 1px dashed var(--c-line); border-radius: var(--radius); }
  .list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
  .item { border: 1px solid var(--c-line); border-radius: var(--radius); background: var(--c-surface); box-shadow: 0 1px 0 var(--c-shadow); transition: border-color .12s, transform .12s; }
  .item:hover { border-color: var(--c-accent); transform: translateY(-1px); }
  .link { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 16px 18px; }
  .txt { display: flex; flex-direction: column; gap: 4px; }
  .ttl { font-family: var(--font-display); font-weight: 600; font-size: 16px; color: var(--c-ink); }
  .src { font-size: 12px; color: var(--c-ink-soft); }
  .go { flex: none; background: var(--c-accent-soft); color: var(--c-accent-ink); font-weight: 700; font-size: 13px; padding: 6px 14px; border-radius: 999px; }
  .note { font-size: 12px; margin-top: 14px; }
  .muted { color: var(--c-ink-soft); }
</style>
