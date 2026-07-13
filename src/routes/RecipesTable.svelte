<script lang="ts">
  import type { Recipe } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { route, setParams } from '../lib/router'

  const P = $route.params
  let all = $state<Recipe[]>([])
  let loading = $state(true)
  // 素材ページからの遷移時は ?ing=材料名 で初期検索
  let query = $state(P.q ?? P.ing ?? '')
  let starFilter = $state(Number(P.star) || 0) // 0 = すべて
  let statusFilter = $state(P.status ?? 'all') // 'all' | 'unlocked' | 'locked'
  let categoryFilter = $state(P.cat ?? 'all') // 'all' | 前菜/主菜/デザート
  let realmFilter = $state(P.realm ?? 'all') // 'all' | コンテンツ名
  let expanded = $state<Set<string>>(new Set())
  const REALMS = ['バレー', '永遠の島', '物語の谷', '願い咲く牧場', 'ハニーグローの森']

  // 絞り込み条件を URL に保持（戻る/リロード/共有で復元）
  $effect(() => {
    setParams('recipes', {
      q: query,
      star: starFilter ? String(starFilter) : '',
      status: statusFilter,
      cat: categoryFilter,
      realm: realmFilter,
    })
  })

  const CAT_ORDER = ['前菜', '主菜', 'デザート']

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<Recipe>('recipes')
    loading = false
  }
  load()

  const unlockedCount = $derived(all.filter((r) => r.unlocked).length)
  const key = (r: Recipe) => r.name_ja || r.name_en

  const groups = $derived(
    (() => {
      const filtered = all.filter((r) => {
        if (statusFilter === 'unlocked' && !r.unlocked) return false
        if (statusFilter === 'locked' && r.unlocked) return false
        if (categoryFilter !== 'all' && r.category !== categoryFilter) return false
        if (realmFilter === '__none__') {
          if (r.realm) return false
        } else if (realmFilter !== 'all' && r.realm !== realmFilter) return false
        if (starFilter && r.stars !== starFilter) return false
        if (query) {
          const q = query.toLowerCase()
          const hay = `${r.name_ja}${r.name_en}${r.ingredients.join('')}${r.ingredients_ja.join('')}`.toLowerCase()
          if (!hay.includes(q)) return false
        }
        return true
      })
      const map = new Map<string, Recipe[]>()
      for (const r of filtered) {
        const c = r.category || 'その他'
        if (!map.has(c)) map.set(c, [])
        map.get(c)!.push(r)
      }
      const out = [...map.entries()].map(([category, items]) => {
        items.sort((a, b) => {
          // 日本語名ありを五十音で先に、英語名のみは後ろに
          const aj = !!a.name_ja
          const bj = !!b.name_ja
          if (aj !== bj) return aj ? -1 : 1
          return key(a).localeCompare(key(b), 'ja')
        })
        return { category, unlocked: items.filter((i) => i.unlocked).length, items }
      })
      out.sort((a, b) => {
        const ia = CAT_ORDER.indexOf(a.category)
        const ib = CAT_ORDER.indexOf(b.category)
        return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
      })
      return out
    })(),
  )

  async function toggleUnlocked(r: Recipe) {
    r.unlocked = !r.unlocked
    await put('recipes', $state.snapshot(r))
    all = [...all]
  }
  function toggleExpand(id: string) {
    const s = new Set(expanded)
    s.has(id) ? s.delete(id) : s.add(id)
    expanded = s
  }
  const sell = (r: Recipe) => r.sell_price_note.replace(' スターコイン', '')
</script>

