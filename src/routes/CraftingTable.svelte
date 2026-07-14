<script lang="ts">
  import type { CraftMaterial } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { route, setParams, asset } from '../lib/router'

  const P = $route.params
  let all = $state<CraftMaterial[]>([])
  let loading = $state(true)
  let query = $state(P.q ?? '')
  let statusFilter = $state(P.status ?? 'all') // 'all' | 'unlocked' | 'locked'
  let catFilter = $state(P.cat ?? 'all')
  let realmFilter = $state(P.realm ?? 'all')
  let expanded = $state<Set<string>>(new Set())
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))

  $effect(() => {
    setParams('crafting', { q: query, status: statusFilter, cat: catFilter, realm: realmFilter })
  })

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<CraftMaterial>('crafting')
    loading = false
  }
  load()

  const CAT_ORDER = ['宝石', '鉱石', '精錬', '木材', '石材', '繊維', 'その他']
  const REALM_ORDER = ['バレー', '永遠の島', '物語の谷', '願い咲く牧場', 'ハニーグローの森']

  const cats = $derived((() => {
    const present = new Set(all.map((m) => m.category).filter(Boolean))
    const ordered = CAT_ORDER.filter((c) => present.has(c))
    const extra = [...present].filter((c) => !CAT_ORDER.includes(c)).sort()
    return [...ordered, ...extra]
  })())
  const realms = $derived((() => {
    const present = new Set(all.flatMap((m) => m.realms ?? []))
    return REALM_ORDER.filter((r) => present.has(r))
  })())
  const unlockedCount = $derived(all.filter((m) => m.unlocked).length)

  const groups = $derived((() => {
    const q = query.toLowerCase()
    const filtered = all.filter((m) => {
      if (statusFilter === 'unlocked' && !m.unlocked) return false
      if (statusFilter === 'locked' && m.unlocked) return false
      if (catFilter !== 'all' && m.category !== catFilter) return false
      if (realmFilter !== 'all' && !(m.realms ?? []).includes(realmFilter)) return false
      if (q && !`${m.name_ja}${m.name_en}`.toLowerCase().includes(q)) return false
      return true
    })
    const order = cats
    const byCat = new Map<string, CraftMaterial[]>()
    for (const m of filtered) {
      const c = m.category || 'その他'
      if (!byCat.has(c)) byCat.set(c, [])
      byCat.get(c)!.push(m)
    }
    // 五十音順。ただし「きらめく○○」は元の「○○」の直後に並べる（ノーマル→Shinyのペア）
    const isShiny = (m: CraftMaterial) => m.name_en.startsWith('Shiny ')
    const baseEn = (m: CraftMaterial) => m.name_en.replace(/^Shiny /, '')
    const sortItems = (items: CraftMaterial[]) => {
      const normalJa = new Map<string, string>()
      for (const m of items) if (!isShiny(m)) normalJa.set(m.name_en, m.name_ja || m.name_en)
      const repKey = (m: CraftMaterial) =>
        normalJa.get(baseEn(m)) ?? (m.name_ja || m.name_en).replace(/^きらめく/, '')
      return [...items].sort((a, b) => {
        const rk = repKey(a).localeCompare(repKey(b), 'ja')
        if (rk !== 0) return rk
        return (isShiny(a) ? 1 : 0) - (isShiny(b) ? 1 : 0)
      })
    }
    const keys = [...byCat.keys()].sort((a, b) => {
      const ia = order.indexOf(a), ib = order.indexOf(b)
      return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib)
    })
    return keys.map((c) => ({ category: c, items: sortItems(byCat.get(c)!) }))
  })())
  const shownCount = $derived(groups.reduce((n, g) => n + g.items.length, 0))

  async function toggleUnlocked(m: CraftMaterial) {
    m.unlocked = !m.unlocked
    await put('crafting', $state.snapshot(m))
    all = [...all]
  }

  function toggleExpand(id: string) {
    const s = new Set(expanded)
    s.has(id) ? s.delete(id) : s.add(id)
    expanded = s
  }
</script>

