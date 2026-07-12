"""
Fandom 'Characters' 一覧ページのギャラリー（File:X.png|link=CharName）から
未取得キャラの肖像を取得する。個人利用・非公開(Cloudflare Access)前提の参照データ。
"""
import requests, re, json, pathlib, time
API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}
OUT=pathlib.Path("public/images/characters"); OUT.mkdir(parents=True, exist_ok=True)
CT={"image/webp":".webp","image/png":".png","image/jpeg":".jpg","image/gif":".gif"}
def norm(s): return "".join(c.lower() for c in s if c.isalnum())

# 一覧ページ取得
d=requests.get(API,params={"action":"query","prop":"revisions","rvprop":"content","rvslots":"main","titles":"Characters","format":"json"},headers=H,timeout=25).json()
txt=list(d["query"]["pages"].values())[0]["revisions"][0]["slots"]["main"]["*"]

# ギャラリー行: File:<file>|link=<charname>[|...]
entries=re.findall(r"File:([^|\n\]]+\.(?:png|jpg|jpeg|webp))\s*\|\s*link=([^|\n\]]+)", txt, re.I)
by_link={}   # norm(charname) -> file
for f,link in entries:
    by_link[norm(link)] = f.strip()
# 保険: File名そのものからも引けるように（link無しでも File:Name.png がキャラ名のことが多い）
by_file={}
for f,_ in entries:
    base=re.sub(r"\.(png|jpg|jpeg|webp)$","",f,flags=re.I)
    by_file[norm(base)] = f.strip()
print(f"ギャラリー抽出: {len(entries)}件 / link一意 {len(by_link)}")

def file_url(fname):
    d=requests.get(API,params={"action":"query","titles":f"File:{fname}","prop":"imageinfo","iiprop":"url","iiurlwidth":500,"format":"json"},headers=H,timeout=20).json()
    for _,pg in d.get("query",{}).get("pages",{}).items():
        info=pg.get("imageinfo",[])
        if info: return info[0].get("thumburl") or info[0].get("url")
    return None

p="src/lib/data/characters.json"
chars=json.load(open(p))
missing=[c for c in chars if not c["icon_path"]]
print(f"未取得: {len(missing)}体")
ok=[]; fail=[]
for c in missing:
    key=norm(c["name_en"])
    f = by_link.get(key) or by_file.get(key)
    if not f:
        fail.append(c["name_ja"]); print(f"  ✗ {c['name_ja']}（{c['name_en']}）: ギャラリーに無し"); continue
    try:
        url=file_url(f)
        if not url: fail.append(c["name_ja"]); print(f"  ✗ {c['name_ja']}: URL取れず({f})"); continue
        r=requests.get(url,headers=H,timeout=25); r.raise_for_status()
        ext=CT.get(r.headers.get("Content-Type","").split(";")[0].strip().lower()) or ".png"
        dest=OUT/f"{c['id']}{ext}"; dest.write_bytes(r.content)
        c["icon_path"]=f"images/characters/{c['id']}{ext}"
        ok.append(c["name_ja"]); print(f"  ✓ {c['name_ja']} ← File:{f}")
    except requests.RequestException as e:
        fail.append(c["name_ja"]); print(f"  ✗ {c['name_ja']}: {e}")
    time.sleep(0.5)

json.dump(chars,open(p,"w"),ensure_ascii=False,indent=2)
print(f"\n成功 {len(ok)} / 失敗 {len(fail)}")
if fail: print("残り:", "、".join(fail))
print("画像付き合計:", sum(1 for c in chars if c["icon_path"]),"/",len(chars))
PY
