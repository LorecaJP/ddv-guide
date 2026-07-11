"""
タスク: animals.json（動物=クリッター種） / companions.json（オトモ=色違い46体）生成
- Fandom 'Critters' 記事の餌付け表をパース: 種 / 生息地(biome) / 好物
- 色違い(companions)は各種にひもづけ、source=生息地, gather_type=種
- companions の画像は File:<変種>.png を images/companions/ に保存
事実データ(固有名詞・好物・生息地)のみ使用。説明prose(approach手順)は取り込まない。
"""
import requests, re, json, pathlib, time

API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}
OUTIMG=pathlib.Path("images/companions"); OUTIMG.mkdir(parents=True, exist_ok=True)
CT={"image/webp":".webp","image/png":".png","image/jpeg":".jpg","image/gif":".gif"}

def api(p):
    p={**p,"format":"json"}; r=requests.get(API,params=p,headers=H,timeout=30); r.raise_for_status(); return r.json()

txt=list(api({"action":"query","prop":"revisions","rvprop":"content","rvslots":"main","titles":"Critters"})["query"]["pages"].values())[0]["revisions"][0]["slots"]["main"]["*"]

SPECIES_WORDS=["Sea Turtle","Baby Dragon","Fox","Squirrel","Raccoon","Rabbit","Sunbird",
               "Crocodile","Capybara","Monkey","Turtle","Cobra","Owl","Pegasus","Raven"]
def species_of(variant):
    for w in sorted(SPECIES_WORDS,key=len,reverse=True):
        if variant.endswith(w): return w
    return ""
def canon_word(name):
    n=name.replace("Pegasi","Pegasus")  # 不規則複数
    for w in sorted(SPECIES_WORDS,key=len,reverse=True):
        if w in n: return w
    return n

# 餌付け表: 行に x50px]]<br>'''種''' を含む
species=[]  # {en, habitat, foods[]}
for row in re.split(r"\n\|-", txt):
    if "x50px" not in row or "'''" not in row: continue
    msp=re.search(r"x50px\]\]\s*<br>\s*'''([^']+)'''", row)
    if not msp: continue
    name=msp.group(1).strip()
    cells=re.split(r"\n\|", row)
    habitat=""; foods=[]
    for ci,c in enumerate(cells):
        # 好物: {{il|Food}} だが変種名(=・Fox等)は除外
        for il in re.findall(r"\{\{il\|([^\}|]+)\}\}", c):
            if not species_of(il) and ci>=1:  # 変種名でない = 好物
                if il not in foods: foods.append(il)
        # 生息地: bare template {{Biome}}（il/File/energy等を除く）
        if not habitat:
            for t in re.findall(r"\{\{([^\}|]+)\}\}", c):
                tl=t.strip()
                if tl.lower() in ("il","energy","starcoin"): continue
                if tl.startswith("il|") or tl.startswith("File:"): continue
                if species_of(tl): continue
                # biomeらしきもの（il でない bare template）
                if ci>=1 and tl not in foods:
                    habitat=tl; break
    species.append({"en":name,"habitat":habitat,"foods":foods})

print("種(species)抽出:", len(species))
for s in species:
    print(f"   {s['en']:12} 生息地={s['habitat']:20} 好物={s['foods']}")

# 変種(companions)
variants=sorted(set(v for v in re.findall(r"\{\{il\|([^\}|]+)\}\}", txt) if species_of(v)))
print("\n変種(companions):", len(variants))

# 種名→データ（canon_word で単数/複数/不規則を吸収）
sp_by={}
for s in species:
    sp_by[canon_word(s["en"])]=s

def slug(s,p): return p+re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

# animals（種レベル）
JA_SP={"Fox":"キツネ","Squirrel":"リス","Raccoon":"アライグマ","Rabbit":"ウサギ",
       "Sea Turtle":"ウミガメ","Turtle":"カメ","Sunbird":"タイヨウチョウ","Crocodile":"ワニ",
       "Capybara":"カピバラ","Monkey":"サル","Cobra":"コブラ","Owl":"フクロウ",
       "Pegasus":"ペガサス","Baby Dragon":"ベビードラゴン","Raven":"ワタリガラス"}
animals=[]
for s in species:
    spw=canon_word(s["en"])
    animals.append({
        "id":slug(s["en"],"animal_"),
        "name_ja":JA_SP.get(spw,""),
        "name_en":s["en"],
        "favorite_foods":s["foods"],
        "habitat":s["habitat"],
        "appearance_schedule":"",
        "becomes_companion":"はい（餌付けして仲間にできる）",
        "fed_today":False,"unlocked_as_companion":False,"memo":"",
    })
pathlib.Path("data/animals.json").write_text(json.dumps(animals,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# companions（変種）＋画像取得
def file_url(fname):
    d=api({"action":"query","titles":f"File:{fname}","prop":"imageinfo","iiprop":"url","iiurlwidth":300})
    for _,pg in d.get("query",{}).get("pages",{}).items():
        info=pg.get("imageinfo",[])
        if info: return info[0].get("thumburl") or info[0].get("url")
    return None

companions=[]
ok_img=0
for v in variants:
    spw=species_of(v)
    sp=sp_by.get(canon_word(v),{})
    icon=""
    url=file_url(f"{v}.png")
    if url:
        try:
            r=requests.get(url,headers=H,timeout=25); r.raise_for_status()
            ext=CT.get(r.headers.get("Content-Type","").split(";")[0].strip().lower()) or ".png"
            iid=slug(v,"comp_")
            dest=OUTIMG/f"{iid}{ext}"; dest.write_bytes(r.content)
            icon=str(dest); ok_img+=1
        except requests.RequestException:
            pass
    companions.append({
        "id":slug(v,"comp_"),"name_ja":"","name_en":v,
        "gather_type":JA_SP.get(spw,spw),
        "source":sp.get("habitat","") or "野生クリッター",
        "owned":False,"friendship_level":0,"is_equipped":False,
        "icon_path":icon,"memo":(f"好物: {'/'.join(sp.get('foods',[]))}" if sp.get('foods') else ""),
    })
    time.sleep(0.6)

pathlib.Path("data/companions.json").write_text(json.dumps(companions,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"\nanimals: {len(animals)}  companions: {len(companions)}（画像 {ok_img}）")
