# DDV 攻略メモ — 引き継ぎ書 / 仕様書

最終更新: 2026-07-12
このドキュメントは、別のセッション（クラウド/iPhone含む）や将来の自分が、このプロジェクトの続きを迷わず進められるようにまとめた自己完結の引き継ぎ資料です。**まず最初にこれを読んでください。**

---

## 0. これは何？（プロジェクト概要）

- **目的**: Disney Dreamlight Valley (DDV) の攻略情報を、自分専用にまとめた**非公開・個人利用**のWebサイト。
- **作業場所**: `/Users/yukimatsui/Desktop/ddv-guide/`（このフォルダ一式がプロジェクト本体）
- **公開URL（あなた専用・鍵付き）**: https://ddv-guide.pages.dev
  - Cloudflare Access で「y1219e@gmail.com のみ」に制限。外出先（携帯回線）でも見られる。iPhoneでPWA化可能。
- **データ出典**: Fandom（英語Wiki, CC-BY-SA）＋ gamepedia.jp 攻略大百科（日本語名の突合のみ）。

### ⚠️ 最重要ルール（著作権）— 必ず守る
1. **キャラ等の画像はディズニー/Gameloftの著作物**。**公開URLに載せない**。
   → いまは Cloudflare Access で「鍵付き（本人のみ）」だから画像を置ける。**公開（誰でも閲覧可）にする場合は画像を必ず外す**こと。
2. Fandom本文（説明文）は**日本語で要約・パラフレーズ**して使う（直訳の丸写しNG）。名前・数値・★等の**事実データはそのまま可**。
3. **gamepedia.jp の本文は転載しない**。日本語の固有名詞（名前）の突合にのみ使用。tips/faq/bugs は本文コピーせず**リンクのみ**。

---

## 1. 技術スタック・構成

