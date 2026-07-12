"""
gamepedia の料理一覧(468種・前菜/主菜/デザートのセクション付き)を既存 recipes.json にマージ。
- 既存レシピ: 日本語名・分類を補完（英語名は不要方針）。unlocked等の✏️は保持。
- 新規レシピ: 追加（category=セクション, realm は判明分のみ）。
突合: 日本語名一致 → (★+材料英語集合)一致 → 高重複フォールバック。
事実データのみ使用。
"""
import json, re, os
from collections import defaultdict

gp=json.load(open("scripts/gp_recipes_cat.json"))
mine=json.load(open("src/lib/data/recipes.json"))

def entok(s): return re.sub(r"[ &'\-\.]","",s).lower()
COLL_EN={"spicesherbs":"@spice","spices":"@spice","vegetable":"@veg","seafood":"@sea","fish":"@fish",
"fruit":"@fruit","sugar":"@sugar","sweets":"@sugar","dairy":"@dairy","grain":"@grain","poultry":"@poultry"}
# gamepedia表記(日本語)→英語トークン
GP2EN={
"タマネギ":"onion","きゅうり":"cucumber","ジャガイモ":"potato","タマゴ":"egg","ミルク":"milk","生姜":"ginger","ショウガ":"ginger",
"トマト":"tomato","レモン":"lemon","ニンニク":"garlic","チーズ":"cheese","バター":"butter","小麦":"wheat","米":"rice","レタス":"lettuce",
"ニシン":"herring","エビ":"shrimp","サーモン":"salmon","マグロ":"tuna","海藻":"seaweed","ナス":"eggplant","ズッキーニ":"zucchini",
"カキ":"oyster","ホタテ":"scallop","バジル":"basil","ミント":"mint","ヨーグルト":"yogurt","アーモンド":"almonds","カボチャ":"pumpkin",
"ディル":"dill","トウガラシ":"chilipepper","トウモロコシ":"corn","ココナッツ":"coconut","バニラ":"vanilla","サトウキビ":"sugarcane",
"カカオ豆":"cocoabean","大豆":"soya","オーツ麦":"oats","オレガノ":"oregano","クミン":"cumin","黒コショウ":"blackpepper","キノコ":"mushroom",
"サボテンの実":"cactoberries","アガベ":"agave","竹":"bamboo","メカジキ":"swordfish","コイ":"carp","ヘダイ":"bream","スズキ":"bass",
"ティラピア":"tilapia","ウォールアイ":"walleye","イカ":"squid","ピラニア":"piranha","ピラルク":"pirarucu","柿":"persimmon",
"ウミマスカット":"seagrapes","ルバーブ":"rhubarb","ルパーブ":"rhubarb","黄金のリンゴ":"goldenapple","アンブロシア":"ambrosia",
"菜の花":"canola","フサスグリ":"redcurrants","ドリームライトの実":"dreamlightfruit","サバ":"mackerel","グースベリー":"gooseberry",
"食用ホオズキ":"capegooseberry","ボタンマッシュルーム":"buttonmushroom","ニンジン":"carrot","針山ピーチ":"pincushionpeach",
"精白丸麦":"pearlybarley","スコップ鳥のタマゴ":"shovelbirdeggs","サテンヒレのベタ":"satinfinnedbetta","チアシード":"chiaseeds",
"うずまきイチゴ":"spiralstrawberries","ピッポカンポス":"hippocampus","ラッパマイマイ":"trumpetsnail","トビウオ":"flyingfish",
"芽キャベツ":"brusselssprout","冥界のトビハゼ":"stygianmudskipper","ヤツメウナギ":"lamprey","イナズマのスパイス":"lightningspice",
"輝く青いヒトデ":"brilliantbluestarfish","ロボット魚":"robotfish","バナナ":"banana","リンゴ":"apple","ブルーベリー":"blueberry",
"ラズベリー":"raspberry","ホウレンソウ":"spinach","ハマグリ":"clam","カニ":"crab","スイカ":"watermelon","イチゴ":"strawberry",
"ブラックベリー":"blackberry","ハチミツ":"honey","オクラ":"okra","長ネギ":"leek","マシュマロ":"marshmallow","スラッシュ":"slush",
}
def cen(i):
    t=entok(i); return COLL_EN.get(t,t)
