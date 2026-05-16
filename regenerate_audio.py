"""
音声ガイド一括再生成スクリプト

使い方:
  python3 regenerate_audio.py              # 未生成のスポットだけ生成
  python3 regenerate_audio.py --force      # 全mp3を削除して再生成
  python3 regenerate_audio.py <spot_id>... # 指定IDだけ再生成
  python3 regenerate_audio.py --list       # 既存mp3の数を確認
"""
import os, sys, json, asyncio
import edge_tts
from reading_fixes import fix_reading

_DIR = os.path.dirname(os.path.abspath(__file__))
SPOTS_FILE = os.path.join(_DIR, "spots.json")
AUDIO_DIR = os.path.join(_DIR, "audio")
VOICE = "ja-JP-NanamiNeural"

def load_spots():
    with open(SPOTS_FILE, encoding="utf-8") as f:
        return json.load(f)

async def gen_one(sid, spot):
    text = fix_reading(spot.get("text", ""))
    if not text:
        return False
    audio_path = os.path.join(AUDIO_DIR, f"{sid}.mp3")
    try:
        c = edge_tts.Communicate(text, VOICE)
        await c.save(audio_path)
        return True
    except Exception as e:
        print(f"  失敗: {e}")
        return False

async def main():
    args = sys.argv[1:]
    spots = load_spots()
    os.makedirs(AUDIO_DIR, exist_ok=True)

    if "--list" in args:
        existing = set(f[:-4] for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3"))
        print(f"スポット総数: {len(spots)}")
        print(f"音声あり: {len(existing & set(spots.keys()))}")
        print(f"音声なし: {len(set(spots.keys()) - existing)}")
        print(f"孤立mp3: {len(existing - set(spots.keys()))}")
        return

    force = "--force" in args
    ids = [a for a in args if not a.startswith("--")]

    if force:
        ans = input(f"全 {len(spots)} スポットを再生成します。よろしいですか？ [y/N]: ")
        if ans.lower() != 'y':
            print("中止しました")
            return
        targets = list(spots.keys())
    elif ids:
        targets = [i for i in ids if i in spots]
        miss = set(ids) - set(spots.keys())
        if miss:
            print(f"未知のID: {miss}")
    else:
        existing = set(f[:-4] for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3"))
        targets = [sid for sid in spots if sid not in existing]
        print(f"未生成: {len(targets)} 件")

    total = len(targets)
    ok = ng = 0
    for i, sid in enumerate(targets, 1):
        print(f"[{i}/{total}] {sid}: {spots[sid].get('name','')}")
        success = await gen_one(sid, spots[sid])
        if success: ok += 1
        else: ng += 1

    print(f"\n完了: 成功 {ok} / 失敗 {ng}")

if __name__ == "__main__":
    asyncio.run(main())
