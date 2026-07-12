"""
新規レシピを recipes.json に追加。
- gamepedia新規85件: 分類あり / realm空欄(出典に無い) / 日本語名・材料・星・売値あり
- ハニーグローの森12件: destructoid+simplegameguide由来 / realm=ハニーグローの森 / 日本語名は暫定訳
✏️(unlocked/memo)は新規なので初期値。
"""
import json, re
mine=json.load(open("src/lib/data/recipes.json"))
existing_ja={r["name_ja"] for r in mine if r["name_ja"]}
existing_ids={r["id"] for r in mine}

def slug(s):
    return "recipe_"+re.sub(r"[^a-z0-9]+","_", s.lower()).strip("_")[:40]
def clean(s): return s.replace(" "," ").replace("&nbsp;"," ").strip()
def fmt_sell(gp_sell):
    m=re.search(r"([\d,]+)", gp_sell or "")
    return f"{m.group(1)}+ スターコイン" if m else ""

# --- 1) gamepedia新規 ---
newgp=json.load(open("scripts/merge_report.json"))["new"]
added=0
NOTE_MARK=("フェスティバル","レシピのようです")
for g in newgp:
    nm=clean(g["name_ja"])
    if not nm or nm in existing_ja: continue
    ings=[clean(x) for x in g["ingredients_ja"]]
    memo=""
    # 材料欄に紛れた注記を除去してmemoへ
    real_ings=[]
    for x in ings:
        if any(k in x for k in NOTE_MARK): memo=x
        elif x: real_ings.append(x)
    rid=slug(g["name_ja"]);
    if rid in existing_ids: rid=rid+f"_{added}"
    existing_ids.add(rid)
    mine.append({
        "id":rid,"name_ja":nm,"name_en":"","stars":g["stars"],
        "ingredients":[],"ingredients_ja":real_ings,
        "category":g["category"],"realm":"",
        "sell_price_note":fmt_sell(g.get("sell")),
        "unlocked":False,"memo":memo,
    })
    existing_ja.add(nm); added+=1
print(f"gamepedia新規 追加:{added}")

# --- 2) ハニーグローの森 12件 ---
HG_ING={"Milk":"ミルク","Golden Honey":"ゴールデンハニー","Sweet Chestnuts":"甘い栗","Sweet Chestnut":"甘い栗",
"Acorn Snail":"どんぐりカタツムリ","Any Fruit":"果物類","Any Grain":"穀物類","Plush Fish":"プラッシュフィッシュ",
"Any Vegetable":"野菜類","Any Protein":"タンパク質類","Mushroom":"キノコ","Truffle":"トリュフ","Sweet Jelly":"甘いゼリー",
"Pufflebud Pods":"パフルバッドの実","Tree Resin":"木の樹脂","Juniper Berry":"ジュニパーベリー","Butter":"バター",
"Egg":"タマゴ","Golden Pattypan":"ゴールデンパティパン","Parsnip":"パースニップ","Carrot":"ニンジン",
"Any Spice":"スパイス類","Any Fish":"魚類","Any Sweet":"糖類"}
def ing_ja(lst): return [HG_ING.get(x,x) for x in lst]
CAT={"Appetizer":"前菜","Entree":"主菜","Dessert":"デザート"}
HG=[
 ("Warm Milk and Honey","温かいミルクとハチミツ","Appetizer",2,"344",["Milk","Golden Honey"]),
 ("Honeycrunch Bar","ハニークランチバー","Appetizer",2,"107",["Sweet Chestnuts","Golden Honey"]),
 ("Sweet Acorn Porridge","甘いどんぐりのポリッジ","Appetizer",3,"119",["Acorn Snail","Any Fruit","Any Grain"]),
 ("Honey-Glazed Plush Fish","プラッシュフィッシュのハニーグレーズ","Entree",3,"1300",["Plush Fish","Any Vegetable","Golden Honey"]),
 ("Blustery Day Soup","風の強い日のスープ","Appetizer",4,"226",["Any Protein","Mushroom","Truffle","Golden Honey"]),
 ("Honey Macarons","ハニーマカロン","Dessert",4,"802",["Golden Honey","Sweet Jelly","Any Grain","Sweet Chestnuts"]),
 ("Honey Triffle","ハニートライフル","Dessert",4,"239",["Pufflebud Pods","Golden Honey","Tree Resin","Juniper Berry"]),
 ("Brunchfast","ブランチファスト","Dessert",4,"1300",["Sweet Jelly","Butter","Egg","Any Fruit"]),
 ("Rabbit's Garden Pie","ラビットのガーデンパイ","Entree",5,"323",["Golden Pattypan","Parsnip","Pufflebud Pods","Carrot","Any Grain"]),
 ("Toasted Picnic Sandwich","トーストピクニックサンドイッチ","Entree",5,"173",["Golden Honey","Parsnip","Any Protein","Tree Resin","Any Spice"]),
 ("Foresty Quiche","森のキッシュ","Entree",5,"248",["Any Fish","Any Protein","Juniper Berry","Truffle","Golden Pattypan"]),
 ("Pooh's Birthday Cake","プーさんのバースデーケーキ","Dessert",5,"112",["Golden Honey","Any Sweet","Any Protein","Any Fruit","Any Grain"]),
]
hg_added=0
for en,ja,cat,stars,sell,ings in HG:
    if ja in existing_ja: continue
    mine.append({
        "id":slug("hg_"+en),"name_ja":ja,"name_en":en,"stars":stars,
        "ingredients":ings,"ingredients_ja":ing_ja(ings),
        "category":CAT[cat],"realm":"ハニーグローの森",
        "sell_price_note":f"{sell}+ スターコイン",
        "unlocked":False,"memo":"ハニーグローの森（くまのプーさんパック）。日本語名は暫定訳",
    })
    existing_ja.add(ja); hg_added+=1
print(f"ハニーグローの森 追加:{hg_added}")

json.dump(mine, open("src/lib/data/recipes.json","w"), ensure_ascii=False, indent=2)
from collections import Counter
print("総レシピ数:", len(mine))
print("realm内訳:", dict(Counter(r.get("realm") or "(空)" for r in mine)))
print("分類内訳:", dict(Counter(r.get("category") or "(空)" for r in mine)))
