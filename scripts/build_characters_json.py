"""
タスクC: characters.json 生成
- Fandom wikitext の infobox から franchise(set) / home_location(house) / unlock(unlocked_via) を抽出
- unlock_condition は日本語で簡潔に要約（Realm/Quest等の固有名詞＋仕組みのみ。原文prose直訳はしない）
- franchise は gamepedia の作品別区分（日本語）を採用
- icon_path は characters_status.csv から突合
- スキーマ: id, name_ja, name_en, franchise, unlock_condition, home_location,
            skill_assigned, owned, icon_path, memo
"""
import csv, json, re, pathlib

SCRATCH = pathlib.Path("/private/tmp/claude-501/-Users-yukimatsui-Desktop/067396cf-6901-4722-8005-5b974656d218/scratchpad")
raw = json.loads((SCRATCH / "raw_wikitext.json").read_text())
pages, rowmap = raw["pages"], raw["map"]

# gamepedia の作品別区分（日本語）
FRANCHISE = {
    "char_mickey":"ミッキー＆フレンズ","char_minnie":"ミッキー＆フレンズ","char_donald":"ミッキー＆フレンズ",
    "char_goofy":"ミッキー＆フレンズ","char_scrooge":"ミッキー＆フレンズ","char_daisy":"ミッキー＆フレンズ",
    "char_merlin":"王様の剣",
    "char_ursula":"リトル・マーメイド","char_ariel":"リトル・マーメイド","char_prince_eric":"リトル・マーメイド",
    "char_mother_gothel":"塔の上のラプンツェル","char_rapunzel":"塔の上のラプンツェル","char_flynn_rider":"塔の上のラプンツェル",
    "char_walle":"ウォーリー","char_eve":"ウォーリー",
    "char_maui":"モアナと伝説の海","char_moana":"モアナと伝説の海",
    "char_remy":"レミーのおいしいレストラン",
    "char_kristoff":"アナと雪の女王","char_anna":"アナと雪の女王","char_elsa":"アナと雪の女王","char_olaf":"アナと雪の女王",
    "char_scar":"ライオン・キング","char_simba":"ライオン・キング","char_nala":"ライオン・キング",
    "char_timon":"ライオン・キング","char_pumbaa":"ライオン・キング",
    "char_woody":"トイ・ストーリー","char_buzz_lightyear":"トイ・ストーリー",
    "char_stitch":"リロ・アンド・スティッチ",
    "char_mirabel":"ミラベルと魔法だらけの家",
    "char_fairy_godmother":"シンデレラ","char_cinderella":"シンデレラ",
    "char_vanellope":"シュガー・ラッシュ",
    "char_belle":"美女と野獣","char_beast":"美女と野獣","char_lumiere":"美女と野獣",
    "char_cogsworth":"美女と野獣","char_gaston":"美女と野獣",
    "char_jack_skellington":"ナイトメアー・ビフォア・クリスマス","char_sally":"ナイトメアー・ビフォア・クリスマス",
    "char_jafar":"アラジン","char_aladdin":"アラジン","char_jasmine":"アラジン",
    "char_sulley":"モンスターズ・インク","char_mike_wazowski":"モンスターズ・インク",
    "char_oswald":"オズワルド",
    "char_mulan":"ムーラン","char_mushu":"ムーラン",
    "char_tiana":"プリンセスと魔法のキス",
    "char_merida":"メリダとおそろしの森",
    "char_hades":"ヘラクレス","char_hercules":"ヘラクレス","char_phil":"ヘラクレス",
    "char_alice":"ふしぎの国のアリス","char_cheshire_cat":"ふしぎの国のアリス",
    "char_peter_pan":"ピーター・パン","char_tinker_bell":"ピーター・パン",
    "char_the_forgotten":"ドリームライト（DDVオリジナル）",
    "char_maleficent":"眠れる森の美女","char_aurora":"眠れる森の美女",
    "char_joy":"インサイド・ヘッド","char_sadness":"インサイド・ヘッド",
    "char_snow_white":"白雪姫",
    "char_tigger":"くまのプーさん",
    "char_cruella":"101匹わんちゃん",
    "char_lady":"わんわん物語","char_tramp":"わんわん物語",
    "char_pocahontas":"ポカホンタス",
}

