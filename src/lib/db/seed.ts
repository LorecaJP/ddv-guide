/* =========================================================================
   シード: 静的JSON（🔒データ）を IndexedDB に投入。
   既存レコードがある場合は ✏️（自分専用）フィールドを保持したまま
   🔒（外部データ）フィールドだけ最新化するマージを行う。
   ========================================================================= */
import { getAll, bulkPut } from './idb'

/* データ（🔒静的JSON）は動的 import で個別チャンクに分割する。
   これにより初期ロードの JS はアプリ本体だけになり（データ計 約0.5MB は別チャンク）、
   アプリ更新時にデータチャンクのキャッシュが再利用できる。
   dist の *.js は PWA(workbox) がプリキャッシュするためオフラインでも従来どおり動く。 */
const SEED_LOADERS: Record<string, () => Promise<{ default: Record<string, any>[] }>> = {
  characters: () => import('../data/characters.json'),
  recipes: () => import('../data/recipes.json'),
  materials: () => import('../data/materials.json'),
  companions: () => import('../data/companions.json'),
  crops: () => import('../data/crops.json'),
  prices: () => import('../data/prices.json'),
  quests: () => import('../data/quests.json'),
  facilities: () => import('../data/facilities.json'),
  events: () => import('../data/events.json'),
  expansions: () => import('../data/expansions.json'),
  updates: () => import('../data/updates.json'),
  tips: () => import('../data/tips.json'),
  faq: () => import('../data/faq.json'),
  bugs: () => import('../data/bugs.json'),
}

// 各カテゴリの ✏️ フィールド（マージ時に既存値を優先して保持する）
const EDITABLE: Record<string, string[]> = {
  characters: ['skill_assigned', 'friendship_level', 'owned', 'memo'],
  recipes: ['unlocked', 'memo'],
  materials: ['unlocked', 'stock_count', 'memo'],
  companions: ['owned', 'friendship_level', 'is_equipped', 'memo'],
  crops: ['planted_count', 'harvested_total', 'memo'],
  prices: ['memo'],
  quests: ['completed', 'completed_date', 'memo'],
  facilities: ['visited_today', 'memo'],
  events: ['participated', 'reward_progress', 'memo'],
  expansions: ['owned', 'progress_notes'],
  updates: ['personal_notes'],
  tips: ['tried', 'useful_rating', 'memo'],
  faq: ['still_confused', 'memo'],
  bugs: ['personal_encountered', 'workaround_tried', 'memo'],
}

async function seedStore(store: string): Promise<void> {
  const editable = EDITABLE[store] ?? []
  const seed = (await SEED_LOADERS[store]()).default
  const existing = await getAll<Record<string, any>>(store)
  const byId = new Map(existing.map((r) => [r.id, r]))
  const merged = seed.map((row) => {
    const prev = byId.get(row.id)
    if (!prev) return row
    // 🔒はseed優先で更新、✏️は既存を保持
    const out = { ...row }
    for (const k of editable) {
      if (prev[k] !== undefined) out[k] = prev[k]
    }
    return out
  })
  await bulkPut(store, merged)
}

let seeded = false

/** アプリ起動時に1回呼ぶ。全カテゴリの静的データを投入。 */
export async function seedAll(): Promise<void> {
  if (seeded) return
  await Promise.all(Object.keys(SEED_LOADERS).map((store) => seedStore(store)))
  seeded = true
}
