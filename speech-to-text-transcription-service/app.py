"""A small page that transcribes freshly synthesized digits.

The page of the project is still here, at `/demo`, and `/transcribe` still
answers with the transcription of a sample. The home page of the site of the
project, its console and the JSON API live in `web/` and are served by this
same application.
"""
from pathlib import Path

from flask import (Flask, jsonify, render_template_string, send_from_directory)

from src.data import load_data, utterance
from src.model import transcribe, train

app = Flask(__name__)
DATA = load_data(seed=4, quick=True)
MODEL, METRICS = train(DATA, quick=True)

WEB = Path(__file__).resolve().parent / "web"

PAGE = """
<!doctype html>
<title>Digit transcription demo</title>
<style> body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; } </style>
<h1>Synthetic transcription</h1>
<p>This service synthesizes three spoken digits and transcribes them. It is not connected to a microphone.</p>
<pre>{{ result }}</pre>
<p><a href="/transcribe">Run another sample</a></p>
"""


@app.route("/demo")
def index():
    return render_template_string(PAGE, result={"hint": "open /transcribe"})


@app.route("/transcribe")
def run_sample():
    truth, signal = DATA["phrases"][0]
    predicted = transcribe(signal, MODEL, DATA["words"])
    return jsonify({"reference": truth, "predicted": predicted, "metrics": METRICS})


# ------------------------------------------------------------------ #
# The web layer of the project                                        #
# ------------------------------------------------------------------ #

@app.route("/")
def site_index():
    """The home page of the site of the project."""
    return send_from_directory(WEB, "index.html")


@app.route("/console.html")
def site_console():
    """The console of the site of the project."""
    return send_from_directory(WEB, "console.html")


@app.route("/assets/<path:name>")
def site_assets(name):
    """The theme and the runtime of the site of the project."""
    return send_from_directory(WEB / "assets", name)


def _phrases() -> list[dict]:
    """The transcription of every test phrase of the service."""
    rows = []
    for truth, signal in DATA["phrases"]:
        predicted = transcribe(signal, MODEL, DATA["words"])
        correct = sum(1 for a, b in zip(truth, predicted) if a == b)
        rows.append({
            "reference": " ".join(truth),
            "heard": " ".join(predicted),
            "correct": f"{correct}/{len(truth)}",
        })
    return rows


@app.route("/api/summary")
def api_summary():
    """The error rate of the service and the transcription of every phrase."""
    rows = _phrases()
    return jsonify({
        "stats": {
            "word_error_rate": METRICS["word_error_rate"],
            "vocabulary_size": METRICS["vocabulary_size"],
            "test_phrases": METRICS["test_phrases"],
            "sample_rate": METRICS["sample_rate"],
        },
        "series": [
            {"label": f"phrase {index + 1}", "value": int(row["correct"].split("/")[0])}
            for index, row in enumerate(rows)
        ],
        "lists": {
            "phrases": rows,
        },
    })


@app.route("/api/transcribe")
def api_transcribe():
    """The transcription of one of the test phrases."""
    truth, signal = DATA["phrases"][0]
    predicted = transcribe(signal, MODEL, DATA["words"])
    return jsonify({
        "reference": truth,
        "predicted": predicted,
        "metrics": METRICS,
    })


if __name__ == "__main__":
    import os

    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=False)
