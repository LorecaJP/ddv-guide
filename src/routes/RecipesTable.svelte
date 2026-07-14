<script lang="ts">
  import type { Recipe, Material } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { route, setParams, asset } from '../lib/router'

  const P = $route.params
  let all = $state<Recipe[]>([])
  let loading = $state(true)
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))
  // 材料アイコン検索用（食材の name_en / name_ja → icon_path）
  let ingIcon = $state<Record<string, string>>({})
  // 素材ページからの遷移時は ?ing=材料名 で初期検索
  let query = $state(P.q ?? P.ing ?? '')
  let starFilter = $state(Number(P.star) || 0) // 0 = すべて
  let statusFilter = $state(P.status ?? 'all') // 'all' | 'unlocked' | 'locked'
  let categoryFilter = $state(P.cat ?? 'all') // 'all' | 前菜/主菜/デザート
  let realmFilter = $state(P.realm ?? 'all') // 'all' | コンテンツ名
  let selected = $state<Recipe | null>(null)
  const REALMS = ['バレー', '永遠の島', '物語の谷', '願い咲く牧場', 'ハニーグローの森']

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') selected = null
  }

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
    // 食材アイコンの逆引きを構築
    const mats = await getAll<Material>('materials')
    const map: Record<string, string> = {}
    for (const m of mats) {
      if (!m.icon_path) continue
      if (m.name_en) map[m.name_en.toLowerCase()] = m.icon_path
      if (m.name_ja) map[m.name_ja] = m.icon_path
    }
    ingIcon = map
    loading = false
  }
  load()

  const iconFor = (en: string, ja: string) =>
    ingIcon[(en || '').toLowerCase()] || ingIcon[ja] || ''

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
    if (selected?.id === r.id) selected = r
  }
  const sell = (r: Recipe) => r.sell_price_note.replace(' スターコイン', '')
  // メモ「入手: X / エナジー Y+」から エナジー値を取り出す（入手はクリーンな realm を使う）
  const energyOf = (r: Recipe) => {
    const m = (r.memo || '').match(/エナジー\s*([0-9０-９]+\+?)/)
    return m ? m[1] : ''
  }
  // 標準パターン以外のメモだけ表示（ハニーグロー注記など）
  const extraMemo = (r: Recipe) => {
    const mm = (r.memo || '').trim()
    return /^入手:.*エナジー/.test(mm) ? '' : mm
  }
  // モーダル内の材料リスト（日本語名＋英語名＋アイコン）
  const ingList = (r: Recipe) =>
    r.ingredients_ja.map((ja, i) => {
      const en = r.ingredients[i] || ''
      return { ja: ja || en, en, icon: iconFor(en, ja) }
    })
</script>

