<script lang="ts">
  import type { Material } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { navigate } from '../lib/router'

  let all = $state<Material[]>([])
  let loading = $state(true)
  let query = $state('')
  let cat = $state('all')
  let sortKey = $state<'name' | 'used'>('used')
  let sortDir = $state<'asc' | 'desc'>('desc')

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<Material>('materials')
    loading = false
  }
  load()

  const cats = $derived([...new Set(all.map((m) => m.category).filter(Boolean))].sort())

  const view = $derived(
    all
      .filter((m) => {
        if (cat !== 'all' && m.category !== cat) return false
        if (query) {
          const q = query.toLowerCase()
          if (!`${m.name_ja}${m.name_en}`.toLowerCase().includes(q)) return false
        }
        return true
      })
      .sort((a, b) => {
        const d =
          sortKey === 'name'
            ? a.name_en.localeCompare(b.name_en)
            : a.used_in_recipes.length - b.used_in_recipes.length
        return sortDir === 'asc' ? d : -d
      }),
  )

  function setSort(k: 'name' | 'used') {
    if (sortKey === k) sortDir = sortDir === 'asc' ? 'desc' : 'asc'
    else {
      sortKey = k
      sortDir = k === 'name' ? 'asc' : 'desc'
    }
  }

  async function setStock(m: Material, v: number) {
    m.stock_count = Math.max(0, v | 0)
    await put('materials', $state.snapshot(m))
    all = [...all]
  }

  const arrow = (k: string) => (sortKey === k ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '')
</script>

<div class="head">
  <h1>素材</h1>
  <p class="sub">{all.length} 種 ・ レシピの材料と ID 連携（「使用レシピ」でレシピ一覧へ）</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="素材名で検索（日本語 / 英語）" bind:value={query} />
  <select bind:value={cat}>
    <option value="all">すべての種別</option>
    {#each cats as c}<option value={c}>{c}</option>{/each}
  </select>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <p class="count muted">{view.length} 種表示</p>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th class="sortable" onclick={() => setSort('name')}>素材名{arrow('name')}</th>
          <th>種別</th>
          <th>入手方法</th>
          <th class="sortable num" onclick={() => setSort('used')}>使用レシピ{arrow('used')}</th>
          <th class="num">在庫</th>
        </tr>
      </thead>
      <tbody>
        {#each view as m (m.id)}
          <tr>
            <td>
              <span class="nm">{m.name_ja || m.name_en}</span>
              {#if m.name_ja}<span class="en">{m.name_en}</span>{/if}
            </td>
            <td class="cat">{m.category || '—'}</td>
            <td class="obtain">{m.obtain_method || '—'}</td>
            <td class="num">
              {#if m.used_in_recipes.length}
                <button class="link" onclick={() => navigate('recipes', { ing: m.name_en })}>
                  {m.used_in_recipes.length} 件 →
                </button>
              {:else}
                <span class="muted">0</span>
              {/if}
            </td>
            <td class="num">
              <div class="stepper">
                <button onclick={() => setStock(m, m.stock_count - 1)} aria-label="減">−</button>
                <span class="val">{m.stock_count}</span>
                <button onclick={() => setStock(m, m.stock_count + 1)} aria-label="増">＋</button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
    {#if view.length === 0}<p class="muted pad">該当なし。</p>{/if}
  </div>
  <p class="note muted">
    ※ 一部の素材は種別・入手方法・日本語名が未取得（Fandom infobox の記載差）。名前・使用レシピは事実データ。
  </p>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 18px; font-size: 14px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
  .search { flex: 1 1 220px; font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  select { padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .count { font-size: 13px; margin: 0 0 8px; }

  .table-wrap { overflow-x: auto; border: 1px solid var(--c-line); border-radius: var(--radius); }
  table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 620px; }
  thead th { background: var(--c-surface-2); color: var(--c-ink-soft); text-align: left; font-weight: 700; padding: 11px 14px; white-space: nowrap; border-bottom: 1px solid var(--c-line); }
  th.sortable { cursor: pointer; user-select: none; }
  th.sortable:hover { color: var(--c-ink); }
  th.num, td.num { text-align: right; }
  tbody td { padding: 10px 14px; border-bottom: 1px solid var(--c-line); }
  tbody tr:hover { background: color-mix(in srgb, var(--c-accent-soft) 30%, transparent); }
  .nm { font-family: var(--font-display); font-weight: 600; display: block; }
  .en { font-size: 11px; color: var(--c-ink-soft); }
  .cat { white-space: nowrap; color: var(--c-ink-soft); }
  .obtain { color: var(--c-ink-soft); font-size: 13px; }
  .link { background: none; border: 0; color: var(--c-accent-ink); font-weight: 700; padding: 0; white-space: nowrap; }
  .link:hover { text-decoration: underline; }
  .stepper { display: inline-flex; align-items: center; gap: 6px; }
  .stepper button { width: 26px; height: 26px; border-radius: 7px; border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink); font-weight: 700; }
  .stepper .val { min-width: 22px; text-align: center; font-variant-numeric: tabular-nums; }
  .muted { color: var(--c-ink-soft); }
  .pad { padding: 16px; }
  .note { font-size: 12px; margin-top: 12px; }
</style>