- **フロント**: Svelte 5（runes: `$state`/`$derived`/`$props`）+ Vite 6 + TypeScript
- **データ保存**: **IndexedDB**（🔒外部データは静的JSONからシード、✏️自分用フィールドは端末ローカルに保存）
- **PWA**: `vite-plugin-pwa`（オフライン対応・ホーム追加・アイコン）
- **ホスティング**: Cloudflare Pages ＋ Cloudflare Access（鍵付き）

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
      router.ts                 ハッシュルーター＋asset()（BASE_URL対応）
      data/*.json               各カテゴリのデータ（下記）
    routes/
      Hub.svelte                トップ（④ハブ＆スポーク＝15カテゴリメニュー）
      CharactersZukan/CompanionsZukan                 ②図鑑グリッド（画像）
      RecipesTable/MaterialsTable                     専用テーブル
      DataTable.svelte          汎用テーブル（tableConfig 駆動：crops/prices/quests/facilities/events/expansions/updates）
      LinkList                   参照リンク集（bugs/tips/faq）
      Dashboard.svelte          レルム進行の集計
  public/
    icons/                      PWAアイコン（金の星✦）
    images/characters|companions/*.webp  ← ★gitignore対象（公開リポジトリに入れない）
  scripts/                      データ生成スクリプト一式（Python）← 再生成・拡充用
  .github/workflows/deploy.yml  （GitHub Pages用。今はCloudflare運用なので未使用でも可）
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
| characters キャラ | ②図鑑 | 69 | 69/69 ✅ | 43/69 | scripts/build_characters_json.py（Fandom） |
| companions オトモ | ②図鑑 | 68 | 0（英名） | 64/68 | scripts/build_critters.py（Fandom Critters記事）。旧「動物」14種は種ごとに統合済み |
| recipes 料理レシピ | 表 | 383 | **307/383** | – | build_recipes_json.py＋build_name_ja.py |
| materials 素材 | 表 | 180 | **148/180** | – | build_materials_json.py＋build_name_ja.py |
| crops 農作物 | 表 | 21 | 21/21 ✅ | – | build_rest.py（materials由来） |
| prices 売値 | 表 | 383 | – | – | build_rest.py（recipes由来） |
| quests クエスト | 表 | 128 | リンク方式※ | – | build_rest.py＋担当キャラ付与 |
| events イベント | 表 | 39 | 22/39 | – | build_rest.py＋手動突合（下記） |
| facilities 施設 | 表 | 7 | 7 | – | build_final.py（既知ショップ・要拡充） |
| expansions 拡張パス | 表 | 2 | 2 | – | build_final.py（手構築） |
| updates 更新履歴 | 表 | 11 | – | – | build_final.py（Fandom版番号＋リンク） |
| bugs/tips/faq | リンク集 | 各1-2 | – | – | build_final.py（gamepedia該当ページへリンク） |
| dashboard | 集計 | – | – | – | 各storeから自動集計＋localStorage |

※ quests の日本語名: 確実な自動突合が困難なため（下記5参照）、各クエスト行に「担当キャラ」＋「gamepediaで見る」リンクを付け、参照先で日本語名を確認する方式（`given_by` は127/128付与済み）。

### 画像が「?」のもの＝Fandomに画像が無くて未取得（正常）
- キャラ26体・オトモ4体・動物1種。Fandom API で画像が露出しない（リダイレクト/スタブページ等）。別ソースがあれば後で追加可。詳細は下記メモリ [[ddv-fandom-api-limits]] 相当。

---

## 3. データの再生成・拡充方法（scripts/）

すべて Python。`cd ~/Desktop/ddv-guide` で実行し、`data/*.json` を更新 → `cp data/*.json src/lib/data/` → 再ビルド/デプロイ。
（注: 実行には `requests` が必要。arm64 Mac では Pillow/charset_normalizer を `pip install --force-reinstall` でarm64版に直す必要がある場合あり）

- **fetch_ddv_images.py**: `items.csv`(id,name_en) から Fandom画像をDL（元祖スクリプト）
- **build_characters_json.py**: キャラ69体のJSON生成（franchise/解放条件要約/居住地/icon_path）
- **build_recipes_json.py**: レシピ383。Fandom `Meals/<realm>` 一覧表をパース（File形式＋{{IDb}}/{{IDm}}テンプレの2形式対応）。★=材料数。
- **build_materials_json.py**: 材料180。Fandom item infobox から種別/入手方法。used_in_recipes逆引き。
- **build_critters.py**: 動物14種＋オトモ68体（色違い）＋画像。`Critters`記事の餌付け表。SPECIES_WORDSに Cobra/Owl/Pegasus/Baby Dragon/Raven を含める（不規則複数 Pegasi 対応済み）。
- **build_rest.py**: crops/prices/quests/facilities/events/updates/bugs/tips/faq をまとめて生成。quests/eventsはFandom Category取得。
- **build_name_ja.py**: ★日本語名突合の要。gamepediaレシピ表(archives/21)を取得し、(★,売値)＋材料一致で recipes に name_ja。さらに**マッチ済レシピの材料位置からEN→JA材料辞書を制約伝播で成長**(99→148語)→ materials/crops へ反映。グループ内1対1マッチで recipes 307達成。
- **match_recipe_ja.py**: build_name_ja の初期版（参考）。
- **build_final.py**: facilities/updates の拡充＋tips/faq/bugsのリンク集データ。

---

## 4. デプロイ手順（Cloudflare Pages ＋ Access）★重要

### 前提（1回だけ設定済み）
- Cloudflare Pages プロジェクト名: **ddv-guide**（account: y1219e@gmail.com / id `da383b6721bf5792564547a16cb602c2`）
- Cloudflare Access アプリで **`ddv-guide.pages.dev` と `*.ddv-guide.pages.dev` の両方**を保護、ポリシー「Emails = y1219e@gmail.com のみ Allow」、Session 1か月。
- wrangler ログイン済み（`npx wrangler whoami` で確認可）。

### ⚠️ ハマりどころ（絶対に忘れない）
Cloudflare Pages は**デプロイのたびに `<hash>.ddv-guide.pages.dev` という枝番URLを作る**。Access を `ddv-guide.pages.dev` だけに掛けると**枝番URLは無防備で画像が公開されてしまう**。
→ **必ず `*.ddv-guide.pages.dev`（ワイルドカード）も Access で保護**しておくこと（設定済み）。デプロイ後は必ず枝番URLが `302`（＝鍵あり）か確認する。

### 更新をデプロイする手順
```bash
cd ~/Desktop/ddv-guide
export CLOUDFLARE_ACCOUNT_ID=da383b6721bf5792564547a16cb602c2
npm run build:fast
npx wrangler pages deploy dist --project-name=ddv-guide --branch=main --commit-dirty=true
# → 出力の https://<hash>.ddv-guide.pages.dev が 302 になるか確認:
#    curl -s -o /dev/null -w '%{http_code}' https://<hash>.ddv-guide.pages.dev/images/characters/char_elsa.webp  → 302 ならOK
```
- 画像は `public/images/`（gitignore対象だがローカルには存在）→ build時に dist に入る → 鍵の内側にだけ置かれる。
- **もし公開（鍵なし）にするなら**: `public/images/` を外してビルド（画像なし版）。コンポーネントは画像が無ければ自動で「?」表示。

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
1. **（中）残りの日本語名**: recipes 76件・materials 32件（gamepedia側に対応が無い/辞書未収の素材）。events 17件（単発イベント）。quests 128件（リンク方式で代替中／自動命名は5参照）。
2. **（中）facilities / updates の拡充**: facilitiesは既知7件のみ。updatesは版番号＋リンクのみ（要約は手入力前提）。
3. **（小）画像が無い「?」のキャラ等**: 別ソースがあれば追加。
4. **（小）デザイン本採用**: 配色は「Dreamlight」仮採用。もし `ddv-prototypes.jsx`（Fraunces+Manrope、正式カラー）が手に入れば `src/app.css` の `:root` を差し替え。
5. **（任意）bugs/tips/faq**: 現状は参照リンクのみ。自分でメモを書き溜めたいなら、入力フォーム＋IndexedDB保存の実装が必要（今は器のみ）。

### 新カテゴリ/データを足す手順（定型）
1. `scripts/` でJSON生成 → `data/<key>.json` → `src/lib/data/<key>.json` にコピー
2. 表なら `src/lib/tableConfig.ts` に列定義を追加（既存が雛形）
3. `src/lib/db/seed.ts` の `seedAll()` に `seedStore('<key>', <key>Seed)` を追加、`EDITABLE` に✏️項目
4. `src/lib/schema/index.ts` の `CATEGORIES` で `implemented: true`
5. 型チェック → ビルド → デプロイ（4章）

---

## 7. 別セッション/iPhoneで続きをやるには

- このプロジェクトの**ソース・データ・スクリプト・本ドキュメントはすべて `~/Desktop/ddv-guide/` に揃っている**ので、そのフォルダを見れば続行可能。
- 新しいClaudeセッション（クラウド/モバイル）で作業する場合は、**まず本 HANDOFF.md を読ませる**こと。加えて、このMacの `~/.claude/projects/.../memory/` にプロジェクトメモリ（ddv-project 等）があるが、これは端末ローカルなので別環境には引き継がれない → 本ドキュメントを正とする。
- ※このチャット（会話ログ）自体の別端末での閲覧については本章末の注記参照。

---

## 8. これまでの経緯（要約）

タスクA(画像取得)→ B(スキャフォールド)→ C(全カテゴリのデータ化)→ D(UI/レスポンシブ)→ 日本語名突合 → 配色 → PWA化 → Cloudflare(鍵付き)公開、の順で構築。全16カテゴリ稼働、型チェック0エラー、iPhone/iPad/Mac対応、外出先から画像つき閲覧＋PWA、を達成。著作権は「非公開（本人のみ）」で担保。
