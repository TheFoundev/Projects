"""The web layer of the project: the site, the console and the API.

Three things live here:

    /             the home page of the site
    /console.html the console, with the live numbers of the run
    /summarize    the demo page of the project: paste a document, read its
                  summary (this is the page the project had)

The API behind the console is /api/summary, which answers with the real
metrics of the corpus, and /api/summarize, which answers with the summary of
a document.
"""
from pathlib import Path

import os

from flask import Flask, jsonify, render_template_string, request, send_from_directory

from src.data import load_data, split_sentences
from src.model import rouge_l, summarize, train

#: The directory of the site, next to this file.
WEB = Path(__file__).resolve().parent / "web"

app = Flask(__name__)

PAGE = """
<!doctype html>
<title>Document summarizer</title>
<style>
 body { font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
 textarea { width: 100%; height: 180px; padding: 10px; font: inherit; }
 button { padding: 9px 16px; margin-top: 10px; }
 .summary { background: #f3f4f6; padding: 16px; border-radius: 8px; margin-top: 20px; }
</style>
<h1>Document summarizer</h1>
<p>Paste a short document. The baseline picks the most central sentences.</p>
<form method="post">
  <textarea name="text">{{ text }}</textarea>
  <button type="submit">Summarize</button>
</form>
{% if summary %}
<div class="summary"><strong>Summary</strong><p>{{ summary }}</p></div>
{% endif %}
"""


#: The metrics of the corpus, computed once and kept for the process.
_STATE = {}


def state():
    """The trained model and the metrics of the corpus.

    The training searches the length of the summary over the corpus, so the
    numbers the console shows are the ones of a real run of the project.
    """
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        documents = []
        for index, (document, reference) in enumerate(
            zip(data["documents"], data["references"]), start=1
        ):
            summary = summarize(document, max_sentences=model["max_sentences"])
            documents.append({
                "document": index,
                "sentences": len(split_sentences(document)),
                "rouge_l": round(rouge_l(reference, summary), 4),
            })
        _STATE["model"] = model
        _STATE["metrics"] = metrics
        _STATE["documents"] = documents
    return _STATE


def summary_payload():
    """The answer of /api/summary: the numbers of the run."""
    current = state()
    metrics = current["metrics"]
    scores = metrics["scores_by_length"]
    return {
        "stats": {
            "rouge_l": metrics["rouge_l"],
            "max_sentences": metrics["max_sentences"],
            "documents": metrics["documents"],
            "lengths": len(scores),
        },
        "series": [
            {"label": f"{length} sentence" + ("s" if length != 1 else ""), "value": score}
            for length, score in sorted(scores.items())
        ],
        "lists": {
            "lengths": [
                {"length": length, "rouge_l": score} for length, score in sorted(scores.items())
            ],
            "documents": current["documents"],
        },
    }


@app.route("/summarize", methods=["GET", "POST"])
def demo():
    """The page of the project: paste a document, read its summary."""
    text = request.form.get("text", "")
    summary = summarize(text, max_sentences=state()["model"]["max_sentences"]) if text.strip() else ""
    return render_template_string(PAGE, text=text, summary=summary)


@app.route("/")
def home():
    """The home page of the site."""
    return send_from_directory(WEB, "index.html")


@app.route("/console.html")
def console():
    """The console of the site."""
    return send_from_directory(WEB, "console.html")


@app.route("/assets/<path:filename>")
def assets(filename):
    """The theme and the runtime of the site."""
    return send_from_directory(WEB / "assets", filename)


@app.route("/api/summary")
def api_summary():
    """The numbers of the run: the best length, the ROUGE-L and the scores."""
    return jsonify(summary_payload())


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """The summary of the text of the request."""
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or "")
    length = state()["model"]["max_sentences"]
    return jsonify({
        "summary": summarize(text, max_sentences=length) if text.strip() else "",
        "sentences": length,
    })


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
