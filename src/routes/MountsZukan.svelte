<script lang="ts">
  import type { Mount } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { asset, route, setParams } from '../lib/router'

  const P = $route.params
  let all = $state<Mount[]>([])
  let loading = $state(true)
  let query = $state(P.q ?? '')
  let statusFilter = $state(P.status ?? 'all') // 'all' | 'owned' | 'unowned'
  let catFilter = $state(P.cat ?? 'all')
  let levelFilter = $state(P.lv ?? 'all') // 'all' | 'max' | 'notmax'
  let selected = $state<Mount | null>(null)
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))
  const MAX_LV = 10
  const lvOf = (m: Mount) => Math.max(1, Math.min(MAX_LV, m.friendship_level || 1))

  $effect(() => {
    setParams('mounts', { q: query, cat: catFilter, status: statusFilter, lv: levelFilter })
  })
  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') selected = null
  }

  async function load() {
    loading = true
    await seedAll()
    all = (await getAll<Mount>('mounts')).sort((a, b) => a.name_ja.localeCompare(b.name_ja, 'ja'))
    loading = false
  }
  load()

  const cats = $derived([...new Set(all.map((m) => m.category).filter(Boolean))])
  const ownedCount = $derived(all.filter((m) => m.owned).length)

  const groups = $derived(
    (() => {
      const q = query.toLowerCase()
      const filtered = all.filter((m) => {
        if (statusFilter === 'owned' && !m.owned) return false
        if (statusFilter === 'unowned' && m.owned) return false
        if (catFilter !== 'all' && m.category !== catFilter) return false
        if (levelFilter === 'max' && lvOf(m) < MAX_LV) return false
        if (levelFilter === 'notmax' && lvOf(m) >= MAX_LV) return false
        if (q && !`${m.name_ja}${m.name_en}`.toLowerCase().includes(q)) return false
        return true
      })
      const map = new Map<string, Mount[]>()
      for (const m of filtered) {
        const c = m.category || 'その他'
        if (!map.has(c)) map.set(c, [])
        map.get(c)!.push(m)
      }
      return [...map.entries()].map(([category, items]) => {
        items.sort((a, b) => a.name_ja.localeCompare(b.name_ja, 'ja'))
        return { category, owned: items.filter((i) => i.owned).length, items }
      })
    })(),
  )

  async function save(m: Mount) {
    await put('mounts', $state.snapshot(m))
    all = [...all]
    if (selected?.id === m.id) selected = m
  }
  function toggleOwned(m: Mount) {
    m.owned = !m.owned
    save(m)
  }
  function setLevel(m: Mount, v: number) {
    m.friendship_level = Math.max(1, Math.min(MAX_LV, v | 0))
    save(m)
  }
</script>

<svelte:window onkeydown={onKey} />

