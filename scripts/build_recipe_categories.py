"""
recipes.json に「category（前菜/主菜/デザート）」と「ingredients_ja（材料の日本語名）」を追加。
- カテゴリ: Fandom の Meals/<realm> 一覧ページのセクション見出し(Appetizers/Entrees/Desserts)から判定
- 材料日本語: materials.json の name_en→name_ja で翻訳
事実データのみ使用。
"""
import requests, re, json
API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}
PAGES=["Meals/Dreamlight Valley","Meals/Eternity Isle","Meals/Storybook Vale","Meals/Wishblossom Mountains"]
CAT_JA={"appetizer":"前菜","appetizers":"前菜","entree":"主菜","entrees":"主菜","dessert":"デザート","desserts":"デザート"}

def fetch(t):
    d=requests.get(API,params={"action":"query","prop":"revisions","rvprop":"content","rvslots":"main","titles":t,"format":"json"},headers=H,timeout=30).json()
    for _,pg in d["query"]["pages"].items():
        if "missing" in pg: return ""
        return pg["revisions"][0]["slots"]["main"]["*"]
    return ""

name2cat={}
for page in PAGES:
    txt=fetch(page)
    # セクション見出しで分割: ===[[File:...]] Appetizers ===
    parts=re.split(r"\n===+([^=\n]+?)===+", txt)
    # parts: [pre, head1, body1, head2, body2, ...]
    cur=None
    for i,seg in enumerate(parts):
        if i==0: continue
        if i%2==1:  # 見出し
            h=re.sub(r"\[\[[^\]]+\]\]","",seg).strip().lower()
            cur=None
            for k,v in CAT_JA.items():
                if k in h: cur=v; break
        else:  # 本文
            if not cur: continue
            for row in re.split(r"\n\|-", seg):
                mn=re.search(r"\{\{IDb\|([^}|]+)\}\}", row) or re.search(r"70x70px[^\]]*\]\]\s*<br>\s*\[\[([^\]|]+)", row)
                if mn: name2cat[mn.group(1).strip()]=cur

print("カテゴリ判定:", len(name2cat), "件")

# 材料 EN→JA
mats=json.load(open("src/lib/data/materials.json"))
en2ja={m["name_en"]:m["name_ja"] for m in mats if m["name_ja"]}

recs=json.load(open("src/lib/data/recipes.json"))
catcount={}
for r in recs:
    r["category"]=name2cat.get(r["name_en"],"")
    r["ingredients_ja"]=[en2ja.get(i,i).replace("&amp;","&") for i in r["ingredients"]]
    catcount[r["category"] or "(未分類)"]=catcount.get(r["category"] or "(未分類)",0)+1
json.dump(recs,open("src/lib/data/recipes.json","w"),ensure_ascii=False,indent=2)
print("カテゴリ内訳:", catcount)
# 材料翻訳サンプル
for r in recs[:5]:
    print(f"  {r['name_ja'] or r['name_en']}: {r['category']} / 材料={r['ingredients_ja']}")
