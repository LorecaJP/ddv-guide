"""
新オトモ種（願い咲く牧場DLC）を追加: ガチョウ / スカンク / スイートなハチ
gamepedia の生息地・出現時間・色、Fandomの画像を使用。事実データのみ。
"""
import requests, json, re, pathlib
API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}
CT={"image/webp":".webp","image/png":".png","image/jpeg":".jpg"}
OUT=pathlib.Path("public/images/companions")

# (name_en, 種JA, 色JA, 生息地, 出現時間, 画像ファイル名 or None)
NEW=[
 # ガチョウ
 ("Golden Goose","ガチョウ","ゴールド","探求の谷","毎日：7時~8時","Golden Goose.png"),
 ("True North Goose","ガチョウ","トゥルーノース","牧場の高原","火・木・土：終日","True North Goose.png"),
 ("Black Goose","ガチョウ","ブラック","銀ヶ峰","毎日：5時~11時","Black Goose.png"),
 ("Blue Goose","ガチョウ","ブルー","願いの小径","毎日：18時~20時","Blue Goose.png"),
 ("Classic Goose","ガチョウ","ベーシック","願い咲く牧場","月・水・金・日：終日",None),
 # スカンク
 ("Brown Skunk","スカンク","ブラウン","ペイズリーパーク","月・水・金・日：12時~24時","Brown Skunk.png"),
 ("White Skunk","スカンク","ホワイト","モディッシュ湿地","火・木・土・日：12時~24時","White Skunk.png"),
 ("Patterned Skunk","スカンク","パターン","オートクチュール台地","毎日：終日（曇り/雨のみ）","Patterned Skunk.png"),
 ("Classic Skunk","スカンク","ベーシック","ランウェイリバー","毎日：0時~12時","Skunk.png"),
 # スイートなハチ（画像なし）
 ("Pink Bee","スイートなハチ","ピンク","妖精の平原","毎日：終日",None),
 ("Blue Bee","スイートなハチ","ブルー","ハチミツの滝","毎日：終日（曇り/晴れのみ）",None),
 ("White Bee","スイートなハチ","ホワイト","100エーカーの野原","毎日：20時~24時",None),
 ("Classic Bee","スイートなハチ","ベーシック","サンデーショア","毎日：7時~20時",None),
]
def slug(s): return "comp_"+re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")
def file_url(f):
    d=requests.get(API,params={"action":"query","titles":f"File:{f}","prop":"imageinfo","iiprop":"url","iiurlwidth":300,"format":"json"},headers=H,timeout=20).json()
    for _,pg in d["query"]["pages"].items():
        if "missing" in pg: return None
        i=pg.get("imageinfo",[])
        if i: return i[0].get("thumburl") or i[0].get("url")
    return None

comps=json.load(open("src/lib/data/companions.json"))
have={c["id"] for c in comps}
added=0; imgs=0
for en,sp,col,hab,sched,fname in NEW:
    cid=slug(en)
    if cid in have: print(f"  skip {en}"); continue
    icon=""
    if fname:
        url=file_url(fname)
        if url:
            r=requests.get(url,headers=H,timeout=25); r.raise_for_status()
            ext=CT.get(r.headers.get("Content-Type","").split(";")[0].strip().lower()) or ".png"
            (OUT/f"{cid}{ext}").write_bytes(r.content); icon=f"images/companions/{cid}{ext}"; imgs+=1
    comps.append({"id":cid,"name_ja":f"{sp}（{col}）","name_en":en,"gather_type":sp,"color_ja":col,
        "source":hab,"habitat":hab,"favorite_foods":[],"appearance_schedule":sched,
        "owned":False,"friendship_level":0,"is_equipped":False,"icon_path":icon,"memo":""})
    added+=1; print(f"  ✓ {sp}（{col}） 画像{'有' if icon else '無'}")
json.dump(comps,open("src/lib/data/companions.json","w"),ensure_ascii=False,indent=2)
print(f"\n追加 {added}体（画像{imgs}）／ オトモ合計 {len(comps)}体")
from collections import Counter
print("種ごと:", dict(Counter(c['gather_type'] for c in comps)))
