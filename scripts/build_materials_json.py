"""
タスクA(素材) : materials.json 生成
- recipes.json の材料からユニーク180件を抽出
- Fandom の item infobox から category(種別) / obtain_via(入手方法) を抽出（事実データ）
- used_in_recipes は recipes.json から逆引きリンク（ID連携）
- name_ja は共通食材の確実な訳のみ付与（DDV固有名詞は空＝後で gamepedia 突合）
スキーマ: id, name_ja, name_en, category, obtain_method, used_in_recipes[], stock_count, memo
"""
import requests, re, json, pathlib, time

API="https://disneydreamlightvalley.fandom.com/api.php"
H={"User-Agent":"personal-ddv-archive/1.0 (individual use; contact: N/A)"}

recs=json.load(open("data/recipes.json"))
# ユニーク材料（出現順）
mats=[]
seen=set()
for r in recs:
    for ing in r["ingredients"]:
        if ing not in seen:
            seen.add(ing); mats.append(ing)

# レシピで「任意の該当素材」を指す調理カテゴリ
META={"Vegetable","Seafood","Fish","Fruit","Sweets","Spices & Herbs","Protein","Dairy","Oil","Ice"}

CAT_JA={
    "grains":"穀物","grain":"穀物","vegetables":"野菜","vegetable":"野菜",
    "fruits":"果物","fruit":"果物","fish":"魚","seafood":"魚介",
    "ingredients":"食材","pantry":"パントリー食材","sweets":"甘味料",
    "spices":"香辛料","spices & herbs":"香辛料・ハーブ","herbs":"ハーブ",
    "dairy":"乳製品","dairy & oils":"乳製品・油",
}
OBTAIN_JA={
    "gardening":"栽培","farming":"栽培","fishing":"釣り","digging":"発掘",
    "foraging":"採取","mining":"採掘","crafting":"クラフト",
    "chez remy":"シェ・レミーで購入","goofy's stall":"グーフィーの露店で購入",
    "pantry":"パントリー","cooking":"料理","restaurant":"レストラン",
    "scrooge's store":"スクルージの店で購入","remy's restaurant":"レミーのレストラン",
    "the wishing well":"願いの井戸","meals":"料理",
}

# 確実に訳せる共通食材のみ（DDV固有名詞は空にして gamepedia 突合待ち）
NAME_JA={
    "Wheat":"小麦","Egg":"卵","Eggs":"卵","Cheese":"チーズ","Tomato":"トマト","Onion":"玉ねぎ",
    "Garlic":"ニンニク","Milk":"牛乳","Butter":"バター","Lemon":"レモン","Rice":"米",
    "Potato":"じゃがいも","Corn":"トウモロコシ","Cucumber":"キュウリ","Lettuce":"レタス",
    "Carrot":"ニンジン","Cabbage":"キャベツ","Spinach":"ほうれん草","Broccoli":"ブロッコリー",
    "Cauliflower":"カリフラワー","Eggplant":"ナス","Zucchini":"ズッキーニ","Pumpkin":"カボチャ",
    "Bell Pepper":"ピーマン","Chili Pepper":"唐辛子","Mushroom":"キノコ","Asparagus":"アスパラガス",
    "Leek":"ネギ","Celery":"セロリ","Beans":"豆","Green Beans":"サヤインゲン","Peanut":"ピーナッツ",
    "Almonds":"アーモンド","Oats":"オーツ麦","Barley":"大麦","Soya":"大豆","Ginger":"ショウガ",
    "Basil":"バジル","Oregano":"オレガノ","Mint":"ミント","Dill":"ディル","Cumin":"クミン",
    "Cinnamon":"シナモン","Nutmeg":"ナツメグ","Paprika":"パプリカ","Vanilla":"バニラ",
    "Black Pepper":"黒コショウ","Honey":"ハチミツ","Sugarcane":"サトウキビ","Vanilla":"バニラ",
    "Cocoa Bean":"カカオ豆","Coffee Bean":"コーヒー豆","Pork":"豚肉","Poultry":"鶏肉",
    "Venison":"鹿肉","Salmon":"サーモン","Tuna":"マグロ","Cod":"タラ","Herring":"ニシン",
    "Shrimp":"エビ","Crab":"カニ","Lobster":"ロブスター","Oyster":"カキ","Clam":"アサリ",
    "Octopus":"タコ","Squid":"イカ","Scallop":"ホタテ","Mussel":"ムール貝","Seaweed":"海藻",
    "Lemon":"レモン","Apple":"リンゴ","Banana":"バナナ","Cherry":"サクランボ","Grapes":"ブドウ",
    "Blueberry":"ブルーベリー","Raspberry":"ラズベリー","Strawberry":"イチゴ","Melon":"メロン",
    "Pineapple":"パイナップル","Coconut":"ココナッツ","Rhubarb":"ルバーブ","Beetroot":"ビーツ",
    "Radish":"ラディッシュ","Turnip":"カブ","Yam":"ヤムイモ","Okra":"オクラ","Perch":"パーチ",
    "Bass":"バス","Tilapia":"ティラピア","Bream":"ブリーム","Sole":"シタビラメ","Carp":"コイ",
    "Koi":"錦鯉","Anglerfish":"アンコウ","Swordfish":"メカジキ","Salt Crystal":"塩の結晶",
    "Rice":"米","Milk":"牛乳","Plain Yogurt":"プレーンヨーグルト","Olives":"オリーブ",
    "Radicchio":"ラディッキオ","Brussels Sprout":"芽キャベツ","Bamboo":"タケノコ",
    "Dates":"デーツ","Persimmon":"柿","Grapes":"ブドウ","Pineapple":"パイナップル",
}

