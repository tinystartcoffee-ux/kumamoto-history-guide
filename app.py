import os, json
from flask import Flask, render_template, jsonify, send_file

app = Flask(__name__)

SPOTS_FILE = os.path.join(os.path.dirname(__file__), "spots.json")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")

def load_spots():
    with open(SPOTS_FILE, encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def index():
    spots = load_spots()
    return render_template("map.html", spots=spots)

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

@app.route("/api/spots")
def api_spots():
    spots = load_spots()
    return jsonify(spots)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
