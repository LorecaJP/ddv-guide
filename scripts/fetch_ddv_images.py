"""
Disney Dreamlight Valley Wiki (Fandom) 画像ダウンロードスクリプト
=================================================================

【使い方】
1. items.csv を用意する（id, name_en の2列。例は下記参照）
2. `pip install requests` 済みの環境で実行
   python fetch_ddv_images.py

【items.csv の例】
id,name_en
char_elsa,Elsa
char_mickey,Mickey Mouse
recipe_fish_soup,Fish Soup

【注意】
- Fandom (disneydreamlightvalley.fandom.com) の MediaWiki API を使って
  各ページのメイン画像URLを取得し、ローカルにダウンロードします。
- 画像自体はDisney/Gameloftの著作物です。CC-BY-SAはWiki本文のライセンスであり
  画像には適用されません。取得した画像は「個人用途の参照データ」として、
  ご自身の環境内でのみ利用してください。再配布や公開サイトへの再アップロードは避けてください。
- APIへの負荷軽減のため、リクエスト間に待機時間(SLEEP_SEC)を入れています。
  短くしすぎないようにしてください。
"""

import csv
import time
import pathlib
import sys

import requests

# ==== 設定 ====
WIKI_API = "https://disneydreamlightvalley.fandom.com/api.php"
INPUT_CSV = "items.csv"          # id,name_en の2列CSV
OUTPUT_DIR = pathlib.Path("images")
SLEEP_SEC = 1.0                   # API/画像取得の間隔（マナー的に1秒以上推奨）
THUMB_SIZE = 500                  # 取得する画像の幅(px)。0でオリジナルサイズ相当を試みる
USER_AGENT = "personal-ddv-archive/1.0 (individual use; contact: N/A)"

HEADERS = {"User-Agent": USER_AGENT}


CONTENT_TYPE_EXT = {
    "image/webp": ".webp",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}


def _normalize(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum())


def is_plausible_match(query: str, candidate_title: str) -> bool:
    """検索候補が問い合わせ語と無関係でないかの簡易チェック"""
    nq = _normalize(query)
    nc = _normalize(candidate_title)
    if not nq or not nc:
        return False
    # 完全一致 / 部分一致（どちらかがどちらかを含む）なら妥当とみなす
    return nq in nc or nc in nq


