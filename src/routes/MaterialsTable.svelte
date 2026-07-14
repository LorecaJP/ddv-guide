<script lang="ts">
  import type { Material } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { navigate, route, setParams, asset } from '../lib/router'

  const P = $route.params
  let all = $state<Material[]>([])
  let loading = $state(true)
  let query = $state(P.q ?? '')
  let statusFilter = $state(P.status ?? 'all') // 'all' | 'unlocked' | 'locked'
  let catFilter = $state(P.cat ?? 'all')
  let realmFilter = $state(P.realm ?? 'all')
  let selected = $state<Material | null>(null)
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') selected = null
  }

  // 絞り込み条件を URL に保持（戻る/リロード/共有で復元）
  $effect(() => {
    setParams('materials', { q: query, status: statusFilter, cat: catFilter, realm: realmFilter })
  })

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<Material>('materials')
    loading = false
  }
  load()

  // 種別・世界の表示順（実在するものだけを順に）
  const CAT_ORDER = ['農作物', 'フルーツ', '穀物', '魚', '魚介', '肉', '卵・ナッツ', '乳製品', 'キノコ', '茶葉', '甘味料', 'スパイス・ハーブ', 'その他']
  const REALM_ORDER = ['バレー', '永遠の島', '物語の谷', '願い咲く牧場']

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

  // フィルタ適用後、種別ごとに分けて各種別内を五十音順に並べる
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
    const byCat = new Map<string, Material[]>()
    for (const m of filtered) {
      const c = m.category || 'その他'
      if (!byCat.has(c)) byCat.set(c, [])
      byCat.get(c)!.push(m)
    }
    const sortJa = (a: Material, b: Material) =>
      (a.name_ja || a.name_en).localeCompare(b.name_ja || b.name_en, 'ja')
    const keys = [...byCat.keys()].sort((a, b) => {
      const ia = order.indexOf(a), ib = order.indexOf(b)
      return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib)
    })
    return keys.map((c) => ({ category: c, items: byCat.get(c)!.sort(sortJa) }))
  })())
  const shownCount = $derived(groups.reduce((n, g) => n + g.items.length, 0))

  // 名前を「本体」と「(色)」に分割（(色)は丸ごと2行目へ。全角/半角括弧対応）
  const splitName = (n: string) => {
    const m = n.match(/^(.*\S)([（(][^（(）)]*[)）])$/)
    return m ? { base: m[1], paren: m[2] } : { base: n, paren: '' }
  }

  async function toggleUnlocked(m: Material) {
    m.unlocked = !m.unlocked
    await put('materials', $state.snapshot(m))
    all = [...all]
    if (selected?.id === m.id) selected = m
  }

  // 入手方法を「本体｜（世界・エリア）｜成長…」の複数行に整形。
  // （…）が場所を表すときは先頭に世界名を付ける（波紋/泡/採取法などは付けない）。
  const REALM_NAMES = ['バレー', '永遠の島', '物語の谷', '願い咲く牧場', 'ハニーグローの森']
  const NON_PLACE = /波紋|泡|木から|茂み|地面|サボテン|ハチの巣|なし|再生|ランダム/
  const formatObtain = (obtain: string, realms: string[]) => {
    const o = (obtain || '').trim()
    if (!o) return ['—']
    const m = o.match(/^(.*?)([（(][^（(）)]*[)）])(.*)$/)
    if (!m) return [o]
    const pre = m[1].replace(/[｜|]\s*$/, '').trim()
    let inner = m[2].slice(1, -1)
    const post = m[3].replace(/^[\s｜|・／/]+/, '').trim()
    const world = (realms || []).join('・')
    const hasRealm = REALM_NAMES.some((r) => inner.includes(r) || pre.includes(r))
    if (world && !hasRealm && !NON_PLACE.test(inner)) inner = `${world}・${inner}`
    const lines: string[] = []
    if (pre) lines.push(pre)
    lines.push(`（${inner}）`)
    if (post) lines.push(post)
    return lines
  }
</script>

<svelte:window onkeydown={onKey} />

