import os, json, threading, time, asyncio
from urllib import request as urlreq
from flask import Flask, render_template, jsonify, send_file, abort, request

try:
    import edge_tts
    from reading_fixes import fix_reading
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

app = Flask(__name__)

SPOTS_FILE = os.path.join(os.path.dirname(__file__), "spots.json")
FIGURES_FILE = os.path.join(os.path.dirname(__file__), "figures.json")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
TTS_VOICE = "ja-JP-NanamiNeural"
TTS_VOICE_EN = "en-US-AriaNeural"

def ensure_audio(spot_id, spot, lang="ja"):
    """音声ファイルが無ければ edge-tts で生成。
    ja: 読み仮名辞書で固有名詞補正 / en: text_en を英語音声で生成"""
    suffix = "" if lang == "ja" else "_" + lang
    audio_path = os.path.join(AUDIO_DIR, f"{spot_id}{suffix}.mp3")
    if os.path.exists(audio_path):
        return audio_path
    if not TTS_AVAILABLE:
        return None
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if lang == "en":
        text = (spot.get("text_en") or "").strip()
        voice = TTS_VOICE_EN
    else:
        text = fix_reading(spot.get("text", ""))
        voice = TTS_VOICE
    if not text:
        return None
    async def _gen():
        c = edge_tts.Communicate(text, voice)
        await c.save(audio_path)
    try:
        asyncio.run(_gen())
        return audio_path
    except Exception as e:
        print(f"音声生成失敗 {spot_id} ({lang}): {e}")
        return None

def load_figures():
    with open(FIGURES_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_spots():
    with open(SPOTS_FILE, encoding="utf-8") as f:
        return json.load(f)

def compute_spot_sizes(spots, figures):
    sizes = {}
    for sid, s in spots.items():
        best = 999
        for fid in s.get("figures", []):
            r = figures.get(fid, {}).get("rank_popular", 0)
            if r > 0 and r < best:
                best = r
        if best <= 5:
            sizes[sid] = 38
        elif best <= 20:
            sizes[sid] = 28
        else:
            sizes[sid] = 20
    return sizes

@app.route("/")
def index():
    spots = load_spots()
    figures = load_figures()
    spot_sizes = compute_spot_sizes(spots, figures)
    return render_template("map.html", spots=spots, spot_sizes=spot_sizes, figures=figures)

@app.route("/spot/<spot_id>")
def spot(spot_id):
    spots = load_spots()
    if spot_id not in spots:
        return "史跡が見つかりません", 404
    s = spots[spot_id]
    return render_template("spot.html", spot=s, spot_id=spot_id)

@app.route("/audio/<spot_id>")
def audio(spot_id):
    lang = request.args.get("lang", "ja")
    if lang not in ("ja", "en"):
        lang = "ja"
    suffix = "" if lang == "ja" else "_" + lang
    audio_path = os.path.join(AUDIO_DIR, f"{spot_id}{suffix}.mp3")
    if not os.path.exists(audio_path):
        # 自動生成を試みる
        spots = load_spots()
        if spot_id in spots:
            ensure_audio(spot_id, spots[spot_id], lang)
    if not os.path.exists(audio_path):
        # 英語が無ければ日本語にフォールバック
        if lang == "en":
            ja_path = os.path.join(AUDIO_DIR, f"{spot_id}.mp3")
            if os.path.exists(ja_path):
                return send_file(ja_path, mimetype="audio/mpeg")
        return "音声ファイルが見つかりません", 404
    return send_file(audio_path, mimetype="audio/mpeg")

@app.route("/figures")
def figures_list():
    figures = load_figures()
    return render_template("figures.html", figures=figures)

@app.route("/figure/<figure_id>")
def figure_detail(figure_id):
    figures = load_figures()
    if figure_id not in figures:
        abort(404)
    spots = load_spots()
    figure = figures[figure_id]
    related = {sid: s for sid, s in spots.items() if figure_id in s.get("figures", [])}
    return render_template("figure_detail.html", figure=figure, figure_id=figure_id, spots=related)

@app.route("/api/spots")
def api_spots():
    spots = load_spots()
    return jsonify(spots)

def _keep_alive():
    base = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base:
        return
    time.sleep(60)
    while True:
        try:
            urlreq.urlopen(f"{base}/health", timeout=10)
        except Exception:
            pass
        time.sleep(600)  # 10分ごと

threading.Thread(target=_keep_alive, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
