/* =========================================================================
   依存なしの最小ハッシュルーター（GitHub Pages でリロードしても壊れない）
   ルート例:  #/            トップ（Hub）
             #/characters  カテゴリ詳細
   ========================================================================= */
import { readable } from 'svelte/store'

export interface Route {
  category: string | null // null = トップ
  params: Record<string, string>
}

function parse(): Route {
  const raw = location.hash.replace(/^#\/?/, '')
  const [path, qs = ''] = raw.split('?')
  const seg = path.split('/').filter(Boolean)
  const params: Record<string, string> = {}
  for (const kv of qs.split('&').filter(Boolean)) {
    const [k, v = ''] = kv.split('=')
    params[decodeURIComponent(k)] = decodeURIComponent(v)
  }
  return { category: seg[0] ?? null, params }
}

export const route = readable<Route>(parse(), (set) => {
  const on = () => set(parse())
  window.addEventListener('hashchange', on)
  return () => window.removeEventListener('hashchange', on)
})

export function navigate(category: string | null, params?: Record<string, string>): void {
  if (!category) {
    location.hash = '#/'
    return
  }
  const qs = params
    ? Object.entries(params)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('&')
    : ''
  location.hash = `#/${category}${qs ? `?${qs}` : ''}`
}

/**
 * 現在のカテゴリの検索/フィルタ状態を URL クエリに反映する。
 * history.replaceState を使うため、履歴（戻る）を汚さず・hashchange も発火しない
 * （＝再描画ループにならない）。空文字/未指定のキーは省く。
 * これにより「戻る」「リロード」「PWA再訪」「URL共有」で絞り込み条件が保持される。
 */
export function setParams(category: string, params: Record<string, string>): void {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== '' && v != null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')
  const hash = `#/${category}${qs ? `?${qs}` : ''}`
  history.replaceState(history.state, '', hash)
}

/** public/ 配下のアセットを base 付きで参照（GitHub Pages のサブパス対応） */
export function asset(path: string): string {
  const base = import.meta.env.BASE_URL // 例: './' または '/ddv-guide/'
  return base.replace(/\/$/, '') + '/' + path.replace(/^\//, '')
}
