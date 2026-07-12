<script lang="ts">
  import type { Companion } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { asset } from '../lib/router'

  let all = $state<Companion[]>([])
  let loading = $state(true)
  let query = $state('')
  let ownedOnly = $state(false)
  let selected = $state<Companion | null>(null)
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))

  async function load() {
    loading = true
    await seedAll()
    all = await getAll<Companion>('companions')
    loading = false
  }
  load()

  const ownedCount = $derived(all.filter((c) => c.owned).length)

  // 種ごとにまとめ、種内は色名の五十音順。種は五十音順。
  const groups = $derived(
    (() => {
      const filtered = all.filter((c) => {
        if (ownedOnly && !c.owned) return false
        if (query) {
          const q = query.toLowerCase()
          if (!`${c.name_ja}${c.name_en}${c.gather_type}`.toLowerCase().includes(q)) return false
        }
        return true
      })
      const map = new Map<string, Companion[]>()
      for (const c of filtered) {
        if (!map.has(c.gather_type)) map.set(c.gather_type, [])
        map.get(c.gather_type)!.push(c)
      }
      const out = [...map.entries()].map(([species, items]) => {
        items.sort((a, b) => a.color_ja.localeCompare(b.color_ja, 'ja'))
        const sample = items[0]
        return {
          species,
          habitat: sample?.habitat ?? '',
          foods: sample?.favorite_foods ?? [],
          owned: items.filter((i) => i.owned).length,
          items,
        }
      })
      out.sort((a, b) => a.species.localeCompare(b.species, 'ja'))
      return out
    })(),
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
  <p class="sub">{ownedCount} / {all.length} 体 なかま ・ 種ごと（色は五十音順）。好物をあげて仲間に</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="名前・色・種で検索" bind:value={query} />
  <label class="toggle"><input type="checkbox" bind:checked={ownedOnly} />なかまのみ</label>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  {#each groups as g (g.species)}
    <section class="species">
      <div class="sp-head">
        <h2>{g.species}<span class="cnt">{g.owned}/{g.items.length}</span></h2>
        <div class="sp-meta">
          {#if g.habitat}<span class="meta"><span class="lbl">生息地</span>{g.habitat}</span>{/if}
          {#if g.foods.length}
            <span class="meta"><span class="lbl">好物</span>{#each g.foods as f}<span class="chip">{f}</span>{/each}</span>
          {/if}
        </div>
      </div>
      <div class="zukan">
        {#each g.items as c (c.id)}
          <button class="card" class:dim={!c.owned} onclick={() => (selected = c)}>
            <div class="thumb">
              {#if c.icon_path && !broken.has(c.id)}
                <img src={asset(c.icon_path)} alt={c.name_ja} loading="lazy" onerror={() => markBroken(c.id)} />
              {:else}
                <span class="noimg"><span class="ph-mark">🐾</span><span class="ph-name">{c.color_ja}</span></span>
              {/if}
              {#if c.owned}<span class="own">✓</span>{/if}
              {#if c.is_equipped}<span class="eq">★</span>{/if}
            </div>
            <span class="nm">{c.color_ja}</span>
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
    <div class="sheet" onclick={(e) => e.stopPropagation()}>
      <button class="close" onclick={() => (selected = null)}>✕</button>
      <div class="sheet-top">
        <div class="big-thumb">
          {#if selected.icon_path && !broken.has(selected.id)}
            <img src={asset(selected.icon_path)} alt={selected.name_ja} onerror={() => selected && markBroken(selected.id)} />
          {:else}<span class="noimg"><span class="ph-mark">🐾</span></span>{/if}
        </div>
        <div>
          <h2>{selected.name_ja}</h2>
          <p class="en">{selected.name_en}</p>
          <p class="chip solid">{selected.gather_type}</p>
        </div>
      </div>
      <dl class="facts">
        <dt>生息地</dt><dd>{selected.habitat || '—'}</dd>
        <dt>好物</dt>
        <dd>{#if selected.favorite_foods.length}{#each selected.favorite_foods as f}<span class="chip">{f}</span>{/each}{:else}—{/if}</dd>
        <dt>フレンドLv</dt>
        <dd>
          <div class="stepper">
            <button onclick={() => selected && setFriend(selected, selected.friendship_level - 1)}>−</button>
            <span class="val">{selected.friendship_level}<span class="mx"> / 10</span></span>
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
  .controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 22px; }
  .search { flex: 1 1 220px; font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .toggle { display: inline-flex; align-items: center; gap: 7px; font-size: 14px; color: var(--c-ink-soft); }

  .species { margin-bottom: 26px; }
  .sp-head { border-bottom: 2px solid var(--c-accent-soft); padding-bottom: 8px; margin-bottom: 14px; }
  .sp-head h2 { font-size: 20px; display: flex; align-items: baseline; gap: 10px; }
  .cnt { font-size: 13px; color: var(--c-ink-soft); font-weight: 400; }
  .sp-meta { display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 8px; font-size: 13px; color: var(--c-ink-soft); }
  .meta { display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .lbl { font-size: 11px; font-weight: 700; color: var(--c-accent-ink); background: var(--c-accent-soft); padding: 1px 7px; border-radius: 999px; }

  .zukan { display: grid; grid-template-columns: repeat(auto-fill, minmax(108px, 1fr)); gap: var(--gap); }
  .card { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 10px 8px 12px; background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); box-shadow: 0 1px 0 var(--c-shadow); transition: transform .12s, box-shadow .12s, border-color .12s; }
  .card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px var(--c-shadow); border-color: var(--c-accent); }
  .card.dim { opacity: 0.62; }
  .thumb { position: relative; width: 100%; aspect-ratio: 1/1; display: grid; place-items: center; background: var(--c-surface-2); border-radius: var(--radius-sm); overflow: hidden; }
  .thumb img { width: 100%; height: 100%; object-fit: contain; }
  .noimg { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; width: 100%; height: 100%; padding: 4px; text-align: center; background: linear-gradient(160deg, var(--c-surface-2), color-mix(in srgb, var(--c-accent-soft) 40%, var(--c-surface-2))); }
  .ph-mark { font-size: 22px; opacity: 0.5; }
  .ph-name { font-family: var(--font-display); font-weight: 600; font-size: 11px; color: var(--c-ink-soft); line-height: 1.1; }
  .own { position: absolute; top: 5px; right: 5px; width: 19px; height: 19px; border-radius: 50%; background: var(--c-accent); color: #fff; font-size: 11px; display: grid; place-items: center; }
  .eq { position: absolute; top: 5px; left: 5px; width: 19px; height: 19px; border-radius: 50%; background: var(--c-magic); color: #fff; font-size: 10px; display: grid; place-items: center; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 13px; text-align: center; line-height: 1.15; }

  .chip { display: inline-block; margin: 2px 4px 2px 0; background: var(--c-surface-2); border: 1px solid var(--c-line); font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .chip.solid { background: var(--c-accent-soft); color: var(--c-accent-ink); border: 0; font-weight: 600; }
  .muted { color: var(--c-ink-soft); }

  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(20,16,10,.45); display: grid; place-items: center; padding: 20px; }
  .sheet { position: relative; width: min(440px, 94vw); background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 22px; box-shadow: 0 24px 60px rgba(0,0,0,.3); }
  .close { position: absolute; top: 12px; right: 12px; background: var(--c-surface-2); border: 0; border-radius: 8px; width: 30px; height: 30px; color: var(--c-ink-soft); }
  .sheet-top { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
  .big-thumb { width: 104px; height: 104px; flex: none; background: var(--c-surface-2); border-radius: var(--radius-sm); display: grid; place-items: center; overflow: hidden; }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .sheet-top h2 { font-size: 22px; }
  .en { color: var(--c-ink-soft); margin: 3px 0 8px; font-size: 13px; }
  .facts { display: grid; grid-template-columns: 80px 1fr; gap: 10px 12px; margin: 4px 0 18px; font-size: 14px; align-items: center; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .stepper { display: inline-flex; align-items: center; gap: 8px; }
  .stepper button { width: 30px; height: 30px; border-radius: 8px; border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 700; font-size: 16px; }
  .stepper .val { min-width: 54px; text-align: center; font-family: var(--font-display); font-weight: 700; font-size: 18px; }
  .mx { font-size: 12px; color: var(--c-ink-soft); font-weight: 400; }
  .btns { display: flex; gap: 10px; }
  .tgl { flex: 1; padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