<div class="head">
  <h1>料理レシピ</h1>
  <p class="sub">{all.length} 件 ・ 解放済み {unlockedCount} 件（★は必要材料数）。料理名タップで材料・売値</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="料理名・材料で検索" bind:value={query} />
  <div class="row2">
    <div class="stars-filter">
      <button class:on={starFilter === 0} onclick={() => (starFilter = 0)}>全★</button>
      {#each [1, 2, 3, 4, 5] as s}
        <button class:on={starFilter === s} onclick={() => (starFilter = s)}>{s}★</button>
      {/each}
    </div>
    <select bind:value={statusFilter} aria-label="解放状態で絞り込み">
      <option value="all">解放：すべて</option>
      <option value="unlocked">解放済み</option>
      <option value="locked">未解放</option>
    </select>
    <select bind:value={categoryFilter} aria-label="分類で絞り込み">
      <option value="all">分類：すべて</option>
      <option value="前菜">前菜</option>
      <option value="主菜">主菜</option>
      <option value="デザート">デザート</option>
    </select>
    <select bind:value={realmFilter} aria-label="コンテンツで絞り込み">
      <option value="all">コンテンツ：すべて</option>
      {#each REALMS as rlm}<option value={rlm}>{rlm}</option>{/each}
      <option value="__none__">（コンテンツ未設定）</option>
    </select>
  </div>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  {#each groups as g (g.category)}
    <section class="cat">
      <div class="cat-head"><h2>{g.category}<span class="cnt">{g.unlocked}/{g.items.length}</span></h2></div>
      <ul class="list">
        {#each g.items as r (r.id)}
          <li class="item" class:done={r.unlocked}>
            <div class="line">
              <button class="main" onclick={() => toggleExpand(r.id)}>
                <span class="nm">{r.name_ja || r.name_en}</span>
                {#if r.name_ja}<span class="en">{r.name_en}</span>{/if}
              </button>
              <span class="stars">{'★'.repeat(r.stars)}</span>
              <button class="own" class:on={r.unlocked} onclick={() => toggleUnlocked(r)} title="解放トグル">
                {r.unlocked ? '✓' : '—'}
              </button>
            </div>
            {#if expanded.has(r.id)}
              <div class="detail">
                <div class="d-row"><span class="lbl">材料</span>
                  <span class="chips">{#each r.ingredients_ja as ing}<span class="chip">{ing}</span>{/each}</span>
                </div>
                <div class="d-row"><span class="lbl">売値</span><span class="sell">{sell(r)}</span></div>
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    </section>
  {/each}
  {#if groups.length === 0}<p class="muted">該当なし。</p>{/if}
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 16px; font-size: 14px; }
  .controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
  .search { font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .row2 { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; }
  .stars-filter { display: inline-flex; gap: 4px; }
  .stars-filter button { border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink-soft); padding: 7px 10px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 600; }
  .stars-filter button.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
  .row2 select { font-family: var(--font-body); padding: 8px 10px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }

  .cat { margin-bottom: 22px; }
  .cat-head { border-bottom: 2px solid var(--c-accent-soft); padding-bottom: 8px; margin-bottom: 8px; }
  .cat-head h2 { font-size: 20px; display: flex; align-items: baseline; gap: 10px; }
  .cnt { font-size: 13px; color: var(--c-ink-soft); font-weight: 400; }

  .list { list-style: none; padding: 0; margin: 0; }
  .item { border-bottom: 1px solid var(--c-line); }
  .item.done { background: color-mix(in srgb, var(--c-accent-soft) 22%, transparent); }
  .line { display: flex; align-items: center; gap: 10px; padding: 10px 4px; }
  .main { flex: 1 1 auto; min-width: 0; background: none; border: 0; text-align: left; padding: 4px 2px; display: flex; flex-direction: column; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 15px; color: var(--c-ink); line-height: 1.25; }
  .en { font-size: 11px; color: var(--c-ink-soft); }
  .stars { flex: none; color: var(--c-accent); letter-spacing: 1px; font-size: 13px; white-space: nowrap; }
  .own { flex: none; width: 34px; height: 32px; border-radius: 8px; border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink-soft); font-weight: 700; }
  .own.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }

  .detail { padding: 4px 6px 12px; display: flex; flex-direction: column; gap: 8px; }
  .d-row { display: flex; gap: 10px; align-items: baseline; }
  .lbl { flex: none; font-size: 11px; font-weight: 700; color: var(--c-accent-ink); background: var(--c-accent-soft); padding: 2px 8px; border-radius: 999px; }
  .chips { display: flex; flex-wrap: wrap; gap: 4px; }
  .chip { background: var(--c-surface-2); border: 1px solid var(--c-line); font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .sell { font-variant-numeric: tabular-nums; font-weight: 600; }
  .muted { color: var(--c-ink-soft); }
</style>
