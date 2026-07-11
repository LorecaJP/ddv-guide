"""
① name_ja 強化（精度優先）
1. gamepedia レシピ表から (JA名, ★, 売値, JA材料) を取得（固有名詞・数値のみ）
2. (★,売値)一意＋材料一致で recipes を確定マッチ
3. 確定マッチの「EN材料↔JA材料」対応から、制約伝播で EN→JA 材料辞書を成長
   （既知の対応を除外して残り1対1になったら新規確定＝誤りにくい）
4. その辞書で materials / crops の name_ja を補完
5. 曖昧だったレシピも、翻訳材料の一致で候補を1つに絞れたら name_ja 確定
"""
import requests, re, json, pathlib
from collections import defaultdict, Counter

H={"User-Agent":"Mozilla/5.0 (personal-ddv-archive; individual use)"}
URL="https://gamepedia.jp/disneydreamlightvalley/archives/21"

def to_kata(s): return "".join(chr(ord(c)+0x60) if "ぁ"<=c<="ゖ" else c for c in s)
def nrm(s):
    s=s.replace("類","").replace("の実","").strip()
    return to_kata(s)

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
            ms=re.search(r"★\s*(\d)",stats); ml=re.search(r"売値[：:]\s*([\d,]+)",stats)
            if not name or not ms or not ml: continue
            ings=re.findall(r"・?\s*([^\n×・]+?)\s*×\s*\d", ing_txt)
            out.append({"ja":name,"star":int(ms.group(1)),"sell":int(ml.group(1).replace(",","")),
                        "ings":[i.strip() for i in ings]})
    # 重複除去
    seen=set(); o2=[]
    for r in out:
        k=(r["ja"],r["star"],r["sell"])
        if k in seen: continue
        seen.add(k); o2.append(r)
    return o2

gp=fetch_rows()
gp_by=defaultdict(list)
for r in gp: gp_by[(r["star"],r["sell"])].append(r)

recs=json.load(open("data/recipes.json"))
mats=json.load(open("data/materials.json"))
crops=json.load(open("data/crops.json"))

# 既知 EN->JA（materials の name_ja）
en2ja={m["name_en"]:m["name_ja"] for m in mats if m["name_ja"]}

def sell_of(r):
    m=re.search(r"(\d+)",r["sell_price_note"]); return int(m.group(1)) if m else -1
rec_by=defaultdict(list)
for r in recs: rec_by[(r["stars"],sell_of(r))].append(r)

def verify(rec_ings, gp_ings):
    tgt=[nrm(en2ja[i]) for i in rec_ings if i in en2ja]
    if not tgt: return None
    g=[nrm(x) for x in gp_ings]; gj="".join(g)
    hit=sum(1 for t in tgt if any(t in x or x in t for x in g) or t in gj)
    if hit==0 and len(tgt)>=2: return False
    return True

# --- 確定マッチ（recipe -> gp row）---
matched={}  # recipe id -> gp row
for r in recs:
    key=(r["stars"],sell_of(r))
    c=gp_by.get(key,[])
    if len(c)==1 and len(rec_by[key])==1 and verify(r["ingredients"],c[0]["ings"]) is not False:
        matched[r["id"]]=c[0]
        r["name_ja"]=c[0]["ja"]

# --- 制約伝播で EN->JA 材料辞書を成長 ---
rec_by_id={r["id"]:r for r in recs}
for _ in range(6):
    grew=0
    for rid,g in matched.items():
        en=rec_by_id[rid]["ingredients"]
        ja=g["ings"]
        # 既知でマッチしたJAを除外
        used_ja=set()
        unk_en=[]
        for e in en:
            if e in en2ja:
                je=nrm(en2ja[e])
                # そのJAが gp 材料にあれば消費
                for x in ja:
                    if nrm(x)==je or je in nrm(x) or nrm(x) in je:
                        used_ja.add(x); break
            else:
                unk_en.append(e)
        rem_ja=[x for x in ja if x not in used_ja]
        if len(unk_en)==1 and len(rem_ja)==1:
            e=unk_en[0]; j=rem_ja[0].strip()
            if e not in en2ja and j:
                en2ja[e]=j; grew+=1
    if not grew: break

# --- materials / crops へ反映 ---
def fill(items):
    n=0
    for it in items:
        if not it["name_ja"] and it["name_en"] in en2ja:
            it["name_ja"]=en2ja[it["name_en"]]; n+=1
    return n
mn=fill(mats); cn=fill(crops)

# --- 曖昧レシピを「グループ内1対1マッチング」で解決（安全） ---
def overlap(rec, c):
    tgt=[nrm(en2ja[i]) for i in rec["ingredients"] if i in en2ja]
    if not tgt: return -1, 0
    g=[nrm(x) for x in c["ings"]]; gj="".join(g)
    hit=sum(1 for t in tgt if any(t in x or x in t for x in g) or t in gj)
    return hit, len(tgt)

# 未確定レシピを (★,売値) グループにまとめる
groups=defaultdict(list)
for r in recs:
    if not r["name_ja"]:
        groups[(r["stars"],sell_of(r))].append(r)

# 既に使われた gp 名（確定済み）は候補から除外
used_ja=set(r["name_ja"] for r in recs if r["name_ja"])
resolved=0
for key,rs in groups.items():
    cands=[c for c in gp_by.get(key,[]) if c["ja"] not in used_ja]
    if not cands: continue
    # スコア行列（recipe×candidate）
    pairs=[]
    for r in rs:
        for c in cands:
            hit,tot=overlap(r,c)
            if tot>0 and hit>0:
                pairs.append((hit/tot, hit, r, c))
    pairs.sort(key=lambda x:(x[0],x[1]), reverse=True)
    taken_r=set(); taken_c=set()
    for ratio,hit,r,c in pairs:
        if id(r) in taken_r or id(c) in taken_c: continue
        # 相互ベスト＆十分な一致（過半数以上）なら採用
        if ratio>=0.5:
            r["name_ja"]=c["ja"]; taken_r.add(id(r)); taken_c.add(id(c)); used_ja.add(c["ja"]); resolved+=1

json.dump(recs,open("data/recipes.json","w"),ensure_ascii=False,indent=2)
json.dump(mats,open("data/materials.json","w"),ensure_ascii=False,indent=2)
json.dump(crops,open("data/crops.json","w"),ensure_ascii=False,indent=2)

print(f"EN→JA 材料辞書: {len(en2ja)} 語")
print(f"recipes name_ja: {sum(1 for r in recs if r['name_ja'])}/{len(recs)} （曖昧解決 +{resolved}）")
print(f"materials name_ja: {sum(1 for m in mats if m['name_ja'])}/{len(mats)} （+{mn}）")
print(f"crops name_ja: {sum(1 for c in crops if c['name_ja'])}/{len(crops)} （+{cn}）")
print("新規辞書の例:", dict(list(en2ja.items())[-12:]))
