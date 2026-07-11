"""
残りカテゴリのデータ生成（事実データのみ・説明prose不使用）
- crops:   materials(栽培) から導出
- prices:  recipes の売値から導出
- expansions: 既知事実で手構築(2)
- updates:    既知の主要バージョンで手構築(最小)
- facilities: materials の入手元(店)＋既知施設から導出
- quests:  Fandom Category:Quests(128) の infobox から type/prereq/reward
- events:  Fandom Category:Events(39) の infobox から period
- bugs/tips/faq: 空（ユーザー入力用の器）
"""
import requests, re, json, pathlib, time
API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}
def api(p):
    p={**p,"format":"json"}; r=requests.get(API,params=p,headers=H,timeout=30); r.raise_for_status(); return r.json()
def slug(s,p): return p+re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

recs=json.load(open("data/recipes.json"))
mats=json.load(open("data/materials.json"))

# ---- crops（materials の 栽培 を農作物として）----
crops=[]
for m in mats:
    if "栽培" in m["obtain_method"]:
        crops.append({
            "id":slug(m["name_en"],"crop_"),
            "name_ja":m["name_ja"],"name_en":m["name_en"],
            "category":m["category"],
            "grow_area":m["obtain_method"].replace("栽培・","").replace("栽培",""),
            "used_in_recipes":m["used_in_recipes"],
            "note":"","planted_count":0,"harvested_total":0,"memo":"",
        })
