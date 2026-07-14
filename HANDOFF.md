# DDV 攻略メモ — 引き継ぎ書 / 仕様書

最終更新: 2026-07-13
このドキュメントは、別のセッション（クラウド/iPhone含む）や将来の自分が、このプロジェクトの続きを迷わず進められるようにまとめた自己完結の引き継ぎ資料です。**まず最初にこれを読んでください。**

---

## 0. これは何？（プロジェクト概要）

- **目的**: Disney Dreamlight Valley (DDV) の攻略情報を、自分用にまとめた個人運営のWebサイト。
- **作業場所**: `/Users/yukimatsui/Desktop/ddv-guide/`（このフォルダ一式がプロジェクト本体）。GitHub: `LorecaJP/ddv-guide`（public）
- **公開URL**: https://lorecajp.github.io/ddv-guide/ （**GitHub Pages で公開**。`main` への push で自動デプロイ）
  - `noindex` 指定のため検索エンジンには載らない（URLを知っている人のみアクセス）。iPhoneでPWA化可能。
  - ※ 旧構成の Cloudflare Pages + Access（鍵付き `ddv-guide.pages.dev`）は廃止。現在は GitHub Pages 公開に一本化。
- **データ出典**: Fandom（英語Wiki, CC-BY-SA）＋ gamepedia.jp 攻略大百科（日本語名の突合のみ）。

### ⚠️ 最重要ルール（著作権）— 必ず守る
1. **画像はディズニー/Gameloftの著作物**。**Disney より本サイト内での利用許諾を得たため、公開版に掲載している**（`public/images/` をコミット＝公開）。この許諾はこのサイトでの利用に限る前提。
2. Fandom本文（説明文）は**日本語で要約・パラフレーズ**して使う（直訳の丸写しNG）。名前・数値・★等の**事実データはそのまま可**。CC-BY-SA のためフッターに Fandom 帰属を明記済み。
3. **gamepedia.jp の本文は転載しない**。日本語の固有名詞（名前）の突合にのみ使用。tips/faq/bugs は本文コピーせず**リンクのみ**。

---

## 1. 技術スタック・構成

- **フロント**: Svelte 5（runes: `$state`/`$derived`/`$props`）+ Vite 6 + TypeScript
- **データ保存**: **IndexedDB**（🔒外部データは静的JSONからシード、✏️自分用フィールドは端末ローカルに保存）
- **PWA**: `vite-plugin-pwa`（オフライン対応・ホーム追加・アイコン）
- **ホスティング**: **GitHub Pages**（`.github/workflows/deploy.yml`：`main` への push で自動ビルド＆デプロイ）

### ディレクトリ
```
ddv-guide/
  src/
    app.css                     デザイントークン（CSS変数「Dreamlight」配色。昼=クリーム＋金 / 夜=紫紺＋金）
    main.ts / App.svelte        ルーティング（ハッシュルーター）
    lib/
      schema/index.ts           15カテゴリのTS型 ＋ CATEGORIES（メニュー定義）
      tableConfig.ts            設定駆動テーブルの列定義（カテゴリごと）
      db/idb.ts                 最小 IndexedDB ラッパー
      db/seed.ts                静的JSON→IndexedDB（✏️編集を保持してマージ）
      db/transfer.ts            データ移行（✏️＋dashboardをJSON書き出し/読み込み。端末間バックアップ）
      router.ts                 ハッシュルーター＋asset()（BASE_URL対応）
      data/*.json               各カテゴリのデータ（下記）
    routes/
      Hub.svelte                トップ（④ハブ＆スポーク＝15カテゴリメニュー）
      CharactersZukan/CompanionsZukan                 ②図鑑グリッド（画像）
      RecipesTable/MaterialsTable                     専用テーブル
      DataTable.svelte          汎用テーブル（tableConfig 駆動：prices/quests/facilities/events/expansions/updates）
      LinkList                   参照リンク集（bugs/tips/faq）
      Dashboard.svelte          レルム進行の集計
  public/
    icons/                      PWAアイコン（金の星✦）
    images/characters|companions/*.webp  ← リポジトリにコミット＝公開（Disney許諾あり）
  scripts/                      データ生成スクリプト一式（Python）← 再生成・拡充用
  .github/workflows/deploy.yml  GitHub Pages 自動デプロイ（main push でトリガ）
  HANDOFF.md                    このファイル
```

