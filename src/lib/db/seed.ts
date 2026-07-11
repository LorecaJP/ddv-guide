/* =========================================================================
   シード: 静的JSON（🔒データ）を IndexedDB に投入。
   既存レコードがある場合は ✏️（自分専用）フィールドを保持したまま
   🔒（外部データ）フィールドだけ最新化するマージを行う。
   ========================================================================= */
import charactersSeed from '../data/characters.json'
import recipesSeed from '../data/recipes.json'
import materialsSeed from '../data/materials.json'
import companionsSeed from '../data/companions.json'
import animalsSeed from '../data/animals.json'
import cropsSeed from '../data/crops.json'
import pricesSeed from '../data/prices.json'
import questsSeed from '../data/quests.json'
import facilitiesSeed from '../data/facilities.json'
import eventsSeed from '../data/events.json'
import expansionsSeed from '../data/expansions.json'
import updatesSeed from '../data/updates.json'
import tipsSeed from '../data/tips.json'
import faqSeed from '../data/faq.json'
import bugsSeed from '../data/bugs.json'
import { getAll, bulkPut } from './idb'

// 各カテゴリの ✏️ フィールド（マージ時に既存値を優先して保持する）
const EDITABLE: Record<string, string[]> = {
  characters: ['skill_assigned', 'owned', 'memo'],
  recipes: ['unlocked', 'memo'],
  materials: ['stock_count', 'memo'],
  companions: ['owned', 'friendship_level', 'is_equipped', 'memo'],
  animals: ['fed_today', 'unlocked_as_companion', 'memo'],
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

async function seedStore(store: string, seed: Record<string, any>[]): Promise<void> {
  const editable = EDITABLE[store] ?? []
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
  await Promise.all([
    seedStore('characters', charactersSeed as any[]),
    seedStore('recipes', recipesSeed as any[]),
    seedStore('materials', materialsSeed as any[]),
    seedStore('companions', companionsSeed as any[]),
    seedStore('animals', animalsSeed as any[]),
    seedStore('crops', cropsSeed as any[]),
    seedStore('prices', pricesSeed as any[]),
    seedStore('quests', questsSeed as any[]),
    seedStore('facilities', facilitiesSeed as any[]),
    seedStore('events', eventsSeed as any[]),
    seedStore('expansions', expansionsSeed as any[]),
    seedStore('updates', updatesSeed as any[]),
    seedStore('tips', tipsSeed as any[]),
    seedStore('faq', faqSeed as any[]),
    seedStore('bugs', bugsSeed as any[]),
  ])
  seeded = true
}
