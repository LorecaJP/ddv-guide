/* =========================================================================
   DDV 14カテゴリのスキーマ（引き継ぎ資料 2章に対応）
   凡例: 🔒 = Wiki等の外部データ由来（自動） / ✏️ = 自分専用・手動編集
   ※ 旧「動物」カテゴリは廃止し、オトモ図鑑（種ごと集約）に統合済み。
   ========================================================================= */

/** 1. キャラクター */
export interface Character {
  id: string
  name_ja: string
  name_en: string          // 🔒
  franchise: string        // 🔒 作品名
  unlock_condition: string // 🔒 要約（日本語）
  home_location: string    // 🔒
  skill_assigned: string   // ✏️ 割り当てロール（釣り/採掘 等）
  friendship_level: number // ✏️ フレンドレベル 0-10
  owned: boolean           // ✏️ 解放済みか
  icon_path: string        // 画像取得後に埋める
  memo: string             // ✏️
}

/** 2. 料理レシピ */
export interface Recipe {
  id: string
  name_ja: string
  name_en: string          // 🔒
  stars: number            // 🔒
  ingredients: string[]    // 🔒 材料（英語）
  ingredients_ja: string[] // 🔒 材料（日本語）
  category: string         // 🔒 前菜/主菜/デザート
  realm: string            // 🔒 コンテンツ（バレー/永遠の島/物語の谷/願い咲く牧場）
  sell_price_note: string  // 🔒
  icon_path: string        // 🔒 料理画像（mydreamlightvalley 由来）
  unlocked: boolean        // ✏️
  memo: string             // ✏️
}

/** 3. 素材 */
export interface Material {
  id: string
  name_ja: string
  name_en: string          // 🔒
  category: string         // 🔒
  obtain_method: string    // 🔒 要約
  used_in_recipes: string[]// 🔒 recipes と ID 連携
  unlocked: boolean        // ✏️ 解放済みか
  stock_count: number      // ✏️
  memo: string             // ✏️
}

/** 4. オトモ（コンパニオン） */
export interface Companion {
  id: string
  name_ja: string          // 🔒 種名（色名）
  name_en: string          // 🔒
  gather_type: string      // 🔒 種（日本語）
  color_ja: string         // 🔒 色名（日本語・並べ替え用）
  source: string           // 🔒 生息地（日本語）
  habitat: string          // 🔒 生息地（日本語・色違いごと）
  favorite_foods: string[] // 🔒 好物（日本語）
  appearance_schedule: string // 🔒 出現時間（曜日・時間）
  owned: boolean           // ✏️
  friendship_level: number // ✏️
  is_equipped: boolean     // ✏️
  icon_path: string        // ✏️
  memo: string             // ✏️
}

/** 5. クエスト */
export interface Quest {
  id: string
  name_ja: string
  type: string             // 🔒
  prerequisite: string     // 🔒
  reward: string           // 🔒
  completed: boolean       // ✏️
  completed_date: string   // ✏️ ISO日付
  memo: string             // ✏️
}

/** 6. イベント／スターパス */
export interface EventItem {
  id: string
  name_ja: string          // 🔒 gamepedia 突合
  period: string           // 🔒
  related_events: string[] // 🔒
  participated: boolean    // ✏️
  reward_progress: string  // ✏️
  memo: string             // ✏️
}

/** 7. （欠番）旧「農作物」カテゴリは廃止し、素材の種別(category)に統合済み。
       栽培場所は素材の obtain_method に取り込み済み。 */

/** 8. 施設 */
export interface Facility {
  id: string
  name_ja: string          // 🔒 gamepedia 突合
  type: string             // 🔒
  unlock_condition: string // 🔒
  restock_time: string     // 🔒
  note: string             // 🔒
  visited_today: boolean   // ✏️
  memo: string             // ✏️
}

/** 9. （欠番）旧「動物」カテゴリは廃止し、オトモ図鑑に統合済み */

/** 10. 不具合・バグ情報 */
export interface Bug {
  id: string
  title: string            // 🔒
  affected_platform: string// 🔒
  description: string      // 🔒 要約
  status: string           // 🔒
  reported_date: string    // 🔒
  source_url: string       // 🔒
  personal_encountered: boolean // ✏️
  workaround_tried: string      // ✏️
  memo: string             // ✏️
}