<div class="head">
  <div>
    <h1>騎乗動物図鑑</h1>
    <p class="sub">{ownedCount} / {all.length} 頭 入手済み（願い咲く牧場で追加された騎乗できる馬など）</p>
  </div>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="名前で検索（日本語 / 英語）" bind:value={query} />
  {#if cats.length > 1}
    <select bind:value={catFilter} aria-label="種別で絞り込み">
      <option value="all">種別：すべて</option>
      {#each cats as c}<option value={c}>{c}</option>{/each}
    </select>
  {/if}
  <select bind:value={statusFilter} aria-label="入手状態で絞り込み">
    <option value="all">入手：すべて</option>
    <option value="owned">入手済み</option>
    <option value="unowned">未入手</option>
  </select>
  <select bind:value={levelFilter} aria-label="レベルで絞り込み">
    <option value="all">Lv：すべて</option>
    <option value="notmax">MAX未満</option>
    <option value="max">MAX（10）</option>
  </select>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  {#each groups as g (g.category)}
    <section class="cat">
      <div class="cat-head">
        <h2>{g.category}<span class="cnt">{g.owned}/{g.items.length}</span></h2>
      </div>
      <div class="zukan">
        {#each g.items as m (m.id)}
          <button class="card" class:dim={!m.owned} onclick={() => (selected = m)}>
            <div class="thumb">
              {#if m.icon_path && !broken.has(m.id)}
                <img src={asset(m.icon_path)} alt={m.name_ja} loading="lazy" onerror={() => markBroken(m.id)} />
              {:else}
                <span class="noimg"><span class="ph-mark">🐴</span><span class="ph-name">{m.name_ja}</span></span>
              {/if}
              {#if m.owned}<span class="own">✓</span>{/if}
              <span class="lv-badge" class:max={lvOf(m) >= MAX_LV}>{lvOf(m) >= MAX_LV ? 'MAX' : 'Lv' + lvOf(m)}</span>
            </div>
            <span class="nm">{m.name_ja}</span>
          </button>
        {/each}
      </div>
    </section>
  {/each}
  {#if groups.length === 0}<p class="muted">該当なし。</p>{/if}
{/if}

{#if selected}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="backdrop" onclick={() => (selected = null)}>
    <div class="sheet" role="dialog" aria-modal="true" aria-label={selected.name_ja} tabindex="-1" onclick={(e) => e.stopPropagation()}>
      <button class="close" onclick={() => (selected = null)} aria-label="閉じる">✕</button>
      <div class="sheet-top">
        <div class="big-thumb">
          {#if selected.icon_path && !broken.has(selected.id)}
            <img src={asset(selected.icon_path)} alt={selected.name_ja} onerror={() => selected && markBroken(selected.id)} />
          {:else}<span class="noimg"><span class="ph-mark">🐴</span></span>{/if}
        </div>
        <div>
          <h2>{selected.name_ja}</h2>
          <p class="en">{selected.name_en}</p>
          <p class="chip">{selected.category}</p>
        </div>
      </div>
      <dl class="facts">
        <dt>入手方法</dt><dd>{selected.obtain_method || '（未登録）'}</dd>
        <dt>特殊能力・備考</dt><dd>{selected.ability_note || '—'}</dd>
        <dt>友情Lv</dt>
        <dd>
          <div class="stepper">
            <button onclick={() => selected && setLevel(selected, lvOf(selected) - 1)} aria-label="下げる">−</button>
            <span class="lv">{lvOf(selected)}<span class="lvmax"> / {MAX_LV}</span></span>
            <button onclick={() => selected && setLevel(selected, lvOf(selected) + 1)} aria-label="上げる">＋</button>
          </div>
        </dd>
        <dt>メモ</dt><dd>{selected.memo || '—'}</dd>
        <dt>入手</dt>
        <dd>
          <button class="own-tgl" class:on={selected.owned} onclick={() => selected && toggleOwned(selected)}>
            {selected.owned ? '✓ 入手済み' : '未入手'}
          </button>
        </dd>
      </dl>
    </div>
  </div>
{/if}

<style>
  .head { display: flex; justify-content: space-between; align-items: end; margin-bottom: 16px; }
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 0; font-size: 14px; }

  .controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
  .search, select {
    font-family: var(--font-body);
    padding: 9px 12px;
    border: 1px solid var(--c-line);
    border-radius: var(--radius-sm);
    background: var(--c-surface);
    color: var(--c-ink);
  }
  .search { flex: 1 1 240px; }

  .cat { margin-bottom: 26px; }
  .cat-head { border-bottom: 2px solid var(--c-accent-soft); padding-bottom: 8px; margin-bottom: 14px; }
  .cat-head h2 { font-size: 20px; display: flex; align-items: baseline; gap: 10px; }
  .cnt { font-size: 13px; color: var(--c-ink-soft); font-weight: 400; }
  .zukan {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: var(--gap);
  }
  .card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 10px 14px;
    background: var(--c-surface);
    border: 1px solid var(--c-line);
    border-radius: var(--radius);
    box-shadow: 0 1px 0 var(--c-shadow);
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
  }
  .card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px var(--c-shadow); border-color: var(--c-accent); }
  .card.dim { opacity: 0.66; }
  .thumb {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    display: grid;
    place-items: center;
    background: var(--c-surface-2);
    border-radius: var(--radius-sm);
    overflow: hidden;
  }
  .thumb img { width: 100%; height: 100%; object-fit: contain; }
  .noimg {
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
    width: 100%; height: 100%; padding: 6px; text-align: center;
    background: linear-gradient(160deg, var(--c-surface-2), color-mix(in srgb, var(--c-accent-soft) 40%, var(--c-surface-2)));
  }
  .ph-mark { font-size: 26px; opacity: 0.55; }
  .ph-name { font-family: var(--font-display); font-weight: 600; font-size: 12px; color: var(--c-ink-soft); line-height: 1.15; }
  .own {
    position: absolute; top: 6px; right: 6px;
    width: 20px; height: 20px; border-radius: 50%;
    background: var(--c-accent); color: #fff; font-size: 12px;
    display: grid; place-items: center;
  }
  .lv-badge {
    position: absolute; bottom: 6px; left: 6px;
    background: color-mix(in srgb, var(--c-ink) 72%, transparent); color: #fff;
    font-size: 11px; font-weight: 700; line-height: 1;
    padding: 3px 6px; border-radius: 999px; font-variant-numeric: tabular-nums;
  }
  .lv-badge.max { background: var(--c-accent); }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 14px; text-align: center; }

  .muted { color: var(--c-ink-soft); }

  .backdrop {
    position: fixed; inset: 0; z-index: 30;
    background: rgba(20, 16, 10, 0.45);
    display: grid; place-items: center; padding: 20px;
  }
  .sheet {
    position: relative;
    width: min(440px, 94vw);
    background: var(--c-surface);
    border: 1px solid var(--c-line);
    border-radius: var(--radius);
    padding: 22px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.3);
  }
  .close {
    position: absolute; top: 12px; right: 12px;
    background: var(--c-surface-2); border: 0; border-radius: 8px;
    width: 30px; height: 30px; color: var(--c-ink-soft);
  }
  .sheet-top { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
  .big-thumb {
    width: 116px; height: 116px; flex: none;
    background: var(--c-surface-2); border-radius: var(--radius-sm);
    display: grid; place-items: center; overflow: hidden;
  }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .sheet-top h2 { font-size: 22px; padding-right: 34px; }
  .en { color: var(--c-ink-soft); margin: 3px 0 8px; font-size: 13px; }
  .chip {
    display: inline-block; margin: 0;
    background: var(--c-accent-soft); color: var(--c-accent-ink);
    font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  }
  .facts { display: grid; grid-template-columns: 108px 1fr; gap: 10px 12px; margin: 4px 0 18px; font-size: 14px; align-items: start; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .own-tgl { padding: 8px 16px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .own-tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
  .stepper { display: inline-flex; align-items: center; gap: 8px; }
  .stepper button {
    width: 30px; height: 30px; border-radius: 8px; border: 1px solid var(--c-line);
    background: var(--c-surface-2); color: var(--c-ink); font-weight: 700; font-size: 16px;
  }
  .lv { min-width: 56px; text-align: center; font-family: var(--font-display); font-weight: 700; font-size: 18px; }
  .lvmax { font-size: 12px; color: var(--c-ink-soft); font-weight: 400; }
</style>
