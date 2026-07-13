# DDV 攻略メモ

Disney Dreamlight Valley の攻略情報を自分用にまとめた個人運営サイト。
公開: **https://lorecajp.github.io/ddv-guide/** （`noindex`。画像は Disney 許諾のもと掲載）

## 技術
- Svelte 5 + Vite + TypeScript
- データ保存: **IndexedDB**（ブラウザローカル。🔒外部データは静的JSONからシード、✏️自分用フィールドは端末に保存。端末間移行はダッシュボードのバックアップ/復元）
- ホスティング: GitHub Pages（`main` への push で `.github/workflows/deploy.yml` が自動デプロイ）

## 開発
```bash
npm install
npm run dev        # 開発サーバ
npm run build      # 型チェック + 本番ビルド（dist/）
npm run build:fast # 型チェックなしで高速ビルド
npm run preview    # ビルド結果をプレビュー
```

## 構成
```
src/
  app.css                 デザイントークン（CSS変数。ddv-prototypes.jsx の値に差し替え予定）
  lib/
    schema/index.ts       15カテゴリの TypeScript 型 + カテゴリメタ(CATEGORIES)
    db/idb.ts             最小 IndexedDB ラッパー
    db/seed.ts            静的JSON → IndexedDB（✏️編集を保持してマージ）
    db/transfer.ts        データ移行（✏️＋dashboard の書き出し/読み込み）
    data/characters.json  キャラ72体（🔒データ）
    router.ts             ハッシュルーター + asset() パスヘルパー
  routes/
    Hub.svelte            トップ = ④ハブ＆スポーク（15カテゴリメニュー・進捗表示）
    CharactersZukan.svelte キャラ詳細 = ②図鑑グリッド（検索/作品フィルタ/解放トグル）
    CategoryPlaceholder.svelte 未実装カテゴリの案内
public/
  images/characters|companions/*.webp  肖像（リポジトリにコミット＝公開）
```

## データの追加（タスクC の続き）
1. 新カテゴリの JSON を `src/lib/data/<key>.json` に置く
2. `src/lib/db/seed.ts` に `seedStore(...)` を1行追加
3. 表示は `src/routes/` に対応コンポーネントを足し、`App.svelte` で分岐

## デザイントークン
`src/app.css` の `:root` は**仮パレット**。`ddv-prototypes.jsx` のカラー値を受領後、ここを差し替えるだけで全体に反映される。フォントは Fraunces（見出し）+ Manrope（本文）。
