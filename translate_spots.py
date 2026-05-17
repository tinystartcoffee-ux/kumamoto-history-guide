"""
spots.json の name/text/highlight を英訳して *_en フィールドを追加。

- 無料の Google 翻訳（deep-translator）を使用
- 既に *_en があるスポットはスキップ（中断後の再開可能）
- 30件ごとに spots.json へ保存（途中中断しても進捗が残る）
- レート制限対策に sleep ＋ 失敗時リトライ

使い方:
  python3 translate_spots.py            # 未翻訳のみ翻訳
  python3 translate_spots.py --status   # 進捗確認のみ
"""
import os, sys, json, time
from deep_translator import GoogleTranslator

DIR = os.path.dirname(os.path.abspath(__file__))
SPOTS = os.path.join(DIR, "spots.json")
FIELDS = ["name", "highlight", "text"]
SLEEP = 0.25          # リクエスト間隔（秒）
SAVE_EVERY = 30       # 何件ごとに保存するか

def load():
    with open(SPOTS, encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(SPOTS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def translate(text, tr):
    text = (text or "").strip()
    if not text:
        return ""
    for attempt in range(4):
        try:
            return tr.translate(text)
        except Exception as e:
            if attempt == 3:
                print(f"  ✗ 翻訳失敗（{attempt+1}回）: {e}")
                return ""
            time.sleep(1.5 * (attempt + 1))
    return ""

def main():
    data = load()
    need = [sid for sid, s in data.items()
            if not all(s.get(f + "_en") for f in FIELDS)]
    total = len(data)
    done = total - len(need)

    if "--status" in sys.argv:
        print(f"翻訳済み: {done}/{total}  未翻訳: {len(need)}")
        return

    print(f"対象 {len(need)} 件を翻訳します（済 {done}/{total}）")
    tr = GoogleTranslator(source="ja", target="en")
    processed = 0
    for i, sid in enumerate(need, 1):
        s = data[sid]
        for f in FIELDS:
            if s.get(f + "_en"):
                continue
            s[f + "_en"] = translate(s.get(f, ""), tr)
            time.sleep(SLEEP)
        processed += 1
        if i % 10 == 0 or i == len(need):
            print(f"[{i}/{len(need)}] {sid}: {s.get('name_en','')[:40]}")
        if processed % SAVE_EVERY == 0:
            save(data)
            print(f"  …保存（{done+processed}/{total}）")
    save(data)
    print(f"完了: {done+processed}/{total} 翻訳済み")

if __name__ == "__main__":
    main()
