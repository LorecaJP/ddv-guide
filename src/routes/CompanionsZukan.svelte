<script lang="ts">
  import type { Companion } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { asset, route, setParams } from '../lib/router'

  const P = $route.params
  let all = $state<Companion[]>([])
  let loading = $state(true)
  let query = $state(P.q ?? '')
  let statusFilter = $state(P.status ?? 'all') // 'all' | 'owned' | 'unowned'
  let levelFilter = $state(P.lv ?? 'all') // 'all' | 'max' | 'notmax'
  let appearFilter = $state(P.appear ?? 'all') // 'all' | 'today' | 'now'
  let selected = $state<Companion | null>(null)
  const MAX_LV = 5

  // 出現スケジュール（例: "火・水・土：終日\n日：午前12時～午後12時"）から今日出現するか判定
  // ゲーム内時間は現実のローカル時間と同期・0時で日付リセットのため端末時刻で判定。
  const WD = ['日', '月', '火', '水', '木', '金', '土']
  const now = new Date()
  const todayChar = WD[now.getDay()]
  const nowHour = now.getHours()

  const toHour = (s: string): number | null => {
    const m = s.match(/(\d{1,2})/)
    if (!m) return null
    let h = parseInt(m[1], 10)
    if (s.includes('午前')) h = h === 12 ? 0 : h
    else if (s.includes('午後')) h = h === 12 ? 12 : h + 12
    else if (/PM/i.test(s)) h = h < 12 ? h + 12 : h
    else if (/AM/i.test(s)) h = h === 12 ? 0 : h
    return h
  }
  const parseRange = (t: string): [number, number] | null => {
    t = t.trim()
    if (t.startsWith('終日')) return [0, 24]
    const parts = t.split(/[~～\-]/)
    if (parts.length < 2) return null
    const s = toHour(parts[0]), e = toHour(parts[1])
    if (s == null || e == null) return null
    return [s, e <= s ? 24 : e]
  }
  const parseLine = (line: string) => {
    const ci = line.indexOf('：') >= 0 ? line.indexOf('：') : line.indexOf(':')
    const days = ci >= 0 ? line.slice(0, ci) : line
    const time = ci >= 0 ? line.slice(ci + 1) : ''
    const dayOk = days.includes('毎日') || days.split('・').some((d) => d.trim() === todayChar)
    return { dayOk, time }
  }
  const appearsToday = (sched: string) => !!sched && sched.split('\n').some((l) => parseLine(l).dayOk)
  const appearsNow = (sched: string) => {
    if (!sched) return false
    for (const line of sched.split('\n')) {
      const { dayOk, time } = parseLine(line)
      if (!dayOk) continue
      const r = parseRange(time)
      if (!r) return true
      if (r[0] <= nowHour && nowHour < r[1]) return true
    }
    return false
  }

  // 絞り込み条件を URL に保持（戻る/リロード/共有で復元）
  $effect(() => {
    setParams('companions', { q: query, status: statusFilter, lv: levelFilter, appear: appearFilter === 'all' ? '' : appearFilter })
  })
  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') selected = null
  }
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
        if (statusFilter === 'owned' && !c.owned) return false
        if (statusFilter === 'unowned' && c.owned) return false
        const lvl = Math.max(1, c.friendship_level || 1)
        if (levelFilter === 'max' && lvl < MAX_LV) return false
        if (levelFilter === 'notmax' && lvl >= MAX_LV) return false
        if (appearFilter === 'today' && !appearsToday(c.appearance_schedule)) return false
        if (appearFilter === 'now' && !appearsNow(c.appearance_schedule)) return false
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
        const first = items[0]
        const habUniform = items.every((i) => i.habitat === first.habitat)
        const foodKey = (i: Companion) => i.favorite_foods.join('|')
        const foodUniform = items.every((i) => foodKey(i) === foodKey(first))
        return {
          species,
          habUniform,
          habitat: habUniform ? (first?.habitat ?? '') : '',
          foods: foodUniform ? (first?.favorite_foods ?? []) : [],
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
  function setLevel(c: Companion, v: number) { c.friendship_level = Math.max(1, Math.min(5, v | 0)); save(c) }
  const lv = (c: Companion) => Math.max(1, c.friendship_level || 1)
</script>

<svelte:window onkeydown={onKey} />

<div class="head">
  <h1>オトモ図鑑</h1>
  <p class="sub">{ownedCount} / {all.length} 体 入手 ・ 種ごと（色は五十音順）。好物をあげて仲間に</p>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="名前・色・種で検索" bind:value={query} />
  <select bind:value={statusFilter} aria-label="入手状態で絞り込み">
    <option value="all">入手：すべて</option>
    <option value="owned">入手済み</option>
    <option value="unowned">未入手</option>
  </select>
  <select bind:value={levelFilter} aria-label="レベルで絞り込み">
    <option value="all">Lv：すべて</option>
    <option value="notmax">MAX未満</option>
    <option value="max">MAX（5）</option>
  </select>
  <select bind:value={appearFilter} aria-label="出現で絞り込み">
    <option value="all">出現：すべて</option>
    <option value="today">今日（{todayChar}）出現</option>
    <option value="now">今 出現中（{todayChar} {nowHour}時台）</option>
  </select>
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
              <span class="lv-badge" class:max={lv(c) >= MAX_LV}>{lv(c) >= MAX_LV ? 'MAX' : 'Lv' + lv(c)}</span>
            </div>
            <span class="label">
              <span class="sp">{c.gather_type}</span>
              <span class="col">{c.color_ja}</span>
            </span>
            {#if !g.habUniform && c.habitat}<span class="card-hab">📍{c.habitat}</span>{/if}
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
    <div class="sheet" role="dialog" aria-modal="true" aria-label={`${selected.gather_type} ${selected.color_ja}`} tabindex="-1" onclick={(e) => e.stopPropagation()}>
      <button class="close" onclick={() => (selected = null)} aria-label="閉じる">✕</button>
      <div class="sheet-top">
        <div class="big-thumb">
          {#if selected.icon_path && !broken.has(selected.id)}
            <img src={asset(selected.icon_path)} alt={selected.name_ja} onerror={() => selected && markBroken(selected.id)} />
          {:else}<span class="noimg"><span class="ph-mark">🐾</span></span>{/if}
        </div>
        <div>
          <h2>{selected.gather_type}</h2>
          <p class="colname">{selected.color_ja}</p>
          <p class="en">{selected.name_en}</p>
        </div>
      </div>
      <dl class="facts">
        <dt>生息地</dt><dd>{selected.habitat || '—'}</dd>
        <dt>好物</dt>
        <dd>{#if selected.favorite_foods.length}{#each selected.favorite_foods as f}<span class="chip">{f}</span>{/each}{:else}—{/if}</dd>
        <dt>出現時間</dt><dd class="sched">{selected.appearance_schedule || '—'}</dd>
        <dt>オトモLv</dt>
        <dd>
          <div class="stepper">
            <button onclick={() => selected && setLevel(selected, lv(selected) - 1)}>−</button>
            <span class="val">{lv(selected)}<span class="mx"> / 5</span></span>
            <button onclick={() => selected && setLevel(selected, lv(selected) + 1)}>＋</button>
          </div>
        </dd>
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
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 18px; font-size: 14px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 22px; }
  .search, .controls select { font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-surface); color: var(--c-ink); }
  .search { flex: 1 1 220px; }

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
  /* 全身の縦長画像が入りきるよう縦長の枠＋contain */
  .thumb { position: relative; width: 100%; aspect-ratio: 3 / 4; display: grid; place-items: center; background: var(--c-surface-2); border-radius: var(--radius-sm); overflow: hidden; }
  .thumb img { width: 100%; height: 100%; object-fit: contain; }
  .noimg { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; width: 100%; height: 100%; padding: 4px; text-align: center; background: linear-gradient(160deg, var(--c-surface-2), color-mix(in srgb, var(--c-accent-soft) 40%, var(--c-surface-2))); }
  .ph-mark { font-size: 22px; opacity: 0.5; }
  .ph-name { font-family: var(--font-display); font-weight: 600; font-size: 11px; color: var(--c-ink-soft); line-height: 1.1; }
  .own { position: absolute; top: 5px; right: 5px; width: 19px; height: 19px; border-radius: 50%; background: var(--c-accent); color: #fff; font-size: 11px; display: grid; place-items: center; }
  .lv-badge { position: absolute; bottom: 5px; left: 5px; background: color-mix(in srgb, var(--c-ink) 72%, transparent); color: #fff; font-size: 10px; font-weight: 700; line-height: 1; padding: 3px 5px; border-radius: 999px; font-variant-numeric: tabular-nums; }
  .lv-badge.max { background: var(--c-accent); }
  .label { display: flex; flex-direction: column; align-items: center; line-height: 1.2; }
  .label .sp { font-size: 11px; color: var(--c-ink-soft); }
  .label .col { font-family: var(--font-display); font-weight: 600; font-size: 13px; text-align: center; }
  .card-hab { font-size: 10px; color: var(--c-ink-soft); text-align: center; line-height: 1.1; margin-top: 1px; }
  .sched { font-size: 13px; line-height: 1.6; white-space: pre-line; }

  .chip { display: inline-block; margin: 2px 4px 2px 0; background: var(--c-surface-2); border: 1px solid var(--c-line); font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .muted { color: var(--c-ink-soft); }

  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(20,16,10,.45); display: grid; place-items: center; padding: 20px; }
  .sheet { position: relative; width: min(440px, 94vw); background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 22px; box-shadow: 0 24px 60px rgba(0,0,0,.3); }
  .close { position: absolute; top: 12px; right: 12px; background: var(--c-surface-2); border: 0; border-radius: 8px; width: 30px; height: 30px; color: var(--c-ink-soft); }
  .sheet-top { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
  .big-thumb { width: 96px; height: 128px; flex: none; background: var(--c-surface-2); border-radius: var(--radius-sm); display: grid; place-items: center; overflow: hidden; }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .sheet-top h2 { font-size: 22px; }
  .colname { font-family: var(--font-display); font-weight: 600; font-size: 16px; color: var(--c-accent-ink); margin: 2px 0 4px; }
  .en { color: var(--c-ink-soft); margin: 0; font-size: 12px; }
  .facts { display: grid; grid-template-columns: 80px 1fr; gap: 10px 12px; margin: 4px 0 4px; font-size: 14px; align-items: center; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .stepper { display: inline-flex; align-items: center; gap: 8px; }
  .stepper button { width: 30px; height: 30px; border-radius: 8px; border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 700; font-size: 16px; }
  .stepper .val { min-width: 54px; text-align: center; font-family: var(--font-display); font-weight: 700; font-size: 18px; }
  .mx { font-size: 12px; color: var(--c-ink-soft); font-weight: 400; }
  .own-tgl { padding: 8px 16px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .own-tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
