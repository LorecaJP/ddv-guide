<script lang="ts">
  import type { Recipe } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { route } from '../lib/router'

  let all = $state<Recipe[]>([])
  let loading = $state(true)
  // 素材ページからの遷移時は ?ing=材料名 で初期検索
  let query = $state($route.params.ing ?? '')
  let starFilter = $state(0) // 0 = すべて
  let unlockedOnly = $state(false)
  let sortKey = $state<'name' | 'stars' | 'sell'>('stars')
  let sortDir = $state<'asc' | 'desc'>('desc')

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<Recipe>('recipes')
    loading = false
  }
  load()

  // 売値の数値化（"556+ スターコイン" → 556）
  function sellNum(r: Recipe): number {
    const m = r.sell_price_note.match(/(\d+)/)
    return m ? parseInt(m[1], 10) : 0
  }

  const unlockedCount = $derived(all.filter((r) => r.unlocked).length)

  const view = $derived(
    all
      .filter((r) => {
        if (unlockedOnly && !r.unlocked) return false
        if (starFilter && r.stars !== starFilter) return false
        if (query) {
          const q = query.toLowerCase()
          const hay = `${r.name_ja}${r.name_en}${r.ingredients.join('')}`.toLowerCase()
          if (!hay.includes(q)) return false
        }
        return true
      })
      .sort((a, b) => {
        let d = 0
        if (sortKey === 'name') d = a.name_en.localeCompare(b.name_en)
        else if (sortKey === 'stars') d = a.stars - b.stars
        else d = sellNum(a) - sellNum(b)
        return sortDir === 'asc' ? d : -d
      }),
  )

  function setSort(k: 'name' | 'stars' | 'sell') {
    if (sortKey === k) sortDir = sortDir === 'asc' ? 'desc' : 'asc'
    else {
      sortKey = k
      sortDir = k === 'name' ? 'asc' : 'desc'
    }
  }

  async function toggleUnlocked(r: Recipe) {
    r.unlocked = !r.unlocked
    await put('recipes', $state.snapshot(r))
    all = [...all]
  }

  const arrow = (k: string) => (sortKey === k ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '')
</script>

<div class="head">
  <h1>料理レシピ</h1>
  <p class="sub">{all.length} 件 ・ 解放済み {unlockedCount} 件（★は必要材料数）</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="料理名・材料で検索" bind:value={query} />
  <div class="stars-filter">
    <button class:on={starFilter === 0} onclick={() => (starFilter = 0)}>全★</button>
    {#each [1, 2, 3, 4, 5] as s}
      <button class:on={starFilter === s} onclick={() => (starFilter = s)}>{s}★</button>
    {/each}
  </div>
  <label class="toggle"><input type="checkbox" bind:checked={unlockedOnly} />解放済みのみ</label>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <p class="count muted">{view.length} 件表示</p>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th class="c-name sortable" onclick={() => setSort('name')}>料理名{arrow('name')}</th>
          <th class="c-star sortable" onclick={() => setSort('stars')}>★{arrow('stars')}</th>
          <th class="c-ing">材料</th>
          <th class="c-sell sortable" onclick={() => setSort('sell')}>売値{arrow('sell')}</th>
          <th class="c-own">解放</th>
        </tr>
      </thead>
      <tbody>
        {#each view as r (r.id)}
          <tr class:done={r.unlocked}>
            <td class="c-name">
              <span class="nm">{r.name_ja || r.name_en}</span>
              {#if r.name_ja}<span class="en">{r.name_en}</span>{/if}
            </td>
            <td class="c-star"><span class="stars">{'★'.repeat(r.stars)}</span></td>
            <td class="c-ing">
              {#each r.ingredients as ing}<span class="chip">{ing}</span>{/each}
            </td>
            <td class="c-sell">{r.sell_price_note.replace(' スターコイン', '')}</td>
            <td class="c-own">
              <button class="ownbtn" class:on={r.unlocked} onclick={() => toggleUnlocked(r)} title="解放トグル">
                {r.unlocked ? '✓' : '—'}
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
    {#if view.length === 0}<p class="muted pad">該当なし。</p>{/if}
  </div>
  <p class="note muted">
    ※ 日本語名（name_ja）は未突合（後で gamepedia と照合予定）。売値・材料・★は Fandom 由来の事実データ。
  </p>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 18px; font-size: 14px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; margin-bottom: 12px; }
  .search {
    flex: 1 1 220px; font-family: var(--font-body); padding: 9px 12px;
    border: 1px solid var(--c-line); border-radius: var(--radius-sm);
    background: var(--c-surface); color: var(--c-ink);
  }
  .stars-filter { display: inline-flex; gap: 4px; }
  .stars-filter button {
    border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink-soft);
    padding: 7px 10px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 600;
  }
  .stars-filter button.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
  .toggle { display: inline-flex; align-items: center; gap: 7px; font-size: 14px; color: var(--c-ink-soft); }
  .count { font-size: 13px; margin: 0 0 8px; }

  .table-wrap { overflow-x: auto; border: 1px solid var(--c-line); border-radius: var(--radius); }
  table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 640px; }
  thead th {
    position: sticky; top: 60px; z-index: 1;
    background: var(--c-surface-2); color: var(--c-ink-soft);
    text-align: left; font-weight: 700; padding: 11px 14px; white-space: nowrap;
    border-bottom: 1px solid var(--c-line);
  }
  th.sortable { cursor: pointer; user-select: none; }
  th.sortable:hover { color: var(--c-ink); }
  tbody td { padding: 10px 14px; border-bottom: 1px solid var(--c-line); vertical-align: top; }
  tbody tr:hover { background: color-mix(in srgb, var(--c-accent-soft) 30%, transparent); }
  tr.done { background: color-mix(in srgb, var(--c-accent-soft) 20%, transparent); }

  .c-name .nm { font-family: var(--font-display); font-weight: 600; display: block; }
  .c-name .en { font-size: 11px; color: var(--c-ink-soft); }
  .c-star { white-space: nowrap; }
  .stars { color: var(--c-accent); letter-spacing: 1px; }
  .c-ing { min-width: 220px; }
  .chip {
    display: inline-block; margin: 2px 4px 2px 0;
    background: var(--c-surface-2); color: var(--c-ink);
    font-size: 12px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--c-line);
  }
  .c-sell { white-space: nowrap; font-variant-numeric: tabular-nums; font-weight: 600; }
  .ownbtn {
    width: 30px; height: 30px; border-radius: 8px;
    border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink-soft);
  }
  .ownbtn.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
  .muted { color: var(--c-ink-soft); }
  .pad { padding: 16px; }
  .note { font-size: 12px; margin-top: 12px; }
</style>
