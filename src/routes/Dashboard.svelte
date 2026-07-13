<script lang="ts">
  import { seedAll } from '../lib/db/seed'
  import { getAll } from '../lib/db/idb'
  import { exportData, importData } from '../lib/db/transfer'

  const REALMS_TOTAL = 13 // Fandom Category:Realms

  // ---- データ移行（バックアップ / 復元）----
  let ioMsg = $state('')
  let ioBusy = $state(false)

  async function doExport() {
    ioBusy = true
    ioMsg = ''
    try {
      const data = await exportData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const day = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      a.href = url
      a.download = `ddv-guide-backup-${day}.json`
      a.click()
      URL.revokeObjectURL(url)
      const total = Object.values(data.stores).reduce((n, arr) => n + arr.length, 0)
      ioMsg = `書き出しました（${total} 件）。このファイルを新しい端末で読み込んでください。`
    } catch (e) {
      ioMsg = '書き出しに失敗しました: ' + (e instanceof Error ? e.message : String(e))
    } finally {
      ioBusy = false
    }
  }

  async function onImportFile(e: Event) {
    const input = e.currentTarget as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return
    if (!confirm('このバックアップの内容を、いまの端末のデータに上書き適用します。よろしいですか？')) {
      input.value = ''
      return
    }
    ioBusy = true
    ioMsg = ''
    try {
      const json = JSON.parse(await file.text())
      const res = await importData(json)
      ioMsg = `復元しました（${res.stores} カテゴリ・${res.rows} 件）。再読み込みします…`
      setTimeout(() => location.reload(), 900)
    } catch (e) {
      ioMsg = '読み込みに失敗しました: ' + (e instanceof Error ? e.message : String(e))
    } finally {
      ioBusy = false
      input.value = ''
    }
  }

  let loading = $state(true)
  let stats = $state<{ label: string; done: number; total: number; key: string }[]>([])

  // ローカル保存する ✏️ フィールド
  let dreamlight = $state(0)
  let realmsUnlocked = $state(0)
  let nextTarget = $state('')
  let priority = $state('')

  function loadLocal() {
    try {
      const s = JSON.parse(localStorage.getItem('ddv-dashboard') ?? '{}')
      dreamlight = s.dreamlight ?? 0
      realmsUnlocked = s.realmsUnlocked ?? 0
      nextTarget = s.nextTarget ?? ''
      priority = s.priority ?? ''
    } catch {}
  }
  function saveLocal() {
    localStorage.setItem(
      'ddv-dashboard',
      JSON.stringify({ dreamlight, realmsUnlocked, nextTarget, priority }),
    )
  }

  async function load() {
    loading = true
    loadLocal()
    await seedAll()
    const [chars, comps, recipes, quests] = await Promise.all([
      getAll<any>('characters'),
      getAll<any>('companions'),
      getAll<any>('recipes'),
      getAll<any>('quests'),
    ])
    stats = [
      { key: 'characters', label: 'キャラクター 解放', done: chars.filter((c) => c.owned).length, total: chars.length },
      { key: 'companions', label: 'オトモ なかま', done: comps.filter((c) => c.owned).length, total: comps.length },
      { key: 'recipes', label: '料理レシピ 解放', done: recipes.filter((r) => r.unlocked).length, total: recipes.length },
      { key: 'quests', label: 'クエスト 達成', done: quests.filter((q) => q.completed).length, total: quests.length },
    ]
    loading = false
  }
  load()

  const pct = (d: number, t: number) => (t ? Math.round((d / t) * 100) : 0)
</script>

<div class="head">
  <h1>📊 レルム進行ダッシュボード</h1>
  <p class="sub">集計ビュー（進捗は各カテゴリの✏️から自動集計。数値は手入力）</p>
</div>

