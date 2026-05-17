"""
figures.json の name/era/desc を英訳して *_en を追加。
無料Google翻訳・中断再開対応（spots版と同方式）。
"""
import os, sys, json, time
from deep_translator import GoogleTranslator

DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(DIR, "figures.json")
FIELDS = ["name", "era", "desc"]
SLEEP = 0.25

def load():
    with open(FILE, encoding="utf-8") as f:
        return json.load(f)

def save(d):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def tr_one(text, tr):
    text = (text or "").strip()
    if not text:
        return ""
    for a in range(4):
        try:
            return tr.translate(text)
        except Exception as e:
            if a == 3:
                print(f"  ✗ {e}")
                return ""
            time.sleep(1.5 * (a + 1))
    return ""

def main():
    d = load()
    need = [fid for fid, f in d.items()
            if not all(f.get(x + "_en") for x in FIELDS)]
    if "--status" in sys.argv:
        print(f"翻訳済み: {len(d)-len(need)}/{len(d)}  未翻訳: {len(need)}")
        return
    print(f"対象 {len(need)} 人を翻訳")
    tr = GoogleTranslator(source="ja", target="en")
    for i, fid in enumerate(need, 1):
        f = d[fid]
        for x in FIELDS:
            if f.get(x + "_en"):
                continue
            f[x + "_en"] = tr_one(f.get(x, ""), tr)
            time.sleep(SLEEP)
        if i % 20 == 0 or i == len(need):
            print(f"[{i}/{len(need)}] {f.get('name_en','')}")
            save(d)
    save(d)
    print("完了")

if __name__ == "__main__":
    main()
