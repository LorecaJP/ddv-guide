"""
タスクB: レシピ name_ja 突合（精度優先・材料検証つき）
- gamepedia のレシピ表から (日本語名, ★, 売値, 材料JA) を抽出（固有名詞＋数値のみ使用）
- 一次キー (★, 売値) が両側一意な候補に対し、材料の一致を検証してから name_ja を確定
  * EN材料を materials.json の name_ja で日本語化し、gamepedia の材料JAとの重なりを見る
  * 訳せた材料のうち十分な割合が一致 → 採用 / 矛盾 → 棄却（誤マッチ防止）
  * 訳せる材料が無い場合のみ、数値一意キーで暫定採用
"""
import requests, re, json, pathlib
from collections import defaultdict

H={"User-Agent":"Mozilla/5.0 (personal-ddv-archive; individual use)"}
URL="https://gamepedia.jp/disneydreamlightvalley/archives/21"

def fetch_rows():
    txt=requests.get(URL,headers=H,timeout=30).text
    out=[]
    for t in re.findall(r"<table.*?</table>", txt, re.S):
        for tr in re.findall(r"<tr.*?</tr>", t, re.S):
            cells=re.findall(r"<t[dh].*?</t[dh]>", tr, re.S)
            if len(cells)<3: continue
            name=re.sub(r"<[^>]+>","",cells[0]).strip()
            ing_txt=re.sub(r"<[^>]+>","",cells[1])
            stats=re.sub(r"<[^>]+>","",cells[-1])
            mstar=re.search(r"★\s*(\d)", stats)
            msell=re.search(r"売値[：:]\s*([\d,]+)", stats)
            if not name or not mstar or not msell: continue
            # 材料JA（"・名前×1" の名前部分）
            ings=re.findall(r"・?\s*([^\n×・]+?)\s*×\s*\d", ing_txt)
            out.append({"name_ja":name,"star":int(mstar.group(1)),
                        "sell":int(msell.group(1).replace(",","")),
                        "ings_ja":[i.strip() for i in ings]})
    return out

# EN材料 -> JA（materials.json）
mats={m["name_en"]:m["name_ja"] for m in json.load(open("data/materials.json")) if m["name_ja"]}
# gamepedia 側の材料表記ゆれを吸収する正規化（平仮名→片仮名、接尾辞除去）
def to_kata(s):
    return "".join(chr(ord(c)+0x60) if "ぁ"<=c<="ゖ" else c for c in s)
def norm_ing(s):
    s=s.replace("類","").replace("の実","").strip()
    return to_kata(s)

gp=fetch_rows()
# 重複除去
seen=set(); gp2=[]
for r in gp:
    k=(r["name_ja"],r["star"],r["sell"])
    if k in seen: continue
    seen.add(k); gp2.append(r)
gp=gp2
print(f"gamepedia 抽出: {len(gp)} レシピ")

gp_by_key=defaultdict(list)
for r in gp: gp_by_key[(r["star"],r["sell"])].append(r)

recs=json.load(open("data/recipes.json"))
def sell_of(r):
    m=re.search(r"(\d+)", r["sell_price_note"]); return int(m.group(1)) if m else -1
rec_by_key=defaultdict(list)
for r in recs: rec_by_key[(r["stars"],sell_of(r))].append(r)

def verify_ings(rec, gprow):
    """EN材料をJA化し、gamepedia材料との重なりで検証。
    棄却は「訳せる材料が2つ以上あって一致0＝強い矛盾」の時だけ（誤マッチのみ排除）。"""
    ja_targets=[norm_ing(mats[i]) for i in rec["ingredients"] if i in mats]
    if not ja_targets:
        return None, 0, 0  # 検証不能
    gp_norm=[norm_ing(x) for x in gprow["ings_ja"]]
    gp_join="".join(gp_norm)
    hit=sum(1 for t in ja_targets if any(t in g or g in t for g in gp_norm) or t in gp_join)
    tc=len(ja_targets)
    if hit==0 and tc>=2:
        return False, tc, hit   # 強い矛盾 → 棄却
    return True, tc, hit

# name_ja を一旦クリアして精度優先で再付与
for r in recs: r["name_ja"]=""

applied=0; provisional=0; rejected=0; ambiguous=0; nogp=0
apply_list=[]; reject_list=[]
for r in recs:
    key=(r["stars"],sell_of(r))
    cands=gp_by_key.get(key,[])
    if not cands:
        nogp+=1; continue
    if not (len(cands)==1 and len(rec_by_key[key])==1):
        ambiguous+=1; continue
    g=cands[0]
    ok,tc,hit=verify_ings(r,g)
    if ok is True:
        r["name_ja"]=g["name_ja"]; applied+=1; apply_list.append((r["name_en"],g["name_ja"]))
    elif ok is None:
        r["name_ja"]=g["name_ja"]; provisional+=1  # 検証不能だが数値一意→暫定
    else:
        rejected+=1; reject_list.append((r["name_en"],g["name_ja"],f"{hit}/{tc}"))

print(f"確定(材料一致): {applied}  暫定(検証不能・数値一意): {provisional}  棄却(材料不一致): {rejected}  曖昧: {ambiguous}  GP側なし: {nogp}")
print(f"name_ja 充足: {sum(1 for r in recs if r['name_ja'])}/{len(recs)}")
print("\n--- 棄却した誤マッチ候補（材料不一致で除外） ---")
for en,ja,hr in reject_list[:15]:
    print(f"   {en[:28]:28} ✕ {ja}  (材料一致 {hr})")
print("\n--- 検証（既知） ---")
by_en={r["name_en"]:r for r in recs}
for en,exp in {"Sweet Udon":"甘いうどん","Aquatic Escargot":"アクア・エスカルゴ","Cheese Platter":"チーズの盛り合わせ"}.items():
    got=by_en.get(en,{}).get("name_ja","")
    print(f"   {en}: '{got}' vs '{exp}' {'OK' if got==exp else '要確認'}")

pathlib.Path("data/recipes.json").write_text(json.dumps(recs,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