/** 11. アップデート履歴 */
export interface Update {
  id: string
  version: string          // 🔒
  release_date: string     // 🔒
  title: string            // 🔒
  summary: string          // 🔒 要約
  new_characters: string[] // 🔒 characters と ID 連携
  new_features: string[]   // 🔒
  bug_fixes: string[]      // 🔒
  source_url: string       // 🔒
  personal_notes: string   // ✏️
}

/** 12. 拡張パス */
export interface Expansion {
  id: string
  name_ja: string          // 🔒 gamepedia 突合
  release_date: string     // 🔒
  price: string            // 🔒
  included_realms: string[]// 🔒
  required_progress: string// 🔒
  owned: boolean           // ✏️
  progress_notes: string   // ✏️
}

/** 13. 売値一覧（エリア別） */
export interface Price {
  id: string
  item_id: string          // 🔒 他テーブルと ID 連携
  item_name: string        // 🔒
  sell_location: string    // 🔒
  base_price: number       // 🔒
  notes: string            // 🔒
  memo: string             // ✏️
}

/** 14. 小技・裏技（記事型） */
export interface Tip {
  id: string
  title: string            // 🔒
  category: string         // 🔒
  body_md: string          // 🔒 要約
  related_ids: string[]    // 🔒
  tried: boolean           // ✏️
  useful_rating: number    // ✏️ 0-5
  memo: string             // ✏️
}

/** 15. FAQ（記事型） */
export interface Faq {
  id: string
  question: string         // 🔒
  answer_md: string        // 🔒 要約
  category: string         // 🔒
  related_ids: string[]    // 🔒
  still_confused: boolean  // ✏️
  memo: string             // ✏️
}

/** 16. レルム進行ダッシュボード（集計ビュー・独立テーブルではない） */
export interface Dashboard {
  realms_unlocked_count: number   // ⚙️ 自動計算
  realms_total_count: number      // ⚙️ 自動計算
  current_dreamlight_balance: number // ✏️
  next_target_realm_id: string    // ✏️
  priority_reason: string         // ✏️
  last_updated: string            // ✏️
}

/** カテゴリのメタ情報（Hub のメニュー・ルーティング・表示種別に使用） */
export type DisplayType = 'image-grid' | 'table' | 'links' | 'dashboard'

export interface CategoryMeta {
  key: string          // ストア名 / ルート
  name_ja: string
  emoji: string        // 仮アイコン（後で画像アイコンに差し替え可）
  display: DisplayType
  implemented: boolean
}

/** 14カテゴリの定義（Hub & Spoke トップの一覧・表示出し分けの元） */
export const CATEGORIES: CategoryMeta[] = [
  { key: 'characters', name_ja: 'キャラクター', emoji: '🧑‍🎤', display: 'image-grid', implemented: true },
  { key: 'companions', name_ja: 'オトモ', emoji: '🐾', display: 'image-grid', implemented: true },
  { key: 'recipes', name_ja: '料理レシピ', emoji: '🍲', display: 'table', implemented: true },
  { key: 'materials', name_ja: '素材', emoji: '🪵', display: 'table', implemented: true },
  { key: 'prices', name_ja: '売値一覧', emoji: '💰', display: 'table', implemented: true },
  { key: 'quests', name_ja: 'クエスト', emoji: '📜', display: 'table', implemented: true },
  { key: 'facilities', name_ja: '施設', emoji: '🏛️', display: 'table', implemented: true },
  { key: 'events', name_ja: 'イベント／スターパス', emoji: '🎉', display: 'table', implemented: true },
  { key: 'expansions', name_ja: '拡張パス', emoji: '🗺️', display: 'table', implemented: true },
  { key: 'updates', name_ja: 'アップデート履歴', emoji: '🆕', display: 'table', implemented: true },
  { key: 'bugs', name_ja: '不具合・バグ情報', emoji: '🐛', display: 'links', implemented: true },
  { key: 'tips', name_ja: '小技・裏技', emoji: '💡', display: 'links', implemented: true },
  { key: 'faq', name_ja: 'FAQ', emoji: '❓', display: 'links', implemented: true },
  { key: 'dashboard', name_ja: 'レルム進行', emoji: '📊', display: 'dashboard', implemented: true },
]
