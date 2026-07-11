<script lang="ts">
  import type { Animal } from '../lib/schema'
  import { seedAll } from '../lib/db/seed'
  import { getAll, put } from '../lib/db/idb'
  import { asset } from '../lib/router'

  let all = $state<Animal[]>([])
  let loading = $state(true)

  async function load() {
    loading = true
    await seedAll()
    all = (await getAll<Animal>('animals')).sort((a, b) => a.name_en.localeCompare(b.name_en))
    loading = false
  }
  load()

  async function toggleFed(a: Animal) {
    a.fed_today = !a.fed_today
    await put('animals', $state.snapshot(a))
    all = [...all]
  }
  async function toggleUnlocked(a: Animal) {
    a.unlocked_as_companion = !a.unlocked_as_companion
    await put('animals', $state.snapshot(a))
    all = [...all]
  }
</script>

<div class="head">
  <h1>動物（クリッター）</h1>
  <p class="sub">
    {all.length} 種 ・ バイオームごとの野生の生き物。好物をあげて仲間（オトモ）にできる
  </p>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <div class="grid">
    {#each all as a (a.id)}
      <div class="card" class:done={a.unlocked_as_companion}>
        <div class="top">
          <div class="thumb">
            <span class="emoji">🐾</span>
            {#if a.icon_path}<img src={asset(a.icon_path)} alt={a.name_en} loading="lazy" onerror={(e) => e.currentTarget.remove()} />{/if}
          </div>
          <div class="titles">
            <span class="nm">{a.name_ja || a.name_en}</span>
            <span class="en">{a.name_en}</span>
          </div>
        </div>
        <dl class="facts">
          <dt>生息地</dt><dd>{a.habitat || '—'}</dd>
          <dt>好物</dt>
          <dd>
            {#if a.favorite_foods.length}
              {#each a.favorite_foods as f}<span class="chip">{f}</span>{/each}
            {:else}—{/if}
          </dd>
        </dl>
        <div class="btns">
          <button class="tgl" class:on={a.fed_today} onclick={() => toggleFed(a)}>
            {a.fed_today ? '✓ 今日あげた' : '餌やり記録'}
          </button>
          <button class="tgl" class:on={a.unlocked_as_companion} onclick={() => toggleUnlocked(a)}>
            {a.unlocked_as_companion ? '★ 仲間済み' : '仲間にした'}
          </button>
        </div>
      </div>
    {/each}
  </div>
  {#if all.length === 0}<p class="muted">データがありません。</p>{/if}
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 20px; font-size: 14px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--gap); }
  .card { background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 16px; box-shadow: 0 1px 0 var(--c-shadow); }
  .card.done { background: color-mix(in srgb, var(--c-accent-soft) 22%, var(--c-surface)); }
  .top { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
  .thumb { width: 64px; height: 64px; flex: none; background: var(--c-surface-2); border-radius: var(--radius-sm); display: grid; place-items: center; overflow: hidden; }
  .thumb img { width: 100%; height: 100%; object-fit: contain; }
  .emoji { font-size: 30px; }
  .titles { display: flex; flex-direction: column; }
  .nm { font-family: var(--font-display); font-weight: 600; font-size: 18px; }
  .en { font-size: 12px; color: var(--c-ink-soft); }
  .facts { display: grid; grid-template-columns: 56px 1fr; gap: 6px 10px; margin: 0 0 14px; font-size: 13px; }
  .facts dt { color: var(--c-ink-soft); }
  .facts dd { margin: 0; }
  .chip { display: inline-block; margin: 2px 4px 2px 0; background: var(--c-surface-2); border: 1px solid var(--c-line); font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .btns { display: flex; gap: 8px; }
  .tgl { flex: 1; padding: 8px; border-radius: var(--radius-sm); border: 1px solid var(--c-line); background: var(--c-surface-2); color: var(--c-ink); font-weight: 600; font-size: 13px; }
  .tgl.on { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
  .muted { color: var(--c-ink-soft); }
</style>