def fetch_batch(titles):
    d=requests.get(API,params={"action":"query","prop":"revisions","rvprop":"content",
        "rvslots":"main","titles":"|".join(titles),"redirects":1,"format":"json"},
        headers=H,timeout=30).json()
    q=d.get("query",{})
    redir={r["from"]:r["to"] for r in q.get("redirects",[])}
    pages={}
    for _,pg in q.get("pages",{}).items():
        if "missing" in pg:
            pages[pg["title"]]=None
        else:
            revs=pg.get("revisions",[])
            pages[pg["title"]]=revs[0]["slots"]["main"]["*"] if revs else ""
    return pages, redir

def get_infobox(text):
    if not text: return {}
    mobj=re.search(r"\{\{\s*[Ii]nfobox[^\|\}]*", text)
    if not mobj: return {}
    start=mobj.start(); depth=0; j=start; end=None
    while j<len(text)-1:
        if text[j:j+2]=="{{": depth+=1; j+=2; continue
        if text[j:j+2]=="}}":
            depth-=1; j+=2
            if depth==0: end=j; break
            continue
        j+=1
    b=text[start+2:end-2] if end else text[start+2:start+1500]
    depth=0; cur=""; parts=[]; k=0
    while k<len(b):
        two=b[k:k+2]
        if two in ("{{","[["): depth+=1; cur+=two; k+=2; continue
        if two in ("}}","]]"): depth-=1; cur+=two; k+=2; continue
        if b[k]=="|" and depth==0: parts.append(cur); cur=""; k+=1; continue
        cur+=b[k]; k+=1
    parts.append(cur)
    params={}
    for p in parts[1:]:
        if "=" in p:
            key,_,val=p.partition("="); params[key.strip()]=val.strip()
    return params

def first_template(s):
    m=re.search(r"\{\{\s*([^\|\}]+)", s)
    return m.group(1).strip() if m else ""

def all_templates(s):
    return [t.strip() for t in re.findall(r"\{\{\s*([^\|\}]+)", s)]

def category_ja(params):
    for key in ("ingredient","type","category","collection"):
        if key in params and params[key]:
            t=first_template(params[key]).lower()
            if t in CAT_JA: return CAT_JA[t]
            # collection has "(Grains)" hint
            m=re.search(r"\(([^)]+)\)", params[key])
            if m and m.group(1).strip().lower() in CAT_JA:
                return CAT_JA[m.group(1).strip().lower()]
    return ""

def obtain_ja(params):
    raw=params.get("obtain_via","")
    if not raw: return ""
    methods=[]
    for t in all_templates(raw):
        tl=t.lower()
        if tl in OBTAIN_JA:
            methods.append(OBTAIN_JA[tl])
        elif tl not in ("energy","starcoin"):
            methods.append(t)  # 店名など固有名詞はそのまま
    # 重複除去・順序維持
    seen=set(); out=[]
    for m in methods:
        if m not in seen: seen.add(m); out.append(m)
    return "・".join(out)

# recipes 逆引き
recipe_by_ing={}
for r in recs:
    for ing in r["ingredients"]:
        recipe_by_ing.setdefault(ing,[]).append(r["id"])

# batch fetch
info={}
redirects_all={}
BATCH=40
real=[m for m in mats if m not in META]
for i in range(0,len(real),BATCH):
    pages,redir=fetch_batch(real[i:i+BATCH])
    info.update(pages); redirects_all.update(redir)
    time.sleep(1.0)

def slug(s): return "mat_"+re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

materials=[]
for name in mats:
    used=sorted(set(recipe_by_ing.get(name,[])))
    if name in META:
        materials.append({
            "id":slug(name),"name_ja":NAME_JA.get(name,""),"name_en":name,
            "category":"調理カテゴリ（任意の該当素材）",
            "obtain_method":"レシピで該当カテゴリの任意素材を使用",
            "used_in_recipes":used,"stock_count":0,"memo":"",
        })
        continue
    resolved=redirects_all.get(name,name)
    text=info.get(resolved) or info.get(name)
    params=get_infobox(text or "")
    materials.append({
        "id":slug(name),"name_ja":NAME_JA.get(name,""),"name_en":name,
        "category":category_ja(params),
        "obtain_method":obtain_ja(params),
        "used_in_recipes":used,"stock_count":0,"memo":"",
    })

pathlib.Path("data/materials.json").write_text(json.dumps(materials,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def cnt(k): return sum(1 for m in materials if m[k])
print(f"合計 {len(materials)} 素材 → data/materials.json")
print(f"  name_ja有:{cnt('name_ja')}  category有:{cnt('category')}  obtain有:{cnt('obtain_method')}  used_in有:{cnt('used_in_recipes')}")
print("\n  プレビュー:")
for m in materials[:12]:
    print(f"   {m['name_en'][:20]:20} ja={m['name_ja'] or '-':8} 種別={m['category'][:10]:10} 入手={m['obtain_method'][:24]:24} 使用レシピ数={len(m['used_in_recipes'])}")
