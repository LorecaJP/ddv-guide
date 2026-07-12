"""
オトモ(companions)を日本語化＆情報統合:
- 種(species)を gamepedia 表記に（例: Raven→カラス, Baby Dragon→ドラゴン）
- 色名を gamepedia の日本語に（Classic→ベーシック 等）
- name_ja = 「種名（色名）」、color_ja（並べ替え用）を付与
- 生息地(habitat, 日本語)と好物(favorite_foods, 日本語)を animals.json＋materials辞書から統合
"""
import json, re, pathlib

comps=json.load(open("src/lib/data/companions.json"))
animals=json.load(open("src/lib/data/animals.json"))
mats=json.load(open("src/lib/data/materials.json"))
food_ja={m["name_en"]:m["name_ja"] for m in mats if m["name_ja"]}

# 種: English species word → gamepedia 日本語
SPECIES_WORDS=["Sea Turtle","Baby Dragon","Fox","Squirrel","Raccoon","Rabbit","Sunbird",
               "Crocodile","Capybara","Monkey","Turtle","Cobra","Owl","Pegasus","Raven"]
SP_JA={"Fox":"キツネ","Squirrel":"リス","Raccoon":"アライグマ","Rabbit":"ウサギ",
       "Sea Turtle":"ウミガメ","Turtle":"ウミガメ","Sunbird":"タイヨウチョウ","Crocodile":"ワニ",
       "Capybara":"カピバラ","Monkey":"サル","Cobra":"コブラ","Owl":"フクロウ",
       "Pegasus":"ペガサス","Baby Dragon":"ドラゴン","Raven":"カラス"}
def species_of(name):
    for w in sorted(SPECIES_WORDS,key=len,reverse=True):
        if name.endswith(w): return w
    return ""

# 色: English → gamepedia 日本語（複合を優先。長い順にマッチ）
COLOR_JA={
    "Black and Brown":"ブラック&ブラウン","Black and Gray":"ブラック&グレー","Black and White":"ブラック&ホワイト",
    "Red and Beige":"レッド&ベージュ","Red and White Striped":"レッド&ホワイトストライプ",
    "Blue and Red Striped":"ブルー&レッドストライプ","Green and White Striped":"グリーン&ホワイトストライプ",
    "Yellow and Purple Striped":"イエロー&パープルストライプ","Blue Striped":"ブルーストライプ",
    "Gray Spotted":"グレーのまだら","Pink Spotted":"ピンクのまだら",
    "Classic":"ベーシック","Calico":"マダラ","Scary":"凶暴",
    "Golden":"ゴールド","Emerald":"エメラルド","Orchid":"オーキッド","Turquoise":"ターコイズ",
    "Black":"ブラック","Blue":"ブルー","Red":"レッド","White":"ホワイト","Brown":"ブラウン",
    "Gray":"グレー","Beige":"ベージュ","Purple":"パープル","Green":"グリーン","Yellow":"イエロー",
    "Pink":"ピンク","Peach":"ピーチ","Dark":"ダーク","Light":"ライト",
}
def color_ja(color_en):
    if color_en in COLOR_JA: return COLOR_JA[color_en]
    # 単語ごとに置換（保険）
    out=color_en
    for en in sorted(COLOR_JA,key=len,reverse=True):
        out=out.replace(en, COLOR_JA[en])
    return out

# 生息地 English → 日本語（gamepedia の出現場所）
HAB_JA={
    "Frosted Heights":"氷の高原","Peaceful Meadow":"平和の草原","Dazzle Beach":"輝きの浜辺",
    "Forest of Valor":"勇気の森","Glade of Trust":"信頼の湿地","Sunlit Plateau":"太陽の台地",
    "Forgotten Lands":"忘却の地","Plaza":"プラザ","The Ruins":"遺跡","The Promenade":"ラグーン",
    "The Wastes":"辺境の地","The Library of Lore":"萬話の館","The Fiery Plains":"炎の平原",
    "The Wild Woods":"荒れの森","The Docks":"波止場",
}

# 種 → animals（habitat, foods）※複数形/不規則(Pegasi)対応で「含む」判定
an_by_sp={}
for a in animals:
    n=a["name_en"].replace("Pegasi","Pegasus")
    for w in sorted(SPECIES_WORDS,key=len,reverse=True):
        if w in n:
            an_by_sp[w]=a; break

for c in comps:
    sp=species_of(c["name_en"])
    color_en=c["name_en"][:-len(sp)].strip() if sp else c["name_en"]
    sja=SP_JA.get(sp, c["gather_type"])
    cja=color_ja(color_en)
    c["gather_type"]=sja
    c["color_ja"]=cja
    c["name_ja"]=f"{sja}（{cja}）"
    # 生息地・好物を種から
    a=an_by_sp.get(sp,{})
    hab_en=a.get("habitat","")
    c["habitat"]=HAB_JA.get(hab_en, hab_en)
    foods=[food_ja.get(f,f) for f in a.get("favorite_foods",[])]
    c["favorite_foods"]=foods
    c["source"]=c["habitat"]  # source も日本語生息地に
    c["memo"]=""              # memoの好物流用をやめる

json.dump(comps,open("src/lib/data/companions.json","w"),ensure_ascii=False,indent=2)
print(f"companions {len(comps)}体 日本語化。")
from collections import Counter
print("種ごと:", dict(Counter(c["gather_type"] for c in comps)))
print("\nサンプル:")
for c in comps[:8]:
    print(f"  {c['name_ja']:16} 生息地={c['habitat']:8} 好物={'/'.join(c['favorite_foods'])[:30]}")
print("\n色名（ユニーク・五十音）:", "、".join(sorted(set(c['color_ja'] for c in comps))))
