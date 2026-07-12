<script lang="ts">
  import type { Character } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { asset } from '../lib/router'

  let all = $state<Character[]>([])
  let loading = $state(true)
  let query = $state('')
  let statusFilter = $state('all') // 'all' | 'owned' | 'unowned'
  let levelFilter = $state('all') // 'all' | 'max' | 'notmax'
  let roleFilter = $state('all') // 'all' | '' (未設定) | ロール名
  const MAX_LV = 10
  let selected = $state<Character | null>(null)
  let broken = $state<Set<string>>(new Set())
  const markBroken = (id: string) => (broken = new Set(broken).add(id))

  // 旧ロール名 → 新名称（ユーザーの割り当てを保持するための移行）
  const ROLE_MIGRATE: Record<string, string> = { 釣り: '魚釣り', 採取: '収集', 発掘: '土掘り' }

  async function load() {
    loading = true
    await seedAll()
    const rows = await getAll<Character>('characters')
    for (const c of rows) {
      const mapped = ROLE_MIGRATE[c.skill_assigned]
      if (mapped) {
        c.skill_assigned = mapped
        await put('characters', $state.snapshot(c))
      }
    }
    all = rows.sort((a, b) => a.name_ja.localeCompare(b.name_ja, 'ja'))
    loading = false
  }
  load()

  // 作品ごとにまとめ、作品内は五十音順。作品は五十音順。
  const groups = $derived(
    (() => {
      const filtered = all.filter((c) => {
        if (statusFilter === 'owned' && !c.owned) return false
        if (statusFilter === 'unowned' && c.owned) return false
        const lvl = Math.max(1, c.friendship_level || 1)
        if (levelFilter === 'max' && lvl < MAX_LV) return false
        if (levelFilter === 'notmax' && lvl >= MAX_LV) return false
        if (roleFilter === '') {
          if (c.skill_assigned) return false // 未設定のみ
        } else if (roleFilter !== 'all') {
          if (c.skill_assigned !== roleFilter) return false
        }
        if (query) {
          const q = query.toLowerCase()
          if (!`${c.name_ja}${c.name_en}`.toLowerCase().includes(q)) return false
        }
        return true
      })
      const map = new Map<string, Character[]>()
      for (const c of filtered) {
        if (!map.has(c.franchise)) map.set(c.franchise, [])
        map.get(c.franchise)!.push(c)
      }
      const out = [...map.entries()].map(([franchise, items]) => {
        items.sort((a, b) => a.name_ja.localeCompare(b.name_ja, 'ja'))
        return { franchise, owned: items.filter((i) => i.owned).length, items }
      })
      out.sort((a, b) => a.franchise.localeCompare(b.franchise, 'ja'))
      return out
    })(),
  )

  const ownedCount = $derived(all.filter((c) => c.owned).length)

  // DDV の割り当てロール（得意分野・整理用タグ。DLC分の時空歪曲/紙精捕獲を含む）
  const SKILLS = ['園芸', '魚釣り', '採掘', '土掘り', '収集', '時空歪曲', '紙精捕獲']

  async function save(c: Character) {
    await put('characters', $state.snapshot(c))
    all = [...all] // 再描画トリガ
    if (selected?.id === c.id) selected = c
  }
  function toggleOwned(c: Character) {
    c.owned = !c.owned
    save(c)
  }
  function setSkill(c: Character, v: string) {
    c.skill_assigned = v
    save(c)
  }
  function setLevel(c: Character, v: number) {
    c.friendship_level = Math.max(1, Math.min(10, v | 0))
    save(c)
  }
</script>

<div class="head">
  <div>
    <h1>キャラクター図鑑</h1>
    <p class="sub">{ownedCount} / {all.length} 体 解放済み・画像 {all.filter((c) => c.icon_path).length} 体分</p>
  </div>
</div>

