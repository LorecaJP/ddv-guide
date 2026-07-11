"""
② facilities / updates 拡充 ＋ ④ tips/faq/bugs を参照リンク集に
- facilities: 既知の主要ショップ/施設（事実データ：名称・機能）
- updates: Fandom Version History の版番号＋各ページへのリンク（本文は転載しない）
- tips/faq/bugs: 参照元ページへの外部リンク（本文コピーはしない＝著作権配慮）
"""
import json, pathlib

# ② facilities（既知の主要ショップ/施設）
facilities=[
    {"id":"fac_scrooge_store","name_ja":"スクルージの店","type":"ショップ（家具・装飾・アイテム）",
     "unlock_condition":"スクルージのクエストで開店","restock_time":"日替わりで品揃え更新",
     "note":"日替わり商品あり。家具・服・素材などを販売","visited_today":False,"memo":""},
    {"id":"fac_chez_remy","name_ja":"レミーのレストラン（シェ・レミー）","type":"レストラン／パントリー",
     "unlock_condition":"レミーのレルム＆クエスト","restock_time":"—",
     "note":"チーズ・卵・牛乳などパントリー食材を購入できる","visited_today":False,"memo":""},
    {"id":"fac_goofy_stall","name_ja":"グーフィーの露店","type":"ショップ（種・食材）",
     "unlock_condition":"各バイオームで解放","restock_time":"時間経過で在庫回復",
     "note":"バイオームごとに設置。種や食材を販売","visited_today":False,"memo":""},
    {"id":"fac_kristoff_stall","name_ja":"クリストフの露店","type":"ショップ（素材）",
     "unlock_condition":"フォレスト・オブ・ヴァラーで解放","restock_time":"時間経過で在庫回復",
     "note":"採取素材などを販売","visited_today":False,"memo":""},
    {"id":"fac_pumpkin_stall","name_ja":"やしの木/釣り/採掘 などの活動場所","type":"採取ポイント",
     "unlock_condition":"バイオーム解放","restock_time":"—",
     "note":"釣り・採掘・採取などの拠点（バイオーム参照）","visited_today":False,"memo":""},
    {"id":"fac_dream_castle","name_ja":"ドリーム城","type":"拠点施設",
     "unlock_condition":"ストーリー進行","restock_time":"—",
     "note":"レルムの扉やドリームライト関連の中心施設","visited_today":False,"memo":""},
    {"id":"fac_house_upgrade","name_ja":"自宅（増築）","type":"住居",
     "unlock_condition":"スクルージに支払って増築","restock_time":"—",
     "note":"部屋の追加・模様替えが可能","visited_today":False,"memo":""},
]
pathlib.Path("data/facilities.json").write_text(json.dumps(facilities,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ② updates（Fandom Version History の版＋リンク。要約は自作の短文）
FANDOM="https://disneydreamlightvalley.fandom.com/wiki/Version_History/"
vers=["Update 1","1.0","1.0.5","1.1","1.1.2","1.1.3","1.2","1.3","1.4","1.6.0","1.7.0"]
updates=[]
for v in vers:
    slug=v.replace(" ","_")
    updates.append({
        "id":"upd_"+v.replace(".","_").replace(" ","_").lower(),
        "version":v,"release_date":"","title":f"バージョン {v}",
        "summary":"詳細（新要素・修正）はリンク先の Fandom Version History を参照",
        "new_characters":[],"new_features":[],"bug_fixes":[],
        "source_url":FANDOM+slug,"personal_notes":"",
    })
pathlib.Path("data/updates.json").write_text(json.dumps(updates,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# ④ 参照リンク集（本文は転載しない）
GP="https://gamepedia.jp/disneydreamlightvalley/"
tips=[
    {"id":"tip_beginner","title":"序盤のおすすめの進め方・レルム解放順","category":"攻略",
     "link":GP+"archives/163","source":"gamepedia 攻略大百科","body_md":"","related_ids":[],
     "tried":False,"useful_rating":0,"memo":""},
    {"id":"tip_articles","title":"攻略記事一覧（小技・裏技など）","category":"攻略",
     "link":GP+"archives/category/%E6%94%BB%E7%95%A5","source":"gamepedia 攻略大百科","body_md":"","related_ids":[],
     "tried":False,"useful_rating":0,"memo":""},
]
faq=[
    {"id":"faq_qa","question":"よくある質問（Q&A）｜見つからない・進めないときの対処","answer_md":"",
     "category":"FAQ","link":GP+"archives/338","source":"gamepedia 攻略大百科",
     "related_ids":[],"still_confused":False,"memo":""},
]
bugs=[
    {"id":"bug_matome","title":"不具合・バグまとめ（対処法・既知の問題）","affected_platform":"全般",
     "description":"","status":"参照","reported_date":"","source_url":GP+"archives/835",
     "link":GP+"archives/835","source":"gamepedia 攻略大百科",
     "personal_encountered":False,"workaround_tried":"","memo":""},
]
pathlib.Path("data/tips.json").write_text(json.dumps(tips,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
pathlib.Path("data/faq.json").write_text(json.dumps(faq,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
pathlib.Path("data/bugs.json").write_text(json.dumps(bugs,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

print("facilities:",len(facilities)," updates:",len(updates)," tips:",len(tips)," faq:",len(faq)," bugs:",len(bugs))
