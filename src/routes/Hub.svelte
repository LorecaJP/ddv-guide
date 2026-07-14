<script lang="ts">
  import { CATEGORIES } from '../lib/schema'
  import { navigate } from '../lib/router'
  import { seedAll } from '../lib/db/seed'
  import { getAll } from '../lib/db/idb'

  // カテゴリごとの「達成」判定フィールド（真偽で数える）。無いものは件数のみ表示。
  const PROGRESS_FIELD: Record<string, string> = {
    characters: 'owned',
    companions: 'owned',
    recipes: 'unlocked',
    materials: 'unlocked',
    quests: 'completed',
    events: 'participated',
    expansions: 'owned',
  }

  type Stat = { total: number; done: number | null }
  let stats = $state<Record<string, Stat>>({})

  async function load() {
    await seedAll()
    const keys = CATEGORIES.filter((c) => c.key !== 'dashboard').map((c) => c.key)
    const entries = await Promise.all(
      keys.map(async (k): Promise<[string, Stat]> => {
        const rows = await getAll<Record<string, any>>(k)
        const f = PROGRESS_FIELD[k]
        return [k, { total: rows.length, done: f ? rows.filter((r) => r[f]).length : null }]
      }),
    )
    stats = Object.fromEntries(entries)
  }
  load()

  const pct = (s: Stat) => (s.total ? Math.round(((s.done ?? 0) / s.total) * 100) : 0)
</script>

<section class="hero">
  <h1>どこから見る？</h1>
  <p>14カテゴリのメニュー。画像で見分けるものは図鑑グリッド、数値ものは表で表示します。</p>
</section>

<div class="grid">
  {#each CATEGORIES as c (c.key)}
    {@const s = stats[c.key]}
    <button class="tile" class:soon={!c.implemented} onclick={() => navigate(c.key)}>
      <span class="emoji">{c.emoji}</span>
      <span class="label">{c.name_ja}</span>
      <span class="type">{c.display === 'image-grid' ? '図鑑' : c.display === 'table' ? '一覧表' : c.display === 'links' ? 'リンク集' : 'ダッシュボード'}</span>
      {#if s}
        {#if s.done !== null}
          <span class="prog">
            <span class="pnum">{s.done}<span class="ptot"> / {s.total}</span></span>
            <span class="bar"><span class="fill" style="width:{pct(s)}%"></span></span>
          </span>
        {:else if s.total > 0}
          <span class="count">{s.total} 件</span>
        {/if}
      {/if}
      {#if !c.implemented}<span class="badge">準備中</span>{/if}
    </button>
  {/each}
</div>

<style>
  .hero { margin: 6px 0 26px; }
  .hero h1 { font-size: clamp(28px, 4vw, 40px); }
  .hero p { color: var(--c-ink-soft); margin: 8px 0 0; max-width: 46ch; }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--gap);
  }
  .tile {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 18px 16px 16px;
    background: var(--c-surface);
    border: 1px solid var(--c-line);
    border-radius: var(--radius);
    box-shadow: 0 1px 0 var(--c-shadow);
    text-align: left;
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
  }
  .tile:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px var(--c-shadow);
    border-color: var(--c-accent);
  }
  .tile .emoji { font-size: 30px; line-height: 1; }
  .tile .label { font-family: var(--font-display); font-weight: 600; font-size: 17px; }
  .tile .type { font-size: 12px; color: var(--c-ink-soft); }
  .tile.soon { opacity: 0.72; }

  .prog { width: 100%; margin-top: 4px; display: flex; flex-direction: column; gap: 4px; }
  .pnum { font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums; color: var(--c-ink); }
  .ptot { font-weight: 400; color: var(--c-ink-soft); }
  .bar { height: 5px; width: 100%; background: var(--c-surface-2); border-radius: 999px; overflow: hidden; }
  .fill { display: block; height: 100%; background: var(--c-accent); border-radius: 999px; }
  .count { margin-top: 2px; font-size: 12px; color: var(--c-ink-soft); font-variant-numeric: tabular-nums; }

  .badge {
    position: absolute;
    top: 12px;
    right: 12px;
    font-size: 10px;
    font-weight: 700;
    color: var(--c-accent-ink);
    background: var(--c-accent-soft);
    padding: 2px 7px;
    border-radius: 999px;
  }
</style>