<div class="head">
  <h1>クラフト素材</h1>
  <p class="sub">{all.length} 種 ・ 入手済み {unlockedCount} 種（鉱石・宝石・木材・石材など。名前タップで入手方法）</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="素材名で検索" bind:value={query} />
  <div class="row2">
    <select bind:value={realmFilter} aria-label="世界で絞り込み">
      <option value="all">世界：すべて</option>
      {#each realms as r}<option value={r}>{r}</option>{/each}
    </select>
    <select bind:value={catFilter} aria-label="種別で絞り込み">
      <option value="all">種別：すべて</option>
      {#each cats as c}<option value={c}>{c}</option>{/each}
    </select>
    <select bind:value={statusFilter} aria-label="入手状態で絞り込み">
      <option value="all">入手：すべて</option>
      <option value="unlocked">入手済み</option>
      <option value="locked">未入手</option>
    </select>
  </div>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <p class="count muted">{shownCount} 種表示</p>
  {#each groups as g (g.category)}
    <section class="cat">
      <div class="cat-head"><h2>{g.category}<span class="cnt">{g.items.length}</span></h2></div>
      <ul class="list">
        {#each g.items as m (m.id)}
          <li class="item" class:done={m.unlocked}>
            <div class="line">
              <button class="main" onclick={() => toggleExpand(m.id)}>
                <span class="mthumb">
                  {#if m.icon_path && !broken.has(m.id)}
                    <img src={asset(m.icon_path)} alt="" loading="lazy" onerror={() => markBroken(m.id)} />
                  {:else}<span class="ph">⛏️</span>{/if}
                </span>
                <span class="txt">
                  <span class="nm">{m.name_ja || m.name_en}</span>
                  {#if m.name_ja}<span class="en">{m.name_en}</span>{/if}
                </span>
              </button>
              {#if m.realms?.length}<span class="realm-badge">{m.realms.join('・')}</span>{/if}
              <button class="own" class:on={m.unlocked} onclick={() => toggleUnlocked(m)} title="入手トグル">
                {m.unlocked ? '✓' : '—'}
              </button>
            </div>
            {#if expanded.has(m.id)}
              <div class="detail">
                <div class="d-row">
                  <span class="lbl">入手方法</span>
                  <span class="obtain">{m.obtain_method || '—'}</span>
                </div>
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    </section>
  {/each}
  {#if shownCount === 0}<p class="muted">該当なし。</p>{/if}
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 16px; font-size: 14px; }
  .controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
  .search { font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .row2 { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; }
  .row2 select { font-family: var(--font-body); padding: 8px 10px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .count { font-size: 13px; margin: 0 0 8px; }

  .cat { margin: 0 0 18px; }
  .cat-head h2 { font-size: 16px; font-family: var(--font-display); display: flex; align-items: baseline; gap: 8px; margin: 0 0 4px; padding: 6px 2px 4px; border-bottom: 2px solid var(--c-accent-soft); }
  .cat-head .cnt { font-size: 12px; font-weight: 400; color: var(--c-ink-soft); font-variant-numeric: tabular-nums; }

  .list { list-style: none; padding: 0; margin: 0; }
  .item { border-bottom: 1px solid var(--c-line); }
  .item.done { background: color-mix(in srgb, var(--c-accent-soft) 22%, transparent); }
  .line { display: flex; align-items: center; gap: 8px; padding: 10px 4px; }
  .main { flex: 1 1 auto; min-width: 0; background: none; border: 0; text-align: left; padding: 4px 2px; display: flex; align-items: center; gap: 10px; }
  .mthumb { flex: none; width: 40px; height: 40px; display: grid; place-items: center; background: var(--c-surface-2); border-radius: 8px; overflow: hidden; }
  .mthumb img { width: 100%; height: 100%; object-fit: contain; }
  .mthumb .ph { font-size: 20px; opacity: 0.5; }
  .txt { display: flex; flex-direction: column; min-width: 0; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 15px; color: var(--c-ink); line-height: 1.25; }
  .en { font-size: 11px; color: var(--c-ink-soft); }
  .realm-badge {
    flex: none;
    font-size: 11px;
    font-weight: 600;
    color: var(--c-ink-soft);
    background: var(--c-surface-2);
    padding: 2px 8px;
    border-radius: 999px;
    white-space: nowrap;
  }
  .own { flex: none; width: 34px; height: 32px; border-radius: 8px; border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink-soft); font-weight: 700; cursor: pointer; }
  .own.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }

  .detail { padding: 4px 6px 12px 56px; display: flex; flex-direction: column; gap: 8px; }
  .d-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .lbl { flex: none; font-size: 11px; font-weight: 700; color: var(--c-accent-ink); background: var(--c-accent-soft); padding: 2px 8px; border-radius: 999px; }
  .obtain { font-size: 13px; color: var(--c-ink-soft); }
  .muted { color: var(--c-ink-soft); }
</style>
