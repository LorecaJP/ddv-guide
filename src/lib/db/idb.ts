/* =========================================================================
   最小限の IndexedDB ラッパー（依存パッケージなし）
   - 1 DB / 各カテゴリ = 1 objectStore（keyPath: 'id'）
   - 🔒フィールドは seed 時に投入、✏️フィールドはユーザー編集で上書き保存
   ========================================================================= */
import { CATEGORIES } from '../schema'

const DB_NAME = 'ddv-guide'
// ⚠️ マイグレーション規約:
//   objectStore は onupgradeneeded でしか作れない。CATEGORIES に新カテゴリ（=新ストア）を
//   追加したら、この DB_VERSION を必ず +1 すること。上げないと、既にDBを持つ端末では
//   onupgradeneeded が再発火せず新ストアが作られない → seed/読み込みが例外になる。
//   （過去に「動物」ストアが未生成のまま seed され初回ロードが固まる不具合の原因がこれ）
const DB_VERSION = 4 // v2: crafting 追加 / v3: flowers・hourglass 追加 / v4: mounts（騎乗動物）追加

// dashboard は集計ビューなので独立ストアは持たない
export const STORE_KEYS = CATEGORIES.filter((c) => c.key !== 'dashboard').map((c) => c.key)

let dbPromise: Promise<IDBDatabase> | null = null

export function openDB(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      for (const key of STORE_KEYS) {
        if (!db.objectStoreNames.contains(key)) {
          db.createObjectStore(key, { keyPath: 'id' })
        }
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
  return dbPromise
}

function tx(db: IDBDatabase, store: string, mode: IDBTransactionMode) {
  return db.transaction(store, mode).objectStore(store)
}

export async function getAll<T>(store: string): Promise<T[]> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const req = tx(db, store, 'readonly').getAll()
    req.onsuccess = () => resolve(req.result as T[])
    req.onerror = () => reject(req.error)
  })
}

export async function get<T>(store: string, id: string): Promise<T | undefined> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const req = tx(db, store, 'readonly').get(id)
    req.onsuccess = () => resolve(req.result as T | undefined)
    req.onerror = () => reject(req.error)
  })
}

export async function put<T>(store: string, value: T): Promise<void> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const req = tx(db, store, 'readwrite').put(value)
    req.onsuccess = () => resolve()
    req.onerror = () => reject(req.error)
  })
}

export async function del(store: string, id: string): Promise<void> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const req = tx(db, store, 'readwrite').delete(id)
    req.onsuccess = () => resolve()
    req.onerror = () => reject(req.error)
  })
}

export async function count(store: string): Promise<number> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const req = tx(db, store, 'readonly').count()
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function bulkPut<T>(store: string, values: T[]): Promise<void> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, 'readwrite')
    const os = t.objectStore(store)
    for (const v of values) os.put(v)
    t.oncomplete = () => resolve()
    t.onerror = () => reject(t.error)
  })
}