<div class="controls">
  <input class="search" type="search" placeholder="名前で検索（日本語 / 英語）" bind:value={query} />
  <select bind:value={roleFilter} aria-label="割り当てロールで絞り込み">
    <option value="all">すべてのロール</option>
    <option value="">未設定</option>
    {#each SKILLS as s}<option value={s}>{s}</option>{/each}
  </select>
  <select bind:value={statusFilter} aria-label="解放状態で絞り込み">
    <option value="all">解放：すべて</option>
    <option value="owned">解放済み</option>
    <option value="unowned">未解放</option>
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
  {#each groups as g (g.franchise)}
    <section class="franchise">
      <div class="fr-head">
        <h2>{g.franchise}<span class="cnt">{g.owned}/{g.items.length}</span></h2>
      </div>
      <div class="zukan">
        {#each g.items as c (c.id)}
          <button class="card" class:dim={!c.owned} onclick={() => (selected = c)}>
            <div class="thumb">
              {#if c.icon_path && !broken.has(c.id)}
                <img src={asset(c.icon_path)} alt={c.name_ja} loading="lazy" onerror={() => markBroken(c.id)} />
              {:else}
                <span class="noimg"><span class="ph-mark">👤</span><span class="ph-name">{c.name_ja}</span></span>
              {/if}
              {#if c.owned}<span class="own">✓</span>{/if}
            </div>
            <span class="nm">{c.name_ja}</span>
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
          {:else}<span class="noimg"><span class="ph-mark">👤</span></span>{/if}
        </div>
        <div>
          <h2>{selected.name_ja}</h2>
          <p class="en">{selected.name_en}</p>
          <p class="chip">{selected.franchise}</p>
        </div>
      </div>
      <dl class="facts">
        <dt>解放条件</dt><dd>{selected.unlock_condition || '（未登録）'}</dd>
        <dt>居住地</dt><dd>{selected.home_location || '（未登録）'}</dd>
        <dt>割り当てロール</dt>
        <dd>
          <select
            class="skill"
            value={selected.skill_assigned}
            onchange={(e) => selected && setSkill(selected, e.currentTarget.value)}
          >
            <option value="">未設定</option>
            {#each SKILLS as s}<option value={s}>{s}</option>{/each}
          </select>
        </dd>
        <dt>フレンドLv</dt>
        <dd>
          <div class="stepper">
            <button onclick={() => selected && setLevel(selected, Math.max(1, selected.friendship_level || 1) - 1)} aria-label="下げる">−</button>
            <span class="lv">{Math.max(1, selected.friendship_level || 1)}<span class="lvmax"> / 10</span></span>
            <button onclick={() => selected && setLevel(selected, Math.max(1, selected.friendship_level || 1) + 1)} aria-label="上げる">＋</button>
          </div>
        </dd>
        <dt>メモ</dt><dd>{selected.memo || '—'}</dd>
        <dt>解放</dt>
        <dd>
          <button class="own-tgl" class:on={selected.owned} onclick={() => selected && toggleOwned(selected)}>
            {selected.owned ? '✓ 解放済み' : '未解放'}
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

  .franchise { margin-bottom: 26px; }
  .fr-head { border-bottom: 2px solid var(--c-accent-soft); padding-bottom: 8px; margin-bottom: 14px; }
  .fr-head h2 { font-size: 20px; display: flex; align-items: baseline; gap: 10px; }
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
    width: 104px; height: 104px; flex: none;
    background: var(--c-surface-2); border-radius: var(--radius-sm);
    display: grid; place-items: center; overflow: hidden;
  }
  .big-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .sheet-top h2 { font-size: 22px; }
  .en { color: var(--c-ink-soft); margin: 3px 0 8px; font-size: 13px; }
  .chip {
    display: inline-block; margin: 0;
    background: var(--c-accent-soft); color: var(--c-accent-ink);
    font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  }
  .facts { display: grid; grid-template-columns: 96px 1fr; gap: 10px 12px; margin: 4px 0 18px; font-size: 14px; align-items: center; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .skill {
    font-family: var(--font-body); padding: 7px 10px; border: 1px solid var(--c-line);
    border-radius: var(--radius-sm); background: var(--c-bg); color: var(--c-ink); font-size: 14px; min-width: 120px;
  }
  .stepper { display: inline-flex; align-items: center; gap: 8px; }
  .stepper button {
    width: 30px; height: 30px; border-radius: 8px; border: 1px solid var(--c-line);
    background: var(--c-surface-2); color: var(--c-ink); font-weight: 700; font-size: 16px;
  }
  .lv { min-width: 56px; text-align: center; font-family: var(--font-display); font-weight: 700; font-size: 18px; }
  .lvmax { font-size: 12px; color: var(--c-ink-soft); font-weight: 400; }
  .own-tgl { padding: 8px 16px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; }
  .own-tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
