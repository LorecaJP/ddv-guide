<script lang="ts">
  import { seedAll } from '../lib/db/seed'
  import { getAll } from '../lib/db/idb'
  import { CATEGORIES } from '../lib/schema'

  let { storeKey }: { storeKey: string } = $props()
  const meta = $derived(CATEGORIES.find((c) => c.key === storeKey))
  // tips: title/body_md, faq: question/answer_md
  const titleKey = $derived(storeKey === 'faq' ? 'question' : 'title')
  const bodyKey = $derived(storeKey === 'faq' ? 'answer_md' : 'body_md')

  let rows = $state<Record<string, any>[]>([])
  let loading = $state(true)
  let openId = $state<string | null>(null)

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
  <p class="sub">{rows.length} 件 ・ 記事型（タイトルをタップで本文展開）</p>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else if rows.length === 0}
  <div class="empty">
    <p>まだ記事がありません。</p>
    <p class="muted">
      {storeKey === 'faq' ? 'よくある疑問と自分用の答え' : '見つけた小技・裏技'}をここに書き溜めていく想定です（ユーザー入力用の器）。
    </p>
  </div>
{:else}
  <ul class="list">
    {#each rows as r (r.id)}
      <li class="item">
        <button class="q" onclick={() => (openId = openId === r.id ? null : r.id)}>
          <span>{r[titleKey]}</span>
          <span class="ar">{openId === r.id ? '−' : '+'}</span>
        </button>
        {#if openId === r.id}
          <div class="body">{r[bodyKey]}</div>
        {/if}
      </li>
    {/each}
  </ul>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 18px; font-size: 14px; }
  .empty { padding: 40px; text-align: center; border: 1px dashed var(--c-line); border-radius: var(--radius); }
  .empty p { margin: 4px 0; }
  .list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .item { border: 1px solid var(--c-line); border-radius: var(--radius); background: var(--c-surface); overflow: hidden; }
  .q { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 12px; background: none; border: 0; padding: 14px 16px; text-align: left; font-family: var(--font-display); font-weight: 600; font-size: 16px; color: var(--c-ink); }
  .ar { color: var(--c-accent); font-size: 20px; }
  .body { padding: 0 16px 16px; color: var(--c-ink-soft); white-space: pre-wrap; }
  .muted { color: var(--c-ink-soft); }
</style>