pathlib.Path("data/crops.json").write_text(json.dumps(crops,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ---- prices（recipes の売値）----
prices=[]
for r in recs:
    m=re.search(r"(\d+)",r["sell_price_note"])
    if not m: continue
    prices.append({
        "id":slug(r["name_en"],"price_"),
        "item_id":r["id"],"item_name":(r["name_ja"] or r["name_en"]),
        "sell_location":"レストラン／ショップ（料理）",
        "base_price":int(m.group(1)),
        "notes":"食材の質で変動（+）","memo":"",
    })
pathlib.Path("data/prices.json").write_text(json.dumps(prices,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ---- expansions（既知事実）----
expansions=[
    {"id":"exp_eternity_isle","name_ja":"永遠の島（A Rift in Time）","release_date":"2023-12-05",
     "price":"有料DLC","included_realms":["永遠の島","失われしタイムスクエア"],
     "required_progress":"本編をある程度進行","owned":False,"progress_notes":""},
    {"id":"exp_storybook_vale","name_ja":"物語の谷（The Storybook Vale）","release_date":"2025-01-01",
     "price":"有料DLC","included_realms":["物語の谷"],
     "required_progress":"本編をある程度進行","owned":False,"progress_notes":""},
]
pathlib.Path("data/expansions.json").write_text(json.dumps(expansions,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ---- updates（最小の器：ユーザーが追記する前提の代表例）----
updates=[
    {"id":"upd_placeholder","version":"（例）","release_date":"","title":"アップデート履歴はここに追記",
     "summary":"Fandom の Version history から随時追加してください。","new_characters":[],
     "new_features":[],"bug_fixes":[],"source_url":"https://disneydreamlightvalley.fandom.com/wiki/Version_history",
     "personal_notes":""},
]
pathlib.Path("data/updates.json").write_text(json.dumps(updates,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ---- facilities（materials の入手元＝店 を施設として集約）----
fac_names=set()
for m in mats:
    for tok in re.split(r"[・/]", m["obtain_method"]):
        tok=tok.strip()
        if "で購入" in tok or "露店" in tok or "レストラン" in tok or "店" in tok:
            fac_names.add(tok.replace("で購入",""))
facilities=[]
for n in sorted(fac_names):
    if not n: continue
    facilities.append({
        "id":slug(n,"fac_"),"name_ja":n,"type":"ショップ／施設",
        "unlock_condition":"","restock_time":"","note":"materials の入手元から自動集約",
        "visited_today":False,"memo":"",
    })
pathlib.Path("data/facilities.json").write_text(json.dumps(facilities,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ---- Fandom fetch: quests / events ----
def members(cat):
    out=[]; cont={}
    while True:
        p={"action":"query","list":"categorymembers","cmtitle":f"Category:{cat}","cmlimit":"500","cmtype":"page"}; p.update(cont)
        d=api(p); out+=[m["title"] for m in d["query"]["categorymembers"]]
        if "continue" in d: cont=d["continue"]
        else: break
    return out

def infobox(text):
    mobj=re.search(r"\{\{\s*[Ii]nfobox[^\|\}]*", text)
    if not mobj: return {}
    s=mobj.start(); depth=0; j=s; end=None
    while j<len(text)-1:
        if text[j:j+2]=="{{": depth+=1; j+=2; continue
        if text[j:j+2]=="}}":
            depth-=1; j+=2
            if depth==0: end=j; break
            continue
        j+=1
    b=text[s+2:end-2] if end else text[s+2:s+1500]
    depth=0; cur=""; parts=[]; k=0
    while k<len(b):
        two=b[k:k+2]
        if two in ("{{","[["): depth+=1; cur+=two; k+=2; continue
        if two in ("}}","]]"): depth-=1; cur+=two; k+=2; continue
        if b[k]=="|" and depth==0: parts.append(cur); cur=""; k+=1; continue
        cur+=b[k]; k+=1
    parts.append(cur)
    d={}
    for p in parts[1:]:
        if "=" in p:
            key,_,val=p.partition("="); d[key.strip()]=val.strip()
    return d

def clean(s):
    s=re.sub(r"\{\{[^\|\}]*\|([^\}]+)\}\}", r"\1", s)
    s=re.sub(r"\{\{([^\}]+)\}\}", r"\1", s)
    s=re.sub(r"\[\[[^\|\]]*\|([^\]]+)\]\]", r"\1", s)
    s=re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s=re.sub(r"<[^>]+>"," ",s)
    s=s.replace("'''","").replace("*"," ").strip()
    return re.sub(r"\s+"," ",s)[:120]

def batch_wikitext(titles):
    res={}
    for i in range(0,len(titles),40):
        d=api({"action":"query","prop":"revisions","rvprop":"content","rvslots":"main",
               "titles":"|".join(titles[i:i+40]),"redirects":1})
        for _,pg in d["query"]["pages"].items():
            if "missing" in pg: res[pg["title"]]=""; continue
            revs=pg.get("revisions",[]); res[pg["title"]]=revs[0]["slots"]["main"]["*"] if revs else ""
        time.sleep(1.0)
    return res

# quests
qtitles=members("Quests")
qtext=batch_wikitext(qtitles)
quests=[]
for t,txt in qtext.items():
    ib=infobox(txt)
    quests.append({
        "id":slug(t,"quest_"),"name_ja":"","type":clean(ib.get("type","")) or "クエスト",
        "prerequisite":clean(ib.get("prerequisite","") or ib.get("prereq","") or ib.get("previous","")),
        "reward":clean(ib.get("rewards","") or ib.get("reward","")),
        "completed":False,"completed_date":"","memo":t,  # memo に英名
    })
pathlib.Path("data/quests.json").write_text(json.dumps(quests,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# events
etitles=members("Events")
etext=batch_wikitext(etitles)
events=[]
for t,txt in etext.items():
    ib=infobox(txt)
    period=clean(ib.get("date","") or ib.get("duration","") or ib.get("time",""))
    events.append({
        "id":slug(t,"event_"),"name_ja":t,"period":period,"related_events":[],
        "participated":False,"reward_progress":"","memo":("スターパス" if "Star Path" in t else "イベント"),
    })
pathlib.Path("data/events.json").write_text(json.dumps(events,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# bugs/tips/faq: 空
for name in ["bugs","tips","faq"]:
    pathlib.Path(f"data/{name}.json").write_text("[]\n",encoding="utf-8")

print("crops:",len(crops)," prices:",len(prices)," expansions:",len(expansions),
      " facilities:",len(facilities)," quests:",len(quests)," events:",len(events),
      " updates:",len(updates)," (bugs/tips/faq=空)")
