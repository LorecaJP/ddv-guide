/* =========================================================================
   設定駆動テーブルの列定義。カテゴリごとに columns を宣言するだけで
   DataTable.svelte が描画・ソート・検索・編集(IndexedDB永続化)を行う。
   ========================================================================= */

export type ColKind = 'title' | 'text' | 'chips' | 'number' | 'stars' | 'toggle' | 'stepper' | 'link'

export interface Column {
  key: string
  label: string
  kind: ColKind
  sortable?: boolean
  primaryKey?: string // kind='title' の主表示キー
  subKey?: string // kind='title' の副表示キー
  onLabel?: string // kind='toggle' のON表示
  offLabel?: string // kind='toggle' のOFF表示
  min?: number // stepper
  max?: number
  align?: 'left' | 'right'
  linkLabel?: string // kind='link' のボタン文言
}

export interface TableConfig {
  columns: Column[]
  searchKeys: string[]
  editable: string[]
  defaultSort?: { key: string; dir: 'asc' | 'desc' }
  note?: string
}

export const TABLE_CONFIG: Record<string, TableConfig> = {
  crops: {
    columns: [
      { key: 'name', label: '作物名', kind: 'title', primaryKey: 'name_ja', subKey: 'name_en', sortable: true },
      { key: 'category', label: '種別', kind: 'text' },
      { key: 'grow_area', label: '栽培/入手', kind: 'text' },
      { key: 'used_in_recipes', label: '使用レシピ', kind: 'number', sortable: true, align: 'right' },
      { key: 'planted_count', label: '植えた', kind: 'stepper', min: 0, align: 'right' },
      { key: 'harvested_total', label: '収穫累計', kind: 'stepper', min: 0, align: 'right' },
    ],
    searchKeys: ['name_ja', 'name_en'],
    editable: ['planted_count', 'harvested_total', 'memo'],
    note: 'materials の栽培アイテムから導出。使用レシピは料理との ID 連携。',
  },
  prices: {
    columns: [
      { key: 'item_name', label: 'アイテム', kind: 'text', sortable: true },
      { key: 'base_price', label: '売値', kind: 'number', sortable: true, align: 'right' },
      { key: 'sell_location', label: '売却先', kind: 'text' },
      { key: 'notes', label: '備考', kind: 'text' },
    ],
    searchKeys: ['item_name'],
    editable: ['memo'],
    defaultSort: { key: 'base_price', dir: 'desc' },
    note: '料理の売値から導出（食材の質で + 変動）。',
  },
  quests: {
    columns: [
      { key: 'name', label: 'クエスト（英名）', kind: 'title', primaryKey: 'memo', subKey: '', sortable: true },
      { key: 'given_by', label: '担当キャラ', kind: 'text', sortable: true },
      { key: 'type', label: '種別', kind: 'text' },
      { key: 'reward', label: '報酬', kind: 'text' },
      { key: 'link', label: '日本語名', kind: 'link', linkLabel: 'gamepediaで見る' },
      { key: 'completed', label: '達成', kind: 'toggle', onLabel: '✓', offLabel: '—' },
    ],
    searchKeys: ['memo', 'given_by', 'type'],
    editable: ['completed', 'completed_date', 'memo'],
    note: '日本語のクエスト名は、担当キャラの gamepedia ページで確認できます（リンク）。',
  },
  facilities: {
    columns: [
      { key: 'name_ja', label: '施設名', kind: 'text', sortable: true },
      { key: 'type', label: '種別', kind: 'text' },
      { key: 'note', label: '備考', kind: 'text' },
      { key: 'visited_today', label: '今日訪問', kind: 'toggle', onLabel: '✓', offLabel: '—' },
    ],
    searchKeys: ['name_ja'],
    editable: ['visited_today', 'memo'],
    note: 'materials の入手元から自動集約（最小）。Fandom の施設ページで拡充可。',
  },
  events: {
    columns: [
      { key: 'name_ja', label: 'イベント/スターパス', kind: 'text', sortable: true },
      { key: 'memo', label: '種別', kind: 'text' },
      { key: 'period', label: '期間', kind: 'text' },
      { key: 'participated', label: '参加', kind: 'toggle', onLabel: '✓', offLabel: '—' },
    ],
    searchKeys: ['name_ja', 'memo'],
    editable: ['participated', 'reward_progress', 'memo'],
  },
  expansions: {
    columns: [
      { key: 'name_ja', label: '拡張パス', kind: 'text', sortable: true },
      { key: 'release_date', label: '配信日', kind: 'text', sortable: true },
      { key: 'price', label: '価格', kind: 'text' },
      { key: 'included_realms', label: '含まれるレルム', kind: 'chips' },
      { key: 'owned', label: '所持', kind: 'toggle', onLabel: '✓', offLabel: '—' },
    ],
    searchKeys: ['name_ja'],
    editable: ['owned', 'progress_notes'],
  },
  updates: {
    columns: [
      { key: 'version', label: 'バージョン', kind: 'text', sortable: true },
      { key: 'release_date', label: '配信日', kind: 'text', sortable: true },
      { key: 'title', label: 'タイトル', kind: 'text' },
      { key: 'summary', label: '概要', kind: 'text' },
    ],
    searchKeys: ['version', 'title'],
    editable: ['personal_notes'],
    note: 'Fandom の Version history から随時追記してください。',
  },
  bugs: {
    columns: [
      { key: 'title', label: 'タイトル', kind: 'text', sortable: true },
      { key: 'affected_platform', label: '対象環境', kind: 'text' },
      { key: 'status', label: '状態', kind: 'text' },
      { key: 'personal_encountered', label: '遭遇', kind: 'toggle', onLabel: '✓', offLabel: '—' },
    ],
    searchKeys: ['title', 'description'],
    editable: ['personal_encountered', 'workaround_tried', 'memo'],
    note: '不具合はユーザーが追記していく想定（現状は器のみ）。',
  },
}