<svelte:window onkeydown={onKey} />

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
            <button class="main" onclick={() => (selected = r)}>
              <span class="rthumb">
                {#if r.icon_path && !broken.has(r.id)}
                  <img src={asset(r.icon_path)} alt="" loading="lazy" onerror={() => markBroken(r.id)} />
                {:else}<span class="ph">🍽️</span>{/if}
              </span>
              <span class="txt">
                <span class="nm">{r.name_ja || r.name_en}</span>
                {#if r.name_ja}<span class="en">{r.name_en}</span>{/if}
              </span>
              <span class="stars">{'★'.repeat(r.stars)}</span>
              {#if r.unlocked}<span class="tick">✓</span>{/if}
            </button>
          </li>
        {/each}
      </ul>
    </section>
  {/each}
  {#if groups.length === 0}<p class="muted">該当なし。</p>{/if}
{/if}

{#if selected}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="backdrop" onclick={() => (selected = null)}>
    <div class="sheet" role="dialog" aria-modal="true" aria-label={selected.name_ja || selected.name_en} tabindex="-1" onclick={(e) => e.stopPropagation()}>
      <button class="close" onclick={() => (selected = null)} aria-label="閉じる">✕</button>
      <div class="sheet-top">
        <div class="big-thumb">
          {#if selected.icon_path && !broken.has(selected.id)}
            <img src={asset(selected.icon_path)} alt="" onerror={() => selected && markBroken(selected.id)} />
          {:else}<span class="ph-big">🍽️</span>{/if}
        </div>
        <div>
          <h2>{selected.name_ja || selected.name_en}</h2>
          {#if selected.name_ja}<p class="en">{selected.name_en}</p>{/if}
          <p class="chips">
            <span class="stars-lg">{'★'.repeat(selected.stars)}</span>
            {#if selected.category}<span class="chip">{selected.category}</span>{/if}
            {#if selected.realm}<span class="chip realm">{selected.realm}</span>{/if}
          </p>
        </div>
      </div>
      <div class="ing-block">
        <span class="lbl">材料（{selected.ingredients_ja.length}）</span>
        <div class="ings">
          {#each ingList(selected) as ing}
            <div class="ing">
              <span class="ing-thumb">
                {#if ing.icon}<img src={asset(ing.icon)} alt="" loading="lazy" />{:else}<span class="ing-ph">🧺</span>{/if}
              </span>
              <span class="ing-nm">{ing.ja}</span>
            </div>
          {/each}
        </div>
      </div>
      <dl class="facts">
        <dt>入手</dt><dd>{selected.realm || '—'}</dd>
        {#if energyOf(selected)}<dt>エナジー</dt><dd>{energyOf(selected)}</dd>{/if}
        <dt>売値</dt><dd>{sell(selected)}</dd>
        {#if extraMemo(selected)}<dt>メモ</dt><dd>{extraMemo(selected)}</dd>{/if}
        <dt>解放</dt>
        <dd>
          <button class="own-tgl" class:on={selected.unlocked} onclick={() => selected && toggleUnlocked(selected)}>
            {selected.unlocked ? '✓ 解放済み' : '未解放'}
          </button>
        </dd>
      </dl>
    </div>
  </div>
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
  .main { width: 100%; background: none; border: 0; text-align: left; padding: 10px 4px; display: flex; align-items: center; gap: 10px; cursor: pointer; }
  .rthumb { flex: none; width: 40px; height: 40px; display: grid; place-items: center; background: var(--c-surface-2); border-radius: 8px; overflow: hidden; }
  .rthumb img { width: 100%; height: 100%; object-fit: contain; }
  .rthumb .ph { font-size: 20px; opacity: 0.5; }
  .txt { flex: 1 1 auto; display: flex; flex-direction: column; min-width: 0; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 15px; color: var(--c-ink); line-height: 1.25; }
  .en { font-size: 11px; color: var(--c-ink-soft); }
  .stars { flex: none; color: var(--c-accent); letter-spacing: 1px; font-size: 13px; white-space: nowrap; }
  .tick { flex: none; width: 22px; height: 22px; border-radius: 50%; background: var(--c-accent); color: #fff; font-size: 12px; display: grid; place-items: center; }
  .muted { color: var(--c-ink-soft); }

  /* モーダル */
  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(20,16,10,0.45); display: grid; place-items: center; padding: 20px; }
  .sheet { position: relative; width: min(460px, 94vw); max-height: 88vh; overflow-y: auto; background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 22px; box-shadow: 0 24px 60px rgba(0,0,0,0.3); }
  .close { position: absolute; top: 12px; right: 12px; background: var(--c-surface-2); border: 0; border-radius: 8px; width: 30px; height: 30px; color: var(--c-ink-soft); }
  .sheet-top { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
  .big-thumb { width: 92px; height: 92px; flex: none; background: var(--c-surface-2); border-radius: var(--radius-sm); display: grid; place-items: center; overflow: hidden; }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .ph-big { font-size: 34px; opacity: 0.5; }
  .sheet-top h2 { font-size: 20px; padding-right: 34px; }
  .en { color: var(--c-ink-soft); margin: 3px 0 8px; font-size: 13px; }
  .chips { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 0; }
  .stars-lg { color: var(--c-accent); letter-spacing: 1px; font-size: 14px; }
  .chip { display: inline-block; background: var(--c-accent-soft); color: var(--c-accent-ink); font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px; }
  .chip.realm { background: var(--c-surface-2); color: var(--c-ink-soft); }

  .ing-block { margin: 6px 0 14px; }
  .lbl { display: inline-block; font-size: 12px; font-weight: 700; color: var(--c-ink-soft); margin-bottom: 8px; }
  .ings { display: grid; grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap: 8px; }
  .ing { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px; background: var(--c-surface-2); border-radius: var(--radius-sm); }
  .ing-thumb { width: 40px; height: 40px; display: grid; place-items: center; }
  .ing-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .ing-ph { font-size: 20px; opacity: 0.5; }
  .ing-nm { font-size: 11px; text-align: center; line-height: 1.2; color: var(--c-ink); }

  .facts { display: grid; grid-template-columns: 72px 1fr; gap: 10px 12px; margin: 0; font-size: 14px; align-items: center; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .own-tgl { padding: 8px 16px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .own-tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
