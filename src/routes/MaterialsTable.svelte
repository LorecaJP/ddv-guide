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
  let expanded = $state<Set<string>>(new Set())
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))

  // 絞り込み条件を URL に保持（戻る/リロード/共有で復元）
  $effect(() => {
    setParams('materials', { q: query, status: statusFilter, cat: catFilter })
  })

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<Material>('materials')
    loading = false
  }
  load()

  // 種別の表示順（実在するものだけを順に）
  const CAT_ORDER = ['農作物', 'フルーツ', '穀物', '魚', '魚介', '肉', '卵・ナッツ', '乳製品', 'キノコ', '茶葉', '甘味料', 'スパイス・ハーブ', 'その他']
  const cats = $derived((() => {
    const present = new Set(all.map((m) => m.category).filter(Boolean))
    const ordered = CAT_ORDER.filter((c) => present.has(c))
    const extra = [...present].filter((c) => !CAT_ORDER.includes(c)).sort()
    return [...ordered, ...extra]
  })())
  const unlockedCount = $derived(all.filter((m) => m.unlocked).length)

  const view = $derived(
    all
      .filter((m) => {
        if (statusFilter === 'unlocked' && !m.unlocked) return false
        if (statusFilter === 'locked' && m.unlocked) return false
        if (catFilter !== 'all' && m.category !== catFilter) return false
        if (query) {
          const q = query.toLowerCase()
          if (!`${m.name_ja}${m.name_en}`.toLowerCase().includes(q)) return false
        }
        return true
      })
      .sort((a, b) => {
        const aj = !!a.name_ja, bj = !!b.name_ja
        if (aj !== bj) return aj ? -1 : 1
        return (a.name_ja || a.name_en).localeCompare(b.name_ja || b.name_en, 'ja')
      })
  )

  async function toggleUnlocked(m: Material) {
    m.unlocked = !m.unlocked
    await put('materials', $state.snapshot(m))
    all = [...all]
  }

  function toggleExpand(id: string) {
    const s = new Set(expanded)
    s.has(id) ? s.delete(id) : s.add(id)
    expanded = s
  }
</script>

<div class="head">
  <h1>素材</h1>
  <p class="sub">{all.length} 種 ・ 解放済み {unlockedCount} 種（素材名タップで入手方法・レシピ）</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="素材名で検索" bind:value={query} />
  <div class="row2">
    <select bind:value={statusFilter} aria-label="解放状態で絞り込み">
      <option value="all">解放：すべて</option>
      <option value="unlocked">解放済み</option>
      <option value="locked">未解放</option>
    </select>
    <select bind:value={catFilter} aria-label="種別で絞り込み">
      <option value="all">種別：すべて</option>
      {#each cats as c}<option value={c}>{c}</option>{/each}
    </select>
  </div>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <p class="count muted">{view.length} 種表示</p>
  <ul class="list">
    {#each view as m (m.id)}
      <li class="item" class:done={m.unlocked}>
        <div class="line">
          <button class="main" onclick={() => toggleExpand(m.id)}>
            <span class="mthumb">
              {#if m.icon_path && !broken.has(m.id)}
                <img src={asset(m.icon_path)} alt="" loading="lazy" onerror={() => markBroken(m.id)} />
              {:else}<span class="ph">🧺</span>{/if}
            </span>
            <span class="txt">
              <span class="nm">{m.name_ja || m.name_en}</span>
              {#if m.name_ja}<span class="en">{m.name_en}</span>{/if}
            </span>
          </button>
          {#if m.category}<span class="cat-badge">{m.category}</span>{/if}
          <button class="own" class:on={m.unlocked} onclick={() => toggleUnlocked(m)} title="解放トグル">
            {m.unlocked ? '✓' : '—'}
          </button>
        </div>
        {#if expanded.has(m.id)}
          <div class="detail">
            <div class="d-row">
              <span class="lbl">入手方法</span>
              <span class="obtain">{m.obtain_method || '—'}</span>
            </div>
            <div class="d-row">
              <span class="lbl">使うレシピ</span>
              {#if m.used_in_recipes.length}
                <button class="recipes-btn" onclick={() => navigate('recipes', { ing: m.name_en })}>
                  {m.used_in_recipes.length}件を見る
                </button>
              {:else}
                <span class="obtain">なし</span>
              {/if}
            </div>
          </div>
        {/if}
      </li>
    {/each}
  </ul>
  {#if view.length === 0}<p class="muted">該当なし。</p>{/if}
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 16px; font-size: 14px; }
  .controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
  .search { font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .row2 { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; }
  .row2 select { font-family: var(--font-body); padding: 8px 10px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .count { font-size: 13px; margin: 0 0 8px; }

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
  .cat-badge {
    flex: none;
    font-size: 11px;
    font-weight: 600;
    color: var(--c-accent-ink);
    background: var(--c-accent-soft);
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
  .recipes-btn { font-size: 13px; font-weight: 700; color: var(--c-accent-ink); background: none; border: 0; padding: 0; cursor: pointer; }
  .recipes-btn:hover { text-decoration: underline; }
  .muted { color: var(--c-ink-soft); }
</style>