### 開発・ビルド
```bash
cd ~/Desktop/ddv-guide
npm install
npm run dev        # 開発サーバ（--host付き。LANのiPhoneからも見える）
npm run check      # 型チェック（0エラーを維持）
npm run build      # 型チェック＋本番ビルド
npm run build:fast # 型チェックなしで高速ビルド（デプロイ時に使用）
```
デスクトップの **「DDV攻略メモを開く.command」** をダブルクリックすると、Mac起動＋LAN URL表示（家のWiFiでiPhone閲覧用）。

---

## 2. カテゴリとデータの現状（15カテゴリすべて稼働）

| カテゴリ | 表示 | 件数 | 日本語名(name_ja) | 画像 | データ源/生成 |
|---|---|---|---|---|---|
| characters キャラ | ②図鑑 | 72 | 72/72 ✅ | **72/72 ✅** | scripts/build_characters_json.py（Fandom） |
| companions オトモ | ②図鑑 | 196 | 種名・色名で表示 | 196/196 ✅ | scripts/build_critters.py（Fandom Critters記事）。旧「動物」14種は種ごとに統合済み。カートゥーン/新種ハリネズミ/イベント・スターパス・プレミアム・キャラのペット等を追加。特別個体は入手元を「生息地」欄に記載（好物なし）。多くの日本語名は暫定（name_en が正） |
| recipes 料理レシピ | 表 | 480 | **480/480 ✅** | – | build_recipes_json.py＋build_name_ja.py＋gamepedia追加分 |
| materials 素材 | 表 | 180 | **180/180 ✅** | **173/180** | build_materials_json.py 系。**種別(category)で13分類**＋**世界(realms)で4分類**（バレー/永遠の島/物語の谷/願い咲く牧場）。表示は種別ごとにグループ化し各種別内を五十音順。画像は mydreamlightvalley、入手方法は各wikiで詳細化。旧「農作物」カテゴリを統合済み |
| crafting クラフト素材 | 表 | 116 | **116/116 ✅** | 112/116 | 宝石53(Shiny含)/鉱石8/精錬10/木材10/石材8/繊維5/その他22。世界5分類(バレー/永遠の島/物語の谷/願い咲く牧場/ハニーグローの森)。mydreamlightvalley `/images/materials/`＋各wiki横断調査。種別グループ＋世界フィルタ（MaterialsTableと同UI）。画像は mydreamlightvalley＋Fandom API。宝石はノーマル→きらめくのペア順表示。画像なし4件(最新DLC木材/石材)は⛏️表示 |
| prices 売値 | 表 | 383 | 料理のname_jaを表示 | – | build_rest.py（recipes由来）。表示時に recipes と id 連携 |
| quests クエスト | 表 | 128 | リンク方式※ | – | build_rest.py＋担当キャラ付与 |
| events イベント | 表 | 39 | 39/39 ✅ | – | build_rest.py＋手動突合 |
| facilities 施設 | 表 | 7 | 7 | – | build_final.py（既知ショップ・要拡充） |
| expansions 拡張パス | 表 | 2 | 2 | – | build_final.py（手構築） |
| updates 更新履歴 | 表 | 11 | – | – | build_final.py（Fandom版番号＋リンク） |
| bugs/tips/faq | リンク集 | 各1-2 | – | – | build_final.py（gamepedia該当ページへリンク） |
| dashboard | 集計 | – | – | – | 各storeから自動集計＋localStorage |

※ quests の日本語名: 確実な自動突合が困難なため（下記5参照）、各クエスト行に「担当キャラ」＋「gamepediaで見る」リンクを付け、参照先で日本語名を確認する方式（`given_by` は127/128付与済み）。

### 画像
- キャラ: **72/72 取得済み ✅**。
- オトモ: **196/196 取得済み ✅**（159体は Fandom API、残り37体は mydreamlightvalley.com の
  `/images/critters/` `/images/companions/` から取得）。
  - 特別個体（スターパス/イベント/プレミアム/クエスト/エディション特典/配布コード）は野生給餌でないため `favorite_foods` は空、入手区分を `habitat`/`source` に記載。日本語名の多くは暫定で `name_en` が正（`memo` に「※日本語名は暫定」を付与）。
- 画像は `public/images/characters|companions/*.webp` に配置し、各 JSON の `icon_path` で参照。

---

## 3. データの再生成・拡充方法（scripts/）