def get_first_page_image_via_images_list(title: str) -> str | None:
    """pageimagesが空の場合のフォールバック：ページ内の画像一覧から代表画像を探す"""
    params = {
        "action": "query",
        "titles": title,
        "prop": "images",
        "format": "json",
        "imlimit": 5,
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    file_titles = []
    for _, page in pages.items():
        for img in page.get("images", []):
            fname = img.get("title", "")
            # アイコン/UI系の使い回し画像は除外
            if any(skip in fname.lower() for skip in ["icon", "ui_", "site-", ".svg"]):
                continue
            file_titles.append(fname)
    if not file_titles:
        return None

    # 最初の候補ファイルの実URLを imageinfo で取得
    params2 = {
        "action": "query",
        "titles": file_titles[0],
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }
    resp2 = requests.get(WIKI_API, params=params2, headers=HEADERS, timeout=15)
    resp2.raise_for_status()
    data2 = resp2.json()
    pages2 = data2.get("query", {}).get("pages", {})
    for _, page in pages2.items():
        infos = page.get("imageinfo", [])
        if infos and "url" in infos[0]:
            return infos[0]["url"]
    return None


def get_page_image_url(title: str, thumb_size: int = THUMB_SIZE) -> str | None:
    """MediaWiki API から指定ページのメイン画像URLを取得する"""
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": thumb_size if thumb_size else 1000,
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    for _, page in pages.items():
        thumb = page.get("thumbnail")
        if thumb and "source" in thumb:
            return thumb["source"]

    # pageimagesに代表画像がない場合、ページ内画像一覧からフォールバック
    return get_first_page_image_via_images_list(title)


def search_best_title(query: str) -> str | None:
    """ページが直接見つからない場合、Wiki内検索で最も近そうなページ名を探す（nearmatch優先）"""
    # 1. タイトルの近似一致（最も信頼できる）
    params_near = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srwhat": "nearmatch",
        "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, params=params_near, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        if results and is_plausible_match(query, results[0]["title"]):
            return results[0]["title"]
    except requests.RequestException:
        pass

    # 2. 全文検索（フォールバック、ただし妥当性チェックを必須にする）
    params_full = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 3,
        "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, params=params_full, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        for r in results:
            if is_plausible_match(query, r["title"]):
                return r["title"]
    except requests.RequestException:
        pass

    return None


def download_image(url: str, dest_no_ext: pathlib.Path) -> pathlib.Path | None:
    """画像をダウンロードし、Content-Typeに基づいた拡張子でファイル名を確定して保存する"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
        ext = CONTENT_TYPE_EXT.get(content_type)

        if not ext:
            # Content-Typeで判定できない場合はURLの拡張子にフォールバック
            url_ext = pathlib.Path(url.split("?")[0]).suffix
            ext = url_ext if url_ext else ".img"

        dest = dest_no_ext.with_suffix(ext)
        dest.write_bytes(resp.content)
        return dest
    except requests.RequestException as e:
        print(f"  [ERROR] ダウンロード失敗: {e}")
        return None


def main():
    input_path = pathlib.Path(INPUT_CSV)
    if not input_path.exists():
        print(f"'{INPUT_CSV}' が見つかりません。id,name_en の2列CSVを用意してください。")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)

    with input_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"{len(rows)} 件の画像取得を開始します。")

    results = []
    for i, row in enumerate(rows, start=1):
        item_id = row["id"].strip()
        name_en = row["name_en"].strip()
        print(f"[{i}/{len(rows)}] {item_id} ({name_en}) ...")

        try:
            url = get_page_image_url(name_en)
        except requests.RequestException as e:
            print(f"  [ERROR] API取得失敗: {e}")
            results.append({"id": item_id, "name_en": name_en, "status": "api_error", "local_path": ""})
            time.sleep(SLEEP_SEC)
            continue

        matched_title = name_en
        if not url:
            # 直接ヒットしなかった場合、Wiki内検索で近い候補を探して再試行
            print("  [INFO] 直接ヒットなし。Wiki内検索でページ名を探します...")
            candidate = search_best_title(name_en)
            if candidate:
                print(f"  [INFO] 候補ページ: '{candidate}' で再試行")
                try:
                    url = get_page_image_url(candidate)
                    matched_title = candidate
                except requests.RequestException:
                    url = None
            time.sleep(SLEEP_SEC)

        if not url:
            print("  [SKIP] 画像が見つかりませんでした。")
            results.append({"id": item_id, "name_en": name_en, "status": "not_found", "local_path": ""})
            time.sleep(SLEEP_SEC)
            continue

        dest_no_ext = OUTPUT_DIR / item_id
        dest = download_image(url, dest_no_ext)
        if dest:
            note = f"（'{matched_title}' として検索一致）" if matched_title != name_en else ""
            print(f"  [OK] 保存: {dest} {note}")
            results.append({"id": item_id, "name_en": name_en, "status": "ok", "local_path": str(dest)})
        else:
            results.append({"id": item_id, "name_en": name_en, "status": "download_error", "local_path": ""})

        time.sleep(SLEEP_SEC)

    # 結果をCSVで書き出し（次工程でJSONデータのicon_pathに突合するため）
    out_csv = pathlib.Path("image_fetch_result.csv")
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name_en", "status", "local_path"])
        writer.writeheader()
        writer.writerows(results)

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\n完了: {ok_count}/{len(rows)} 件成功。結果は {out_csv} に出力しました。")


if __name__ == "__main__":
    main()