{#if loading}
  <p class="muted">読み込み中…</p>
{:else}
  <div class="cards">
    <div class="card big">
      <span class="lbl">レルム解放</span>
      <div class="realm">
        <input type="number" min="0" max={REALMS_TOTAL} bind:value={realmsUnlocked} onchange={saveLocal} />
        <span class="of">/ {REALMS_TOTAL}</span>
      </div>
      <div class="bar"><div class="fill" style="width:{pct(realmsUnlocked, REALMS_TOTAL)}%"></div></div>
    </div>
    <div class="card big">
      <span class="lbl">ドリームライト残高</span>
      <input class="dl" type="number" min="0" bind:value={dreamlight} onchange={saveLocal} />
    </div>
  </div>

  <div class="grid">
    {#each stats as s}
      <div class="card">
        <span class="lbl">{s.label}</span>
        <span class="num">{s.done}<span class="tot"> / {s.total}</span></span>
        <div class="bar"><div class="fill" style="width:{pct(s.done, s.total)}%"></div></div>
        <span class="pc">{pct(s.done, s.total)}%</span>
      </div>
    {/each}
  </div>

  <div class="card wide">
    <label class="field">
      <span class="lbl">次に狙うレルム</span>
      <input type="text" bind:value={nextTarget} onchange={saveLocal} placeholder="例: ムーランのレルム" />
    </label>
    <label class="field">
      <span class="lbl">優先理由・メモ</span>
      <textarea rows="2" bind:value={priority} onchange={saveLocal} placeholder="なぜそこを優先するか"></textarea>
    </label>
  </div>

  <div class="card wide io-card">
    <span class="lbl">データのバックアップ / 復元</span>
    <p class="io-note">
      進捗（解放・レベル・メモ・所持など）はこの端末のブラウザに保存されます。機種変更や別ブラウザに移すときは、書き出したファイルを新しい端末で読み込んでください。
    </p>
    <div class="io-row">
      <button class="io-btn" onclick={doExport} disabled={ioBusy}>⬇ 書き出し（バックアップ）</button>
      <label class="io-btn file" class:disabled={ioBusy}>
        ⬆ 読み込み（復元）
        <input type="file" accept="application/json,.json" onchange={onImportFile} disabled={ioBusy} hidden />
      </label>
    </div>
    {#if ioMsg}<p class="io-msg">{ioMsg}</p>{/if}
  </div>
{/if}

<style>
  .head h1 { font-size: clamp(24px, 3.4vw, 34px); }
  .sub { color: var(--c-ink-soft); margin: 6px 0 20px; font-size: 14px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--gap); margin-bottom: var(--gap); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: var(--gap); margin-bottom: var(--gap); }
  .card { background: var(--c-surface); border: 1px solid var(--c-line); border-radius: var(--radius); padding: 16px 18px; box-shadow: 0 1px 0 var(--c-shadow); }
  .card.big { display: flex; flex-direction: column; gap: 10px; }
  .lbl { font-size: 12px; color: var(--c-ink-soft); font-weight: 600; }
  .num { font-family: var(--font-display); font-size: 28px; font-weight: 700; display: block; margin: 6px 0; }
  .tot { font-size: 15px; color: var(--c-ink-soft); font-weight: 400; }
  .realm { display: flex; align-items: baseline; gap: 8px; }
  .realm input { width: 64px; font-family: var(--font-display); font-size: 28px; font-weight: 700; background: none; border: 0; border-bottom: 2px solid var(--c-line); color: var(--c-ink); }
  .of { color: var(--c-ink-soft); }
  .dl { width: 100%; font-family: var(--font-display); font-size: 26px; font-weight: 700; background: none; border: 0; border-bottom: 2px solid var(--c-line); color: var(--c-accent-ink); margin-top: 6px; }
  .bar { height: 7px; background: var(--c-surface-2); border-radius: 999px; overflow: hidden; }
  .fill { height: 100%; background: var(--c-accent); border-radius: 999px; }
  .pc { font-size: 12px; color: var(--c-ink-soft); margin-top: 4px; display: inline-block; }
  .wide { display: grid; gap: 14px; }
  .field { display: flex; flex-direction: column; gap: 6px; }
  .field input, .field textarea { font-family: var(--font-body); padding: 9px 12px; border: 1px solid var(--c-line); border-radius: var(--radius-sm); background: var(--c-bg); color: var(--c-ink); resize: vertical; }
  .muted { color: var(--c-ink-soft); }

  .io-card { gap: 12px; }
  .io-note { color: var(--c-ink-soft); font-size: 13px; margin: 2px 0 0; line-height: 1.7; }
  .io-row { display: flex; flex-wrap: wrap; gap: 10px; }
  .io-btn {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: var(--font-body); font-weight: 700; font-size: 14px;
    padding: 10px 16px; border-radius: var(--radius-sm);
    border: 1px solid var(--c-accent); background: var(--c-accent); color: #fff;
  }
  .io-btn.file { background: var(--c-surface-2); color: var(--c-ink); border-color: var(--c-line); cursor: pointer; }
  .io-btn:disabled, .io-btn.disabled { opacity: 0.55; pointer-events: none; }
  .io-msg { font-size: 13px; color: var(--c-accent-ink); margin: 2px 0 0; }
</style>