def cja(i):
    s=re.sub(r"[（(][^）)]*[）)]","",i).strip(); s2=s.replace("類","")
    coll={"野菜":"@veg","シーフード":"@sea","魚":"@fish","果物":"@fruit","フルーツ":"@fruit","糖":"@sugar","乳製品":"@dairy","穀物":"@grain","鶏":"@poultry"}
    if s2 in coll: return coll[s2]
    return GP2EN.get(s, GP2EN.get(s2, "JA:"+s2))

def mset(r): return frozenset(cen(x) for x in r["ingredients"])
def gset(g): return frozenset(cja(x) for x in g["ingredients_ja"])

# 手動対応表（英語名→gamepedia日本語名）: 集合材料で曖昧になる少数を確定
MANUAL={
"Hearty Salad":"ヘルシーサラダ","Tasty Salad":"おいしいサラダ","Mediterranean Salad":"地中海風サラダ",
"Tasty Veggies":"おいしい野菜","Hors d'Oeuvres":"オードブル","Cape Gooseberry Smoothie":"食用ホオズキスムージー",
"Squid Sashimi":"イカの刺し身","Grilled Veggie Platter":"野菜のグリルの盛り合わせ",
}
by_name={r["name_ja"]:r for r in mine if r["name_ja"]}
by_en={r["name_en"]:r for r in mine if r["name_en"]}
gp_by_ja={g["name_ja"]:g for g in gp}
sigidx=defaultdict(list)
for r in mine: sigidx[(r["stars"], mset(r))].append(r)

matched={}       # mine.id -> gp
gp_matched=set() # gp name_ja
# 0) 手動対応
for en,ja in MANUAL.items():
    if en in by_en and ja in gp_by_ja:
        matched[by_en[en]["id"]]=gp_by_ja[ja]; gp_matched.add(ja)
# 1) 名前一致
for g in gp:
    if g["name_ja"] in gp_matched: continue
    if g["name_ja"] in by_name and by_name[g["name_ja"]]["id"] not in matched:
        matched[by_name[g["name_ja"]]["id"]]=g; gp_matched.add(g["name_ja"])
# 2) シグネチャ一致
for g in gp:
    if g["name_ja"] in gp_matched: continue
    h=[r for r in sigidx.get((g["stars"], gset(g)),[]) if r["id"] not in matched]
    if h:
        matched[h[0]["id"]]=g; gp_matched.add(g["name_ja"])
# 3) 高重複フォールバック(★不問, 共有>=材料数-1 かつ >=2)
remaining_mine=[r for r in mine if r["id"] not in matched]
gp_left=[g for g in gp if g["name_ja"] not in gp_matched]
for r in sorted(remaining_mine, key=lambda x:-len(x["ingredients"])):
    me=mset(r); best=None; bs=1
    for g in gp_left:
        if g["name_ja"] in gp_matched: continue
        sh=len(me & gset(g))
        need=max(2, len(me)-1)
        if sh>=need and sh>bs: bs=sh; best=g
    if best:
        matched[r["id"]]=best; gp_matched.add(best["name_ja"])

print(f"既存 {len(mine)} 件中 マッチ:{len(matched)} 未マッチ:{len(mine)-len(matched)}")
unm=[r for r in mine if r["id"] not in matched]
print("未マッチ既存(英語名):", [r["name_en"] for r in unm])

# 補完適用: 既存レシピに 日本語名(空なら)・分類 を埋める
filled_ja=0
for r in mine:
    g=matched.get(r["id"])
    if not g: continue
    if not r["name_ja"]:
        r["name_ja"]=g["name_ja"]; filled_ja+=1
    if not r.get("category"):
        r["category"]=g["category"]
print(f"日本語名を補完:{filled_ja}件")

# 新規 = gpでマッチしなかったもの
newgp=[g for g in gp if g["name_ja"] not in gp_matched]
from collections import Counter
print(f"新規追加:{len(newgp)} 内訳:", dict(Counter(g['category'] for g in newgp)))
json.dump({"matched_count":len(matched),"unmatched_mine":[r["name_en"] for r in unm],
           "new":newgp}, open("scripts/merge_report.json","w"), ensure_ascii=False, indent=2)
# mine(補完済み)も保存
json.dump(mine, open("src/lib/data/recipes.json","w"), ensure_ascii=False, indent=2)
print("recipes.json を補完保存（新規はまだ未追加。realm判定後に追加）")