すべて Python。`cd ~/Desktop/ddv-guide` で実行し、`data/*.json` を更新 → `cp data/*.json src/lib/data/` → 再ビルド/デプロイ。
（注: 実行には `requests` が必要。arm64 Mac では Pillow/charset_normalizer を `pip install --force-reinstall` でarm64版に直す必要がある場合あり）

- **fetch_ddv_images.py**: `items.csv`(id,name_en) から Fandom画像をDL（元祖スクリプト）
- **build_characters_json.py**: キャラ72体のJSON生成（franchise/解放条件要約/居住地/icon_path）
- **build_recipes_json.py**: レシピの基礎生成。Fandom `Meals/<realm>` 一覧表をパース（File形式＋{{IDb}}/{{IDm}}テンプレの2形式対応）。★=材料数。※現在は gamepedia 追加分と合わせて計480件。
- **build_materials_json.py**: 材料180。Fandom item infobox から種別/入手方法。used_in_recipes逆引き。
- **build_critters.py**: 動物14種＋オトモ68体（色違い）＋画像。`Critters`記事の餌付け表。SPECIES_WORDSに Cobra/Owl/Pegasus/Baby Dragon/Raven を含める（不規則複数 Pegasi 対応済み）。※その後、新オトモ（色違い/カートゥーン/ハリネズミ/イベント・スターパス・プレミアム・クエスト・キャラのペット 等）を手動追加し現在オトモは計196体。
- **build_rest.py**: crops/prices/quests/facilities/events/updates/bugs/tips/faq をまとめて生成。quests/eventsはFandom Category取得。
- **build_name_ja.py**: ★日本語名突合の要。gamepediaレシピ表(archives/21)を取得し、(★,売値)＋材料一致で recipes に name_ja。さらに**マッチ済レシピの材料位置からEN→JA材料辞書を制約伝播で成長**(99→148語)→ materials/crops へ反映。グループ内1対1マッチで recipes 307達成。
- **match_recipe_ja.py**: build_name_ja の初期版（参考）。
- **build_final.py**: facilities/updates の拡充＋tips/faq/bugsのリンク集データ。

---

## 4. デプロイ手順（GitHub Pages・自動）★重要

### 仕組み
- リポジトリ `LorecaJP/ddv-guide`（public）の **`main` に push すると `.github/workflows/deploy.yml` が自動実行**され、`npm ci` → `npm run build:fast` → `actions/deploy-pages` で公開される。
- 公開先: **https://lorecajp.github.io/ddv-guide/**
- リポジトリ Settings → Pages → Source =「GitHub Actions」に設定済み（有効化は1回だけ。未設定だと deploy が 404 で失敗する）。

### 更新をデプロイする手順（普段の運用）
```bash
cd ~/Desktop/ddv-guide
# （データ/画像/コードを変更したら）
git add -A
git commit -m "変更内容"
git push origin main       # ← これだけで自動ビルド＆公開（1〜2分）
```
- 画像は `public/images/` にコミット済み → build 時に `dist/images/` へ入り、そのまま公開される。
- 画像を追加/差し替えたら `git add public/images && commit && push` で反映。
- ⚠️ 画像を大量に push すると `RPC failed; HTTP 400`（送信バッファ超過）が出ることがある → 一度だけ `git config http.postBuffer 524288000` を実行しておく（設定済み）。

### 手動での確認・再実行
- 進捗: GitHub の Actions タブ →「Deploy to GitHub Pages」。
- 失敗時: 該当 run で「Re-run all jobs」。または Actions →「Run workflow」で main を手動実行。

---

## 5. 日本語名突合：徹底調査の結論（quests/events）

「英語名→機械翻訳→文字列で近似マッチ」は公式訳と合わず不正確。代わりに**言語非依存の鍵で照合**した。調査済みの方法と結果:
- ❌ Fandom言語間リンク（日本語版）: 存在しない（es/frのみ）
- ❌ 公開の英日対訳データセット: 見つからず
- ❌ イベント日付照合: gamepediaの日付は記事投稿日で開催日でない
- ✅ **イベント**: 時系列順＋テーマ一致で22/39にJA名（スターパス群。build後 events.json に反映済み）
- ⚠️ **クエスト**: Fandom infoboxに `given by`(担当キャラ)＋`previous/next`(連鎖順)、gamepediaキャラページに順序付きJAクエスト名 → 「キャラ別＋順番」で照合可能だが**2サイトの順序ズレで誤りが連鎖するリスク大**。よって自動命名は保留し、**リンク方式**を採用（現状）。
  - もし将来やるなら: キャラごとに Fandom連鎖順 vs gamepedia順を突き合わせ、**報酬アイテム名（EN→JA辞書）で各対応を検証**して誤りを排除する実装が必要。

