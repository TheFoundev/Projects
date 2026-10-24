"""A compact sales dashboard.

The dashboard of the project is still here, at `/demo`. The home page of the
site of the project, its console and the JSON API live in `web/` and are
served by this same application.
"""
import json
from pathlib import Path

from flask import (Flask, jsonify, render_template_string, send_file,
                   send_from_directory)

from src.pipeline import run

app = Flask(__name__)
run(quick=True, base_dir="artifacts")

WEB = Path(__file__).resolve().parent / "web"

PAGE = """
<!doctype html>
<title>Sales KPIs</title>
<style>
 body { font-family: system-ui, sans-serif; max-width: 900px; margin: 36px auto; color: #1f2937; }
 .cards { display: flex; gap: 14px; flex-wrap: wrap; }
 .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 18px; min-width: 150px; }
 .card strong { display: block; font-size: 1.5rem; margin-top: 4px; }
 table { border-collapse: collapse; width: 100%; margin-top: 10px; }
 th, td { text-align: left; padding: 7px; border-bottom: 1px solid #e5e7eb; }
 img { max-width: 100%; margin-top: 18px; border: 1px solid #e5e7eb; }
</style>
<h1>Sales KPIs</h1>
<div class="cards">
 <div class="card">Revenue<strong>{{ '%.2f'|format(kpis.revenue) }}</strong></div>
 <div class="card">Orders<strong>{{ kpis.orders }}</strong></div>
 <div class="card">Average order<strong>{{ '%.2f'|format(kpis.aov) }}</strong></div>
 <div class="card">30-day growth<strong>{{ '%.1f'|format(kpis.growth_pct) }}%</strong></div>
</div>
<img src="/chart" alt="Daily revenue trend">
<h2>Revenue by product</h2>
<table><tr><th>Product</th><th>Revenue</th></tr>
{% for row in kpis.products %}<tr><td>{{ row.product }}</td><td>{{ '%.2f'|format(row.revenue) }}</td></tr>{% endfor %}
</table>
"""


@app.route("/demo")
def index():
    kpis = json.loads(Path("artifacts/kpis.json").read_text())
    return render_template_string(PAGE, kpis=kpis)


@app.route("/chart")
def chart():
    return send_file(Path("artifacts/revenue_trend.png"), mimetype="image/png")


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


def _kpis() -> dict:
    """The KPIs of the last run of the pipeline."""
    return json.loads(Path("artifacts/kpis.json").read_text())


@app.route("/api/summary")
def api_summary():
    """The KPIs of the running instance and the revenue per product and region."""
    kpis = _kpis()
    revenue = float(kpis["revenue"]) or 1.0
    return jsonify({
        "stats": {
            "revenue": kpis["revenue"],
            "orders": kpis["orders"],
            "aov": kpis["aov"],
            "growth_pct": kpis["growth_pct"],
        },
        "series": [
            {"label": str(row["product"]), "value": float(row["revenue"])}
            for row in kpis["products"]
        ],
        "lists": {
            "products": [
                {"product": str(row["product"]), "revenue": float(row["revenue"]),
                 "share %": round(float(row["revenue"]) / revenue * 100, 2)}
                for row in kpis["products"]
            ],
            "regions": [
                {"region": str(row["region"]), "revenue": float(row["revenue"]),
                 "share %": round(float(row["revenue"]) / revenue * 100, 2)}
                for row in kpis["regions"]
            ],
        },
    })


@app.route("/api/kpis")
def api_kpis():
    """The KPIs as the pipeline wrote them."""
    return jsonify(_kpis())


@app.route("/api/products")
def api_products():
    """The revenue of every product."""
    return jsonify({"products": _kpis()["products"]})


@app.route("/api/regions")
def api_regions():
    """The revenue of every region."""
    return jsonify({"regions": _kpis()["regions"]})


@app.route("/api/rerun", methods=["POST"])
def api_rerun():
    """Run the pipeline again and answer with the new KPIs."""
    summary = run(quick=True, base_dir="artifacts")
    return jsonify({"rerun": True, "summary": summary})


if __name__ == "__main__":
    import os

    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=False)