def get_infobox(text):
    mobj = re.search(r"\{\{\s*[Ii]nfobox[^\|\}]*", text)
    if not mobj: return {}
    start = mobj.start(); depth=0; j=start; end=None
    while j < len(text)-1:
        if text[j:j+2]=="{{": depth+=1; j+=2; continue
        if text[j:j+2]=="}}":
            depth-=1; j+=2
            if depth==0: end=j; break
            continue
        j+=1
    b = text[start+2:end-2] if end else text[start+2:start+1500]
    # split top-level params
    depth=0; cur=""; parts=[]; k=0
    while k < len(b):
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

def strip_markup(s):
    s=re.sub(r"\{\{\s*il\s*\|\s*([^\|\}]+)\}\}", r"\1", s)   # {{il|X}} -> X
    s=re.sub(r"\{\{[^\|\}]*\|\s*([^\|\}]+)\}\}", r"\1", s)   # {{T|X}} -> X
    s=re.sub(r"\{\{\s*([^\|\}]+)\}\}", r"\1", s)             # {{X}} -> X
    s=re.sub(r"\[\[[^\|\]]*\|([^\]]+)\]\]", r"\1", s)        # [[a|b]] -> b
    s=re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)                  # [[X]] -> X
    s=s.replace("'''","").replace("''","").strip(" *\n")
    return s.strip()

def summarize_unlock(raw):
    """unlocked_via wikitext を日本語で簡潔に要約（仕組み＋固有名詞のみ）"""
    if not raw.strip():
        return ""
    realms=re.findall(r"\{\{\s*[Rr]ealm\s*\|\s*([^\|\}]+)\}\}", raw)
    quests=re.findall(r"\{\{\s*[Qq]uest\s*\|\s*([^\|\}]+)\}\}", raw)
    starpaths=re.findall(r"\{\{\s*[Ss]tar\s*[Pp]ath[^\|\}]*\|\s*([^\|\}]+)\}\}", raw)
    parts=[]
    if realms:
        parts.append("「" + "・".join(r.strip() for r in dict.fromkeys(realms)) + "」レルム")
    if quests:
        qs="・".join("「"+q.strip()+"」" for q in dict.fromkeys(quests))
        parts.append("クエスト" + qs)
    if starpaths:
        parts.append("スターパス「" + "・".join(s.strip() for s in dict.fromkeys(starpaths)) + "」")
    if parts:
        return "／".join(parts) + "で解放"
    # テンプレートが無い場合、素のテキストを軽く整形（prose直訳を避け短縮）
    plain=strip_markup(raw)
    plain=re.sub(r"\s+"," ",plain)
    return plain[:80]

# icon_path 突合
icon={}
for r in csv.DictReader(open("characters_status.csv",encoding="utf-8")):
    icon[r["id"]]=r["icon_path"]

rows=list(csv.DictReader(open("items_characters.csv",encoding="utf-8")))
chars=[]
incomplete=[]
for r in rows:
    iid=r["id"].strip()
    name_en=r["name_en"].strip()
    name_ja=r.get("name_ja","").strip()
    resolved=rowmap[iid]["resolved"]
    pg=pages.get(resolved,{"content":"","missing":True})
    params=get_infobox(pg["content"]) if not pg.get("missing") else {}
    home=strip_markup(params.get("house","")) if params else ""
    unlock=summarize_unlock(params.get("unlocked_via","")) if params else ""
    ip=icon.get(iid,"")
    if not params or (not unlock and not home):
        incomplete.append(iid)
    chars.append({
        "id":iid,
        "name_ja":name_ja,
        "name_en":name_en,
        "franchise":FRANCHISE.get(iid,""),
        "unlock_condition":unlock,
        "home_location":home,
        "skill_assigned":"",
        "owned":False,
        "icon_path":ip,
        "memo":"",
    })

pathlib.Path("data").mkdir(exist_ok=True)
out=pathlib.Path("data/characters.json")
out.write_text(json.dumps(chars,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("生成:",out,"／",len(chars),"体")
print("infobox欠落(要調査):",len(incomplete))
# 参考プレビュー（数体）
for c in chars[:6]:
    print(f"  {c['id']:20} {c['name_ja']:10} F={c['franchise']:14} home={c['home_location'][:18]:18} unlock={c['unlock_condition'][:40]}")