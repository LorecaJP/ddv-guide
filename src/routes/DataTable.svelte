<script lang="ts">
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { TABLE_CONFIG } from '../lib/tableConfig'
  import { CATEGORIES } from '../lib/schema'

  let { storeKey }: { storeKey: string } = $props()

  const cfg = $derived(TABLE_CONFIG[storeKey])
  const meta = $derived(CATEGORIES.find((c) => c.key === storeKey))

  let rows = $state<Record<string, any>[]>([])
  let loading = $state(true)
  let query = $state('')
  let sortKey = $state('')
  let sortDir = $state<'asc' | 'desc'>('desc')

  async function load() {
    loading = true
    await seedAll()
    rows = await getAll<Record<string, any>>(storeKey)
    if (cfg.defaultSort) {
      sortKey = cfg.defaultSort.key
      sortDir = cfg.defaultSort.dir
    }
    loading = false
  }
  $effect(() => {
    storeKey // re-run when storeKey changes
    load()
  })

  function cellSortVal(row: Record<string, any>, key: string): number | string {
    const v = row[key]
    if (Array.isArray(v)) return v.length
    if (typeof v === 'number') return v
    if (typeof v === 'boolean') return v ? 1 : 0
    return (v ?? '').toString()
  }

  const view = $derived(
    (() => {
      let r = rows.filter((row) => {
        if (!query) return true
        const q = query.toLowerCase()
        return cfg.searchKeys.some((k) => (row[k] ?? '').toString().toLowerCase().includes(q))
      })
      if (sortKey) {
        r = [...r].sort((a, b) => {
          const av = cellSortVal(a, sortKey)
          const bv = cellSortVal(b, sortKey)
          let d = 0
          if (typeof av === 'number' && typeof bv === 'number') d = av - bv
          else d = av.toString().localeCompare(bv.toString(), 'ja')
          return sortDir === 'asc' ? d : -d
        })
      }
      return r
    })(),
  )

  function setSort(key: string) {
    if (sortKey === key) sortDir = sortDir === 'asc' ? 'desc' : 'asc'
    else {
      sortKey = key
      sortDir = 'desc'
    }
  }

  async function persist(row: Record<string, any>) {
    await put(storeKey, $state.snapshot(row))
    rows = [...rows]
  }
  function toggle(row: Record<string, any>, key: string) {
    row[key] = !row[key]
    persist(row)
  }
  function step(row: Record<string, any>, key: string, delta: number, min = 0, max = Infinity) {
    row[key] = Math.max(min, Math.min(max, (row[key] | 0) + delta))
    persist(row)
  }

  const arrow = (k: string) => (sortKey === k ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '')
</script>

<div class="head">
  <h1>{meta?.emoji} {meta?.name_ja}</h1>
  <p class="sub">{rows.length} 件{cfg.note ? ` ・ ${cfg.note}` : ''}</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="検索" bind:value={query} />
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else if rows.length === 0}
  <div class="empty">
    <p>まだデータがありません。</p>
    <p class="muted">このカテゴリはユーザーが追記していく想定です（現状は器のみ）。</p>
  </div>
{:else}
  <p class="count muted">{view.length} 件表示</p>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          {#each cfg.columns as col}
            <th
              class:sortable={col.sortable}
              class:num={col.align === 'right'}
              onclick={() => col.sortable && setSort(col.key === 'name' ? col.primaryKey ?? col.key : col.key)}
            >
              {col.label}{col.sortable ? arrow(col.key === 'name' ? col.primaryKey ?? col.key : col.key) : ''}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each view as row (row.id)}
          <tr>
            {#each cfg.columns as col}
              <td class:num={col.align === 'right'}>
                {#if col.kind === 'title'}
                  <span class="nm">{row[col.primaryKey ?? 'name_ja'] || row[col.subKey ?? 'name_en']}</span>
                  {#if row[col.primaryKey ?? 'name_ja'] && row[col.subKey ?? '']}
                    <span class="en">{row[col.subKey ?? '']}</span>
                  {/if}
                {:else if col.kind === 'chips'}
                  {#each (row[col.key] ?? []) as c}<span class="chip">{c}</span>{/each}
                {:else if col.kind === 'stars'}
                  <span class="stars">{'★'.repeat(row[col.key] ?? 0)}</span>
                {:else if col.kind === 'toggle'}
                  <button class="tgl" class:on={row[col.key]} onclick={() => toggle(row, col.key)}>
                    {row[col.key] ? col.onLabel ?? '✓' : col.offLabel ?? '—'}
                  </button>
                {:else if col.kind === 'stepper'}
                  <div class="stepper">
                    <button onclick={() => step(row, col.key, -1, col.min, col.max)}>−</button>
                    <span class="val">{row[col.key] ?? 0}</span>
                    <button onclick={() => step(row, col.key, 1, col.min, col.max)}>＋</button>
                  </div>
                {:else if col.kind === 'link'}
                  {#if row[col.key]}
                    <a class="ext" href={row[col.key]} target="_blank" rel="noopener noreferrer">
                      {col.linkLabel ?? '開く'} ↗
                    </a>
                  {:else}—{/if}
                {:else if col.kind === 'number'}
                  {Array.isArray(row[col.key]) ? row[col.key].length : (row[col.key] ?? '—')}
                {:else}
                  {row[col.key] || '—'}
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
    {#if view.length === 0}<p class="muted pad">該当なし。</p>{/if}
  </div>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 16px; font-size: 14px; }
  .controls { margin-bottom: 12px; }
  .search { width: min(360px, 100%); font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .count { font-size: 13px; margin: 0 0 8px; }
  .empty { padding: 40px; text-align: center; border: 1px dashed var(--c-line); border-radius: var(--radius); }
  .empty p { margin: 4px 0; }
  .table-wrap { overflow-x: auto; border: 1px solid var(--c-line); border-radius: var(--radius); }
  table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 560px; }
  thead th { background: var(--c-surface-2); color: var(--c-ink-soft); text-align: left; font-weight: 700; padding: 11px 14px; white-space: nowrap; border-bottom: 1px solid var(--c-line); }
  th.sortable { cursor: pointer; user-select: none; }
  th.sortable:hover { color: var(--c-ink); }
  th.num, td.num { text-align: right; }
  tbody td { padding: 10px 14px; border-bottom: 1px solid var(--c-line); vertical-align: top; }
  tbody tr:hover { background: color-mix(in srgb, var(--c-accent-soft) 30%, transparent); }
  .nm { font-family: var(--font-display); font-weight: 600; display: block; }
  .en { font-size: 11px; color: var(--c-ink-soft); }
  .chip { display: inline-block; margin: 2px 4px 2px 0; background: var(--c-surface-2); border: 1px solid var(--c-line); font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .stars { color: var(--c-accent); letter-spacing: 1px; }
  .ext { color: var(--c-accent-ink); font-weight: 700; white-space: nowrap; }
  .ext:hover { text-decoration: underline; }
  .tgl { width: 32px; height: 30px; border-radius: 8px; border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink-soft); font-weight: 700; }
  .tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
  .stepper { display: inline-flex; align-items: center; gap: 6px; }
  .stepper button { width: 26px; height: 26px; border-radius: 7px; border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink); font-weight: 700; }
  .stepper .val { min-width: 22px; text-align: center; font-variant-numeric: tabular-nums; }
  .muted { color: var(--c-ink-soft); }
  .pad { padding: 16px; }
</style>
