"""
未取得のキャラ画像を拾い直す（infobox image1 を直接取得する方式）。
characters.json の icon_path が空のキャラについて:
  1. Fandomページを解決（直接/リダイレクト、ダメなら検索で妥当な候補）
  2. infobox の image1 / image を取得 → File のURLを imageinfo で取得
  3. images/characters/<id>.<ext> に保存し、characters.json の icon_path を更新
個人利用・非公開（Cloudflare Access）前提の参照データ。説明文は取得しない。
"""
import requests, re, json, pathlib, time
API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}
OUT=pathlib.Path("public/images/characters"); OUT.mkdir(parents=True, exist_ok=True)
CT={"image/webp":".webp","image/png":".png","image/jpeg":".jpg","image/gif":".gif"}

def api(p):
    p={**p,"format":"json"}; r=requests.get(API,params=p,headers=H,timeout=25); r.raise_for_status(); return r.json()
def norm(s): return "".join(c.lower() for c in s if c.isalnum())

def get_wikitext(title):
    d=api({"action":"query","prop":"revisions","rvprop":"content","rvslots":"main","titles":title,"redirects":1})
    for _,pg in d["query"]["pages"].items():
        if "missing" in pg: return None,None
        revs=pg.get("revisions",[])
        return pg["title"], (revs[0]["slots"]["main"]["*"] if revs else "")
    return None,None

def infobox_image(wt):
    if not wt or "{{Infobox character" not in wt and "{{infobox character" not in wt.lower():
        # 画像だけでも拾えるように継続
        pass
    m=re.search(r"\|\s*image1?\s*=\s*([^\n|}]+)", wt or "")
    if not m: return None
    v=m.group(1).strip()
    v=re.sub(r"\{\{PAGENAME\}\}", "", v)
    v=re.sub(r"\[\[File:", "", v); v=v.replace("File:","")
    v=v.split("|")[0].strip().strip("[]")
    return v if v.lower().endswith((".png",".jpg",".jpeg",".webp",".gif")) else None

def search_pages(q):
    d=api({"action":"query","list":"search","srsearch":q,"srlimit":6})
    return [r["title"] for r in d.get("query",{}).get("search",[])]

def resolve(name):
    # 1) 直接
    title,wt=get_wikitext(name)
    if wt:
        img=infobox_image(wt)
        if img: return title,img
    # 2) 検索（キャラページ＆名前が妥当なもの）
    for cand in search_pages(name):
        base=re.sub(r"\s*\(.*?\)\s*","",cand)
        if norm(base)!=norm(name) and norm(name) not in norm(base):
            continue
        t,wt=get_wikitext(cand)
        if not wt: continue
        img=infobox_image(wt)
        if img: return t,img
    return None,None

def file_url(fname):
    d=api({"action":"query","titles":f"File:{fname}","prop":"imageinfo","iiprop":"url","iiurlwidth":500})
    for _,pg in d.get("query",{}).get("pages",{}).items():
        info=pg.get("imageinfo",[])
        if info: return info[0].get("thumburl") or info[0].get("url")
    return None

chars=json.load(open("src/lib/data/characters.json"))
missing=[c for c in chars if not c["icon_path"]]
print(f"未取得キャラ: {len(missing)}")
ok=[]; fail=[]
for c in missing:
    name=c["name_en"]; iid=c["id"]
    try:
        title,img=resolve(name)
        if not img:
            fail.append((name,"ページ/画像なし")); print(f"  ✗ {name}: 見つからず"); time.sleep(0.4); continue
        url=file_url(img)
        if not url:
            fail.append((name,f"file URL取得失敗({img})")); print(f"  ✗ {name}: URL取れず"); time.sleep(0.4); continue
        r=requests.get(url,headers=H,timeout=25); r.raise_for_status()
        ext=CT.get(r.headers.get("Content-Type","").split(";")[0].strip().lower()) or ".png"
        dest=OUT/f"{iid}{ext}"; dest.write_bytes(r.content)
        c["icon_path"]=f"images/characters/{iid}{ext}"
        ok.append(name); print(f"  ✓ {name} ← {title} / {img}")
    except requests.RequestException as e:
        fail.append((name,str(e)[:40])); print(f"  ✗ {name}: {e}")
    time.sleep(0.6)

json.dump(chars,open("src/lib/data/characters.json","w"),ensure_ascii=False,indent=2)
print(f"\n取得成功 {len(ok)} / 失敗 {len(fail)}")
if fail:
    print("失敗:", [f[0] for f in fail])
print("画像付きキャラ合計:", sum(1 for c in chars if c["icon_path"]), "/", len(chars))
