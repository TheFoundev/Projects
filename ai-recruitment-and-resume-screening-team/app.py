"""The web layer of the project: the site, the console and the API.

Three things live here:

    /             the home page of the site
    /console.html the console, with the candidates and the metrics of the run
    /candidates   the dashboard of the project, with the table of the
                  candidates (this is the page the project had)

The API behind the console is /api/summary, /api/candidates and
/api/questions, and /api/train fits the classifier again.
"""
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_from_directory

from src.data import load_data
from src.model import draft_interview_questions, rank_candidates, train

#: The directory of the site and the database of the candidates.
ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DB_PATH = ROOT / "artifacts" / "candidates.db"

app = Flask(__name__)

DATA = load_data(seed=3, quick=False)
MODEL, METRICS = train(DATA, quick=False, db_path=str(DB_PATH))

PAGE = """
<!doctype html>
<title>Resume screening</title>
<style>
 body { font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; }
 table { border-collapse: collapse; width: 100%; }
 th, td { text-align: left; padding: 8px; border-bottom: 1px solid #e5e7eb; }
 .yes { color: #15803d; font-weight: 600; }
</style>
<h1>Resume screening</h1>
<p>{{ job }}</p>
<table>
<tr><th>Candidate</th><th>Years</th><th>Score</th><th>Shortlist</th></tr>
{% for row in rows %}
<tr>
  <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ '%.2f'|format(row[3]) }}</td>
  <td class="{{ 'yes' if row[4] else '' }}">{{ 'yes' if row[4] else 'no' }}</td>
</tr>
{% endfor %}
</table>
<p>Metrics: precision {{ '%.2f'|format(metrics.precision) }}, recall {{ '%.2f'|format(metrics.recall) }}.</p>

<h2>Questions for the interview</h2>
{% for question in questions %}
<p>- {{ question }}</p>
{% endfor %}
"""


def candidates():
    """The candidates of the database, the best score first."""
    connection = sqlite3.connect(DB_PATH)
    rows = connection.execute(
        "SELECT name, years, skills, score, shortlisted FROM candidates ORDER BY score DESC"
    ).fetchall()
    connection.close()
    return rows


def interview_questions():
    """The questions of the interview, drafted from the best candidate."""
    ranked = rank_candidates(MODEL, DATA)
    if not ranked:
        return []
    return draft_interview_questions(ranked[0][0], DATA["job_description"])


def summary_payload():
    """The answer of /api/summary: the numbers of the run."""
    rows = candidates()
    questions = interview_questions()
    return {
        "stats": {
            "candidates": len(rows),
            "shortlisted": sum(1 for row in rows if row[4]),
            "precision": METRICS["precision"],
            "recall": METRICS["recall"],
        },
        "series": [
            {"label": row[0], "value": round(row[3], 4)} for row in rows
        ],
        "lists": {
            "candidates": [
                {
                    "name": row[0],
                    "years": row[1],
                    "score": round(row[3], 4),
                    "shortlisted": "yes" if row[4] else "no",
                }
                for row in rows
            ],
            "questions": [{"question": question} for question in questions],
        },
    }


@app.route("/candidates")
def index():
    """The dashboard of the project: the candidates and the questions."""
    return render_template_string(
        PAGE,
        rows=candidates(),
        metrics=METRICS,
        job=DATA["job_description"],
        questions=interview_questions(),
    )


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
    """The numbers of the run: the candidates, the shortlist and the metrics."""
    return jsonify(summary_payload())


@app.route("/api/candidates")
def api_candidates():
    """The candidates of the test set with their score."""
    return jsonify({"candidates": summary_payload()["lists"]["candidates"]})


@app.route("/api/questions")
def api_questions():
    """The questions of the interview, drafted from the best candidate."""
    return jsonify({"questions": interview_questions()})


@app.route("/api/train", methods=["POST"])
def api_train():
    """Fit the classifier again and answer with the new metrics."""
    global MODEL, METRICS
    MODEL, METRICS = train(DATA, quick=False, db_path=str(DB_PATH))
    return jsonify(summary_payload()["stats"])


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