<div class="head">
  <h1>食材</h1>
  <p class="sub">{all.length} 種 ・ 解放済み {unlockedCount} 種（名前タップで入手方法・レシピ）</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="食材名で検索" bind:value={query} />
  <div class="row2">
    <select bind:value={realmFilter} aria-label="世界で絞り込み">
      <option value="all">世界：すべて</option>
      {#each realms as r}<option value={r}>{r}</option>{/each}
    </select>
    <select bind:value={catFilter} aria-label="種別で絞り込み">
      <option value="all">種別：すべて</option>
      {#each cats as c}<option value={c}>{c}</option>{/each}
    </select>
    <select bind:value={statusFilter} aria-label="解放状態で絞り込み">
      <option value="all">解放：すべて</option>
      <option value="unlocked">解放済み</option>
      <option value="locked">未解放</option>
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
          {@const nm = splitName(m.name_ja || m.name_en)}
          <li class="item" class:done={m.unlocked}>
            <button class="main" onclick={() => (selected = m)}>
              <span class="mthumb">
                {#if m.icon_path && !broken.has(m.id)}
                  <img src={asset(m.icon_path)} alt="" loading="lazy" onerror={() => markBroken(m.id)} />
                {:else}<span class="ph">🧺</span>{/if}
              </span>
              <span class="txt">
                <span class="nm">{nm.base}{#if nm.paren}<span class="paren">{nm.paren}</span>{/if}</span>
                {#if m.name_ja}<span class="en">{m.name_en}</span>{/if}
              </span>
              {#if m.realms?.length}<span class="realm-badge">{m.realms.join('・')}</span>{/if}
              {#if m.unlocked}<span class="tick">✓</span>{/if}
            </button>
          </li>
        {/each}
      </ul>
    </section>
  {/each}
  {#if shownCount === 0}<p class="muted">該当なし。</p>{/if}
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
          {:else}<span class="ph-big">🧺</span>{/if}
        </div>
        <div>
          <h2>{selected.name_ja || selected.name_en}</h2>
          {#if selected.name_ja}<p class="en">{selected.name_en}</p>{/if}
          <p class="chips">
            <span class="chip">{selected.category}</span>
            {#each selected.realms ?? [] as r}<span class="chip realm">{r}</span>{/each}
          </p>
        </div>
      </div>
      <dl class="facts">
        <dt>入手方法</dt>
        <dd>{#each formatObtain(selected.obtain_method, selected.realms) as line}<span class="obtain-line">{line}</span>{/each}</dd>
        <dt>使うレシピ</dt>
        <dd>
          {#if selected.used_in_recipes.length}
            <button class="recipes-btn" onclick={() => selected && navigate('recipes', { ing: selected.name_en })}>
              {selected.used_in_recipes.length}件を見る
            </button>
          {:else}なし{/if}
        </dd>
        {#if selected.memo}<dt>メモ</dt><dd>{selected.memo}</dd>{/if}
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
  .row2 select { font-family: var(--font-body); padding: 8px 10px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .count { font-size: 13px; margin: 0 0 8px; }

  .cat { margin: 0 0 18px; }
  .cat-head h2 { font-size: 16px; font-family: var(--font-display); display: flex; align-items: baseline; gap: 8px; margin: 0 0 4px; padding: 6px 2px 4px; border-bottom: 2px solid var(--c-accent-soft); }
  .cat-head .cnt { font-size: 12px; font-weight: 400; color: var(--c-ink-soft); font-variant-numeric: tabular-nums; }

  .list { list-style: none; padding: 0; margin: 0; }
  .item { border-bottom: 1px solid var(--c-line); }
  .item.done { background: color-mix(in srgb, var(--c-accent-soft) 22%, transparent); }
  .main { width: 100%; background: none; border: 0; text-align: left; padding: 10px 4px; display: flex; align-items: center; gap: 10px; cursor: pointer; }
  .mthumb { flex: none; width: 40px; height: 40px; display: grid; place-items: center; background: var(--c-surface-2); border-radius: 8px; overflow: hidden; }
  .mthumb img { width: 100%; height: 100%; object-fit: contain; }
  .mthumb .ph { font-size: 20px; opacity: 0.5; }
  .txt { flex: 1 1 auto; display: flex; flex-direction: column; min-width: 0; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 15px; color: var(--c-ink); line-height: 1.25; }
  .nm .paren { white-space: nowrap; }
  .en { font-size: 11px; color: var(--c-ink-soft); }
  .realm-badge {
    flex: none;
    font-size: 11px;
    font-weight: 600;
    color: var(--c-ink-soft);
    background: var(--c-surface-2);
    padding: 2px 8px;
    border-radius: 12px;
    text-align: center;
    white-space: nowrap;
  }
  .tick { flex: none; width: 22px; height: 22px; border-radius: 50%; background: var(--c-accent); color: #fff; font-size: 12px; display: grid; place-items: center; }

  .muted { color: var(--c-ink-soft); }

  /* モーダル */
  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(20,16,10,0.45); display: grid; place-items: center; padding: 20px; }
  .sheet { position: relative; width: min(420px, 94vw); background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 22px; box-shadow: 0 24px 60px rgba(0,0,0,0.3); }
  .close { position: absolute; top: 12px; right: 12px; background: var(--c-surface-2); border: 0; border-radius: 8px; width: 30px; height: 30px; color: var(--c-ink-soft); }
  .sheet-top { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
  .big-thumb { width: 84px; height: 84px; flex: none; background: var(--c-surface-2); border-radius: var(--radius-sm); display: grid; place-items: center; overflow: hidden; }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .ph-big { font-size: 34px; opacity: 0.5; }
  .sheet-top h2 { font-size: 20px; padding-right: 34px; }
  .obtain-line { display: block; }
  .obtain-line:not(:first-child) { color: var(--c-ink-soft); }
  .en { color: var(--c-ink-soft); margin: 3px 0 8px; font-size: 13px; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 0; }
  .chip { display: inline-block; background: var(--c-accent-soft); color: var(--c-accent-ink); font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px; }
  .chip.realm { background: var(--c-surface-2); color: var(--c-ink-soft); }
  .facts { display: grid; grid-template-columns: 84px 1fr; gap: 10px 12px; margin: 4px 0 0; font-size: 14px; align-items: start; line-height: 1.5; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .recipes-btn { font-size: 14px; font-weight: 700; color: var(--c-accent-ink); background: none; border: 0; padding: 0; cursor: pointer; }
  .recipes-btn:hover { text-decoration: underline; }
  .own-tgl { padding: 8px 16px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .own-tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
