"""
タスクC: recipes.json 生成（料理レシピ）
Fandom の一覧ページ Meals/<realm> の wikitable をパース。2形式に対応:
  (A) File形式:  |[[File:X.png|70x70px]]<br>[[Meal]]  / 材料 [[File:i.png|40x40px]]<br>[[Ing]]
  (B) テンプレ:  |{{IDb|Meal}}  / 材料 {{IDm|Ing}}
抽出: name_en / ingredients[] / sell(スターコイン) / energy / realm。stars=材料数(1-5)。
事実データのみ（説明文captionは取り込まない）。name_ja は後で gamepedia 突合。
スキーマ: id, name_ja, name_en, stars, ingredients[], sell_price_note, unlocked, memo
"""
import requests, re, json, pathlib, time

API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}

PAGES={
    "Meals/Dreamlight Valley":"ドリームライトバレー",
    "Meals/Eternity Isle":"エターニティアイル",
    "Meals/Storybook Vale":"ストーリーブックベール",
    "Meals/Wishblossom Mountains":"ウィッシュブロッサム山",
}

def fetch(title):
    d=requests.get(API,params={"action":"query","prop":"revisions","rvprop":"content",
        "rvslots":"main","titles":title,"format":"json"},headers=H,timeout=30).json()
    for _,pg in d["query"]["pages"].items():
        if "missing" in pg: return ""
        return pg["revisions"][0]["slots"]["main"]["*"]
    return ""

def nonfile_link(cell):
    for inner in re.findall(r"\[\[([^\]]+)\]\]", cell):
        if inner.lower().startswith("file:"):
            continue
        return inner.split("|")[-1].strip()
    return ""

def parse_page(text, realm_ja):
    out=[]
    for row in re.split(r"\n\|-", text):
        is_file = "70x70px" in row
        is_tmpl = "{{IDb" in row
        if not (is_file or is_tmpl):
            continue
        # 料理名
        if is_tmpl:
            mn=re.search(r"\{\{IDb\|([^}|]+)\}\}", row)
        else:
            mn=re.search(r"70x70px[^\]]*\]\]\s*<br>\s*\[\[([^\]|]+)", row)
        if not mn:
            continue
        name=mn.group(1).strip()

        ingredients=[]; sell=""; energy=""
        for cell in re.split(r"\n\|", row):
            idm=re.findall(r"\{\{IDm\|([^}|]+)\}\}", cell)
            if idm:
                ingredients.extend(x.strip() for x in idm)
            elif ("x40px" in cell) and ("Empty.png" not in cell) and ("IDb" not in cell):
                t=nonfile_link(cell)
                if t and t.lower()!="empty":
                    ingredients.append(t)
            ms=re.search(r"[Ss]tarcoin\s*\}\}\s*\*?\s*([\d,]+\+?)", cell)
            if ms: sell=ms.group(1).replace(",","")
            me=re.search(r"[Ee]nergy\s*\}\}\s*\*?\s*([\d,]+\+?)", cell)
            if me: energy=me.group(1).replace(",","")

        # 順序維持で重複除去
        seen=set(); ing=[]
        for i in ingredients:
            if i not in seen:
                seen.add(i); ing.append(i)
        stars=max(1,min(5,len(ing))) if ing else 0
        slug=re.sub(r"[^a-z0-9]+","_",name.lower()).strip("_")
        out.append({
            "id":f"recipe_{slug}","name_ja":"","name_en":name,"stars":stars,
            "ingredients":ing,
            "sell_price_note":(f"{sell} スターコイン" if sell else ""),
            "energy":energy,"realm":realm_ja,"unlocked":False,"memo":"",
        })
    return out

all_recipes=[]; seen_ids=set()
for page,realm in PAGES.items():
    recs=parse_page(fetch(page),realm)
    print(f"{page}: {len(recs)} 件")
    for r in recs:
        if r["id"] in seen_ids: continue
        seen_ids.add(r["id"]); all_recipes.append(r)
    time.sleep(1.0)

# realm / energy は memo に畳み込み（スキーマ外情報を保持）
for r in all_recipes:
    ex=[]
    if r["realm"]: ex.append(f"入手: {r['realm']}")
    if r["energy"]: ex.append(f"エナジー {r['energy']}")
    r["memo"]=" / ".join(ex)

fields=["id","name_ja","name_en","stars","ingredients","sell_price_note","unlocked","memo"]
clean=[{k:r[k] for k in fields} for r in all_recipes]
pathlib.Path("data").mkdir(exist_ok=True)
pathlib.Path("data/recipes.json").write_text(json.dumps(clean,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

from collections import Counter
def cnt(k): return sum(1 for r in clean if r[k])
print(f"\n合計 {len(clean)} 件 → data/recipes.json")
print("  ingredients有:",cnt("ingredients")," sell有:",cnt("sell_price_note"))
print("  stars分布:",dict(sorted(Counter(r['stars'] for r in clean).items())))
print("  空材料の料理:",[r["name_en"] for r in clean if not r["ingredients"]][:20])
print("\n  プレビュー:")
for r in clean[:10]:
    print(f"   ★{r['stars']} {r['name_en'][:24]:24} 材料={' / '.join(r['ingredients'])[:46]:46} 売={r['sell_price_note']}")