---

## 6. 残タスク（やり残し）

優先度の目安つき。
1. **（中）残りの日本語名**: materials 32件（gamepedia側に対応が無い/辞書未収の素材）。※ recipes・events は現在 name_ja 全件付与済み。quests はリンク方式で代替中（自動命名は5参照）。
2. **（中）facilities / updates の拡充**: facilitiesは既知7件のみ。updatesは版番号＋リンクのみ（要約は手入力前提）。
3. **（小）オトモの未取得画像 9体**: ペガサス4色・ガチョウ・スイートなハチ4種。Fandom 等に画像があれば `icon_path` に追加。
4. **（小）デザイン本採用**: 配色は「Dreamlight」仮採用。もし `ddv-prototypes.jsx`（Fraunces+Manrope、正式カラー）が手に入れば `src/app.css` の `:root` を差し替え。
5. **（任意）bugs/tips/faq**: 現状は参照リンクのみ。自分でメモを書き溜めたいなら、入力フォーム＋IndexedDB保存の実装が必要（今は器のみ）。

### 新カテゴリ/データを足す手順（定型）
1. `scripts/` でJSON生成 → `data/<key>.json` → `src/lib/data/<key>.json` にコピー
2. 表なら `src/lib/tableConfig.ts` に列定義を追加（既存が雛形）
3. `src/lib/db/seed.ts` の `SEED_LOADERS` に `<key>: () => import('../data/<key>.json')` を追加、`EDITABLE` に✏️項目（seedAll は SEED_LOADERS を自動で回す）
4. `src/lib/schema/index.ts` の `CATEGORIES` に追加（`display` と `implemented: true`）
5. ⚠️ 新ストア追加時は `src/lib/db/idb.ts` の `DB_VERSION` を +1（既存端末に objectStore を作るため。過去の「動物」不具合の教訓）
6. 型チェック → ビルド → push（自動デプロイ, 4章）

---

## 7. 別セッション/iPhoneで続きをやるには

- このプロジェクトの**ソース・データ・スクリプト・本ドキュメントはすべて `~/Desktop/ddv-guide/` に揃っている**ので、そのフォルダを見れば続行可能。
- 新しいClaudeセッション（クラウド/モバイル）で作業する場合は、**まず本 HANDOFF.md を読ませる**こと。加えて、このMacの `~/.claude/projects/.../memory/` にプロジェクトメモリ（ddv-project 等）があるが、これは端末ローカルなので別環境には引き継がれない → 本ドキュメントを正とする。
- ※このチャット（会話ログ）自体の別端末での閲覧については本章末の注記参照。

---

## 8. これまでの経緯（要約）

タスクA(画像取得)→ B(スキャフォールド)→ C(全カテゴリのデータ化)→ D(UI/レスポンシブ)→ 日本語名突合 → 配色 → PWA化、の順で構築。当初は Cloudflare(鍵付き)公開だったが、後に **GitHub Pages で一般公開**へ移行。

### その後の主な変更（2026-07 時点）
- **構造整理**: 旧「動物」カテゴリを廃止しオトモ図鑑へ統合。さらに旧「農作物」カテゴリを廃止し素材に統合（素材を種別13分類でフィルタ、栽培場所は obtain_method へ）（→ 14カテゴリ）。到達不能な死コード（ArticleList 等）を除去。表示種別を `image-grid/table/links/dashboard` に整理。
- **UX/性能**: Hub タイルに進捗表示 / 検索・フィルタ状態を URL に保持 / 静的データを動的 import で分割しメインJSを 551KB→96.5KB に / 売値ページのアイテム名を料理の日本語名に。
- **データ移行**: `lib/db/transfer.ts`＋ダッシュボードに「バックアップ/復元」を追加（端末間で ✏️ データを移行）。
- **公開**: リポジトリを public 化 → GitHub Pages 有効化 → **Disney の許諾のもと画像も公開版に掲載**（`public/images/` をコミット）。フッターに Fandom(CC BY-SA) 帰属を明記。
- 現状: 15カテゴリ稼働、型チェック0エラー、iPhone/iPad/Mac対応、PWA、画像つき公開。
