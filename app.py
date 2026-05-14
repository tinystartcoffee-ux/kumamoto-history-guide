import os, json, threading, time
from urllib import request as urlreq
from flask import Flask, render_template, jsonify, send_file, abort

app = Flask(__name__)

SPOTS_FILE = os.path.join(os.path.dirname(__file__), "spots.json")
FIGURES_FILE = os.path.join(os.path.dirname(__file__), "figures.json")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")

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
    return render_template("map.html", spots=spots, spot_sizes=spot_sizes)

@app.route("/spot/<spot_id>")
def spot(spot_id):
    spots = load_spots()
    if spot_id not in spots:
        return "史跡が見つかりません", 404
    s = spots[spot_id]
    return render_template("spot.html", spot=s, spot_id=spot_id)

@app.route("/audio/<spot_id>")
def audio(spot_id):
    audio_path = os.path.join(AUDIO_DIR, f"{spot_id}.mp3")
    if not os.path.exists(audio_path):
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
