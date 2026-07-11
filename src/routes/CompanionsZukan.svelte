<script lang="ts">
  import type { Companion } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { asset } from '../lib/router'

  let all = $state<Companion[]>([])
  let loading = $state(true)
  let query = $state('')
  let typeFilter = $state('all')
  let ownedOnly = $state(false)
  let selected = $state<Companion | null>(null)
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))

  async function load() {
    loading = true
    await seedAll()
    all = (await getAll<Companion>('companions')).sort((a, b) => a.name_en.localeCompare(b.name_en))
    loading = false
  }
  load()

  const types = $derived([...new Set(all.map((c) => c.gather_type))].sort())
  const ownedCount = $derived(all.filter((c) => c.owned).length)

  const filtered = $derived(
    all.filter((c) => {
      if (ownedOnly && !c.owned) return false
      if (typeFilter !== 'all' && c.gather_type !== typeFilter) return false
      if (query && !`${c.name_ja}${c.name_en}`.toLowerCase().includes(query.toLowerCase())) return false
      return true
    }),
  )

  async function save(c: Companion) {
    await put('companions', $state.snapshot(c))
    all = [...all]
    if (selected?.id === c.id) selected = c
  }
  function toggleOwned(c: Companion) { c.owned = !c.owned; save(c) }
  function toggleEquip(c: Companion) { c.is_equipped = !c.is_equipped; save(c) }
  function setFriend(c: Companion, v: number) { c.friendship_level = Math.max(0, Math.min(10, v | 0)); save(c) }
</script>

<div class="head">
  <h1>オトモ図鑑</h1>
  <p class="sub">{ownedCount} / {all.length} 体 なかま ・ 色違いクリッター（餌付けで仲間に）</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="名前で検索" bind:value={query} />
  <select bind:value={typeFilter}>
    <option value="all">すべての種</option>
    {#each types as t}<option value={t}>{t}</option>{/each}
  </select>
  <label class="toggle"><input type="checkbox" bind:checked={ownedOnly} />なかまのみ</label>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <div class="zukan">
    {#each filtered as c (c.id)}
      <button class="card" class:dim={!c.owned} onclick={() => (selected = c)}>
        <div class="thumb">
          {#if c.icon_path && !broken.has(c.id)}
            <img src={asset(c.icon_path)} alt={c.name_en} loading="lazy" onerror={() => markBroken(c.id)} />
          {:else}<span class="noimg">?</span>{/if}
          {#if c.owned}<span class="own">✓</span>{/if}
          {#if c.is_equipped}<span class="eq">★</span>{/if}
        </div>
        <span class="nm">{c.name_ja || c.name_en}</span>
        <span class="fr">{c.gather_type}</span>
      </button>
    {/each}
  </div>
  {#if filtered.length === 0}<p class="muted">該当なし。</p>{/if}
{/if}

{#if selected}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="backdrop" onclick={() => (selected = null)}>
    <div class="sheet" onclick={(e) => e.stopPropagation()}>
      <button class="close" onclick={() => (selected = null)}>✕</button>
      <div class="sheet-top">
        <div class="big-thumb">
          {#if selected.icon_path && !broken.has(selected.id)}
            <img src={asset(selected.icon_path)} alt={selected.name_en} onerror={() => selected && markBroken(selected.id)} />
          {:else}<span class="noimg">?</span>{/if}
        </div>
        <div>
          <h2>{selected.name_ja || selected.name_en}</h2>
          <p class="en">{selected.name_en}</p>
          <p class="chip">{selected.gather_type}</p>
        </div>
      </div>
      <dl class="facts">
        <dt>入手元</dt><dd>{selected.source || '—'}</dd>
        <dt>メモ</dt><dd>{selected.memo || '—'}</dd>
        <dt>フレンドLv</dt>
        <dd>
          <div class="stepper">
            <button onclick={() => selected && setFriend(selected, selected.friendship_level - 1)}>−</button>
            <span class="val">{selected.friendship_level}</span>
            <button onclick={() => selected && setFriend(selected, selected.friendship_level + 1)}>＋</button>
          </div>
        </dd>
      </dl>
      <div class="btns">
        <button class="tgl" class:on={selected.owned} onclick={() => selected && toggleOwned(selected)}>
          {selected.owned ? '✓ なかま' : 'なかまにする'}
        </button>
        <button class="tgl" class:on={selected.is_equipped} onclick={() => selected && toggleEquip(selected)}>
          {selected.is_equipped ? '★ 連れ歩き中' : '連れ歩く'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 18px; font-size: 14px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
  .search, select { font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .search { flex: 1 1 220px; }
  .toggle { display: inline-flex; align-items: center; gap: 7px; font-size: 14px; color: var(--c-ink-soft); }
  .zukan { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: var(--gap); }
  .card { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px 10px 14px; background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); box-shadow: 0 1px 0 var(--c-shadow); transition: transform .12s, box-shadow .12s, border-color .12s; }
  .card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px var(--c-shadow); border-color: var(--c-accent); }
  .card.dim { opacity: 0.66; }
  .thumb { position: relative; width: 100%; aspect-ratio: 1/1; display: grid; place-items: center; background: var(--c-surface-2); border-radius: var(--radius-sm); overflow: hidden; }
  .thumb img { width: 100%; height: 100%; object-fit: contain; }
  .noimg { font-family: var(--font-display); font-size: 30px; color: var(--c-ink-soft); }
  .own { position: absolute; top: 6px; right: 6px; width: 20px; height: 20px; border-radius: 50%; background: var(--c-accent); color: #fff; font-size: 12px; display: grid; place-items: center; }
  .eq { position: absolute; top: 6px; left: 6px; width: 20px; height: 20px; border-radius: 50%; background: var(--c-magic); color: #fff; font-size: 11px; display: grid; place-items: center; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 14px; text-align: center; }
  .fr { font-size: 11px; color: var(--c-ink-soft); }
  .muted { color: var(--c-ink-soft); }
  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(20,16,10,.45); display: grid; place-items: center; padding: 20px; }
  .sheet { position: relative; width: min(440px, 94vw); background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 22px; box-shadow: 0 24px 60px rgba(0,0,0,.3); }
  .close { position: absolute; top: 12px; right: 12px; background: var(--c-surface-2); border: 0; border-radius: 8px; width: 30px; height: 30px; color: var(--c-ink-soft); }
  .sheet-top { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
  .big-thumb { width: 104px; height: 104px; flex: none; background: var(--c-surface-2); border-radius: var(--radius-sm); display: grid; place-items: center; overflow: hidden; }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .sheet-top h2 { font-size: 22px; }
  .en { color: var(--c-ink-soft); margin: 3px 0 8px; font-size: 13px; }
  .chip { display: inline-block; margin: 0; background: var(--c-accent-soft); color: var(--c-accent-ink); font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px; }
  .facts { display: grid; grid-template-columns: 88px 1fr; gap: 8px 12px; margin: 4px 0 18px; font-size: 14px; align-items: center; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .stepper { display: inline-flex; align-items: center; gap: 8px; }
  .stepper button { width: 26px; height: 26px; border-radius: 7px; border: 1px solid var(--c-line); background: var(--c-surface); color: var(--c-ink); font-weight: 700; }
  .stepper .val { min-width: 20px; text-align: center; }
  .btns { display: flex; gap: 10px; }
  .tgl { flex: 1; padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
