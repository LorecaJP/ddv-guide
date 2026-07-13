/* =========================================================================
   データ移行（バックアップ / 復元）
   -------------------------------------------------------------------------
   進捗などの ✏️（自分用）フィールドは IndexedDB に端末ローカル保存される。
   機種変更・別ブラウザ・キャッシュ削除で消えるため、書き出し/読み込みで移行する。
   - 書き出し: 全ストアの ✏️ フィールド(+id)＋ダッシュボードの localStorage をJSON化
   - 読み込み: id 一致で ✏️ のみ上書きマージ（🔒データは触らない＝seed更新に強い）
   ========================================================================= */
import { STORE_KEYS, getAll, bulkPut } from './idb'
import { EDITABLE, seedAll } from './seed'

const DASH_KEY = 'ddv-dashboard'
const FORMAT = 'ddv-guide'
const FORMAT_VERSION = 1

export interface Backup {
  app: string
  version: number
  exported_at: string
  dashboard: Record<string, unknown>
  stores: Record<string, Record<string, any>[]>
}

/** 現在の端末の ✏️ データを1つの JSON にまとめて返す。 */
export async function exportData(): Promise<Backup> {
  await seedAll()
  const stores: Record<string, Record<string, any>[]> = {}
  for (const store of STORE_KEYS) {
    const editable = EDITABLE[store] ?? []
    if (editable.length === 0) continue
    const rows = await getAll<Record<string, any>>(store)
    stores[store] = rows.map((r) => {
      const out: Record<string, any> = { id: r.id }
      for (const k of editable) out[k] = r[k]
      return out
    })
  }
  let dashboard: Record<string, unknown> = {}
  try {
    dashboard = JSON.parse(localStorage.getItem(DASH_KEY) ?? '{}')
  } catch {}
  return {
    app: FORMAT,
    version: FORMAT_VERSION,
    exported_at: new Date().toISOString(),
    dashboard,
    stores,
  }
}

export interface ImportResult {
  stores: number
  rows: number
}

/** バックアップJSONを読み込み、id 一致で ✏️ フィールドのみ上書きマージする。 */
export async function importData(data: any): Promise<ImportResult> {
  if (!data || data.app !== FORMAT || typeof data.stores !== 'object') {
    throw new Error('このファイルは DDV 攻略メモのバックアップではありません。')
  }
  await seedAll() // 先に 🔒データを投入して各レコードを用意しておく
  let storesApplied = 0
  let rowsApplied = 0
  for (const store of STORE_KEYS) {
    const incoming = data.stores[store]
    if (!Array.isArray(incoming) || incoming.length === 0) continue
    const editable = EDITABLE[store] ?? []
    if (editable.length === 0) continue
    const existing = await getAll<Record<string, any>>(store)
    const byId = new Map<string, any>(incoming.map((r: any) => [r.id, r]))
    let touched = false
    const merged = existing.map((row) => {
      const inc = byId.get(row.id)
      if (!inc) return row
      const out = { ...row }
      for (const k of editable) if (k in inc) out[k] = inc[k]
      touched = true
      rowsApplied++
      return out
    })
    if (touched) {
      await bulkPut(store, merged)
      storesApplied++
    }
  }
  if (data.dashboard && typeof data.dashboard === 'object') {
    localStorage.setItem(DASH_KEY, JSON.stringify(data.dashboard))
  }
  return { stores: storesApplied, rows: rowsApplied }
}
