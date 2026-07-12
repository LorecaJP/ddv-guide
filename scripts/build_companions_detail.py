"""
オトモの「色違いごと」の 生息地・出現時間・好物 を gamepedia(archives/600) から取得して
companions.json を修正する。事実データ(場所名・時間・好物名)のみ使用。
"""
import requests, re, json

H={"User-Agent":"Mozilla/5.0 (personal-ddv-archive; individual use)"}
html=requests.get("https://gamepedia.jp/disneydreamlightvalley/archives/600",headers=H,timeout=25).text.replace("&amp;","&")
tables=re.findall(r"<table.*?</table>", html, re.S)
def cells(row): return [re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",c)).strip() for c in re.findall(r"<t[dh].*?</t[dh]>", row, re.S)]

DAYS=["月","火","水","木","金","土","日"]
def parse_schedule(text):
    # 「曜：値」を、次の「曜：」または末尾まで抽出（終日/時間帯を正しく取る）
    pairs=re.findall(r"([月火水木金土日])[：:]\s*(.+?)(?=\s*[月火水木金土日][：:]|$)", text)
    groups={}
    for day,v in pairs:
        v=v.strip()
        if v in ("×","x","✕","✖","-",""): continue
        groups.setdefault(v,[]).append(day)
    if not groups: return ""
    if len(groups)==1 and sum(len(ds) for ds in groups.values())==7:
        return "毎日 "+list(groups.keys())[0]
    return " / ".join(f"{''.join(ds)} {v}" for v,ds in groups.items())

variant={}   # (種, 色) -> {habitat, schedule}
sp_food={}   # 種 -> 好物(日本語)
cur_biome=""; cur_food=""
pending_sp=None

for t in tables:
    for row in re.findall(r"<tr.*?</tr>", t, re.S):
        cs=cells(row)
        if not cs: continue
        c0=cs[0]
        if c0=="出現場所" and len(cs)>1: cur_biome=cs[1]; continue
        if c0=="好物" and len(cs)>1: cur_food=cs[1]; pending_sp=None; continue
        # 変種行: "種 (色)"
        m=re.match(r"^([ァ-ヶー一-龠]{2,10})\s*[（(]\s*([^）)]{1,20})\s*[)）]\s*$", c0)
        rest=" ".join(cs[1:])
        if not m:
            # Eternity形式: cells[0]自体に schedule/場所が入る場合
            m2=re.match(r"^([ァ-ヶー一-龠]{2,10})\s*[（(]\s*([^）)]{1,20})\s*[)）]\s*(.*)$", c0, re.S)
            if not m2: continue
            sp,col,inline=m2.group(1),m2.group(2),m2.group(3)
            rest=(inline+" "+rest).strip()
        else:
            sp,col=m.group(1),m.group(2)
        col=col.strip()
        mh=re.search(r"出現場所[：:]\s*([^\s月火水木金土日]+)", rest)
        hab=mh.group(1) if mh else cur_biome
        sched=parse_schedule(rest)
        variant[(sp,col)]={"habitat":hab,"schedule":sched}
        if cur_food and sp not in sp_food and not mh and "異なる" not in cur_food:
            sp_food[sp]=cur_food

print(f"gamepedia 変種データ: {len(variant)}件")
print("種→好物:", sp_food)

# 英語→日本語 食べ物辞書（材料＋レシピ＋手動）
mats=json.load(open("src/lib/data/materials.json"))
recs=json.load(open("src/lib/data/recipes.json"))
en2ja={}
for m in mats:
    if m["name_ja"]: en2ja[m["name_en"]]=m["name_ja"]
for r in recs:
    if r["name_ja"]: en2ja[r["name_en"]]=r["name_ja"]
en2ja.update({
    "Pastry Cream and Fruits":"カスタードクリームとフルーツ","Fish Creole":"フィッシュクレオール","Bulgur Salad":"ブルグルサラダ",
    "Pure Ice":"ピュアアイス","Shiny Pure Ice":"きらめくピュアアイス",
    "Magma":"マグマ","Shiny Magma":"きらめくマグマ",
    "Green Passion Lily":"グリーンパッションリリー","Sunflower":"ヒマワリ",
    "Pink Bromeliad":"ピンクのブロメリア","Red Bromeliad":"レッドのブロメリア","Pink Houseleek":"ピンクのイワレンゲ",
})
def food_ja(f): return en2ja.get(f, f)

# companions 更新
p="src/lib/data/companions.json"; comps=json.load(open(p))
def norm(s): return s.replace(" ","").replace("　","")
vmap={(norm(k[0]),norm(k[1])):v for k,v in variant.items()}
hit=0; food_fix=0; miss=[]
for c in comps:
    key=(norm(c["gather_type"]),norm(c["color_ja"]))
    v=vmap.get(key)
    if v:
        c["habitat"]=v["habitat"]; c["source"]=v["habitat"]
        c["appearance_schedule"]=v["schedule"]
        hit+=1
    else:
        c.setdefault("appearance_schedule","")
        miss.append(c["name_ja"])
    # 好物: gamepediaの種好物を優先、無ければ既存を英→日で翻訳
    f=sp_food.get(c["gather_type"])
    if f:
        c["favorite_foods"]=[f]; food_fix+=1
    else:
        c["favorite_foods"]=[food_ja(x) for x in c.get("favorite_foods",[])]
json.dump(comps,open(p,"w"),ensure_ascii=False,indent=2)
print(f"\n生息地/時間 更新: {hit}/{len(comps)}  好物差し替え: {food_fix}")
if miss: print("未マッチ:", "、".join(miss))
print("\nサンプル:")
for c in comps:
    if c["gather_type"] in ("ペガサス","フクロウ","リス"):
        print(f"  {c['name_ja']:14} 生息地={c['habitat']:8} 好物={'/'.join(c['favorite_foods'])[:16]:16} 時間={c['appearance_schedule'][:40]}")
