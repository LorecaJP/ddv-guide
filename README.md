# DDV 攻略メモ（個人用）

Disney Dreamlight Valley の攻略情報を自分専用にまとめる非公開サイト。**個人利用のみ**。

## 技術
- Svelte 5 + Vite + TypeScript
- データ保存: **IndexedDB**（ブラウザローカル。🔒外部データは静的JSONからシード、✏️自分用フィールドは端末に保存）
- ホスティング想定: GitHub Pages（`.github/workflows/deploy.yml`）

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
    schema/index.ts       16カテゴリの TypeScript 型 + カテゴリメタ(CATEGORIES)
    db/idb.ts             最小 IndexedDB ラッパー
    db/seed.ts            静的JSON → IndexedDB（✏️編集を保持してマージ）
    data/characters.json  キャラ69体（🔒データ）
    router.ts             ハッシュルーター + asset() パスヘルパー
  routes/
    Hub.svelte            トップ = ④ハブ＆スポーク（16カテゴリメニュー）
    CharactersZukan.svelte キャラ詳細 = ②図鑑グリッド（検索/作品フィルタ/解放トグル）
    CategoryPlaceholder.svelte 未実装カテゴリの案内
public/
  images/characters/*.webp  キャラ肖像（ローカル参照）
```

## データの追加（タスクC の続き）
1. 新カテゴリの JSON を `src/lib/data/<key>.json` に置く
2. `src/lib/db/seed.ts` に `seedStore(...)` を1行追加
3. 表示は `src/routes/` に対応コンポーネントを足し、`App.svelte` で分岐

## 画像・著作権
画像・データは Disney Dreamlight Valley Wiki (Fandom) 由来。画像は Disney/Gameloft の著作物で、**個人参照用**として保持。再配布・公開再アップロードはしない。本文の説明は Fandom 英語版を日本語で要約（直訳の丸写しはしない）。

## デザイントークン
`src/app.css` の `:root` は**仮パレット**。`ddv-prototypes.jsx` のカラー値を受領後、ここを差し替えるだけで全体に反映される。フォントは Fraunces（見出し）+ Manrope（本文）。
