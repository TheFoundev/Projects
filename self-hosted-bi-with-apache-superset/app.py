"""A read-only BI page over the saved query output.

The dashboard of the project is still here, at `/demo`. The home page of the
site of the project, its console and the JSON API live in `web/` and are
served by this same application.
"""
import json
from pathlib import Path

from flask import (Flask, jsonify, render_template_string, send_file,
                   send_from_directory)

from src.pipeline import QUERIES, run

app = Flask(__name__)
run(quick=True, base_dir="artifacts")

WEB = Path(__file__).resolve().parent / "web"

PAGE = """
<!doctype html>
<title>Mini BI</title>
<style>
 body { font-family: system-ui, sans-serif; max-width: 980px; margin: 36px auto; color: #1f2937; }
 table { border-collapse: collapse; width: 100%; margin: 8px 0 22px; }
 th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e5e7eb; }
 img { max-width: 100%; border: 1px solid #e5e7eb; }
</style>
<h1>Mini BI dashboard</h1>
<p>Saved SQL queries over a local warehouse. Synthetic data only.</p>
<img src="/chart" alt="Monthly revenue">
<h2>Monthly revenue</h2>
{{ monthly|safe }}
<h2>Top products</h2>
{{ products|safe }}
<h2>Region share</h2>
{{ regions|safe }}
<h2>Repeat purchase rate</h2>
<p>{{ repeat }}% of paying customers ordered more than once.</p>
"""


def to_table(rows):
    if not rows:
        return "<p>No rows.</p>"
    headers = "".join(f"<th>{key}</th>" for key in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{value}</td>" for value in row.values()) + "</tr>"
        for row in rows
    )
    return f"<table><tr>{headers}</tr>{body}</table>"


@app.route("/demo")
def index():
    dashboard = json.loads(Path("artifacts/dashboard.json").read_text())
    repeat = dashboard["repeat_rate"][0]["repeat_rate"]
    return render_template_string(
        PAGE,
        monthly=to_table(dashboard["monthly_revenue"]),
        products=to_table(dashboard["top_products"]),
        regions=to_table(dashboard["region_share"]),
        repeat=repeat,
    )


@app.route("/chart")
def chart():
    return send_file(Path("artifacts/monthly_revenue.png"), mimetype="image/png")


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


def _dashboard() -> dict:
    """The answers of the saved queries of the last run."""
    return json.loads(Path("artifacts/dashboard.json").read_text())


@app.route("/api/summary")
def api_summary():
    """The numbers of the warehouse and the answers of the saved queries."""
    dashboard = _dashboard()
    monthly = dashboard["monthly_revenue"]
    products = dashboard["top_products"]
    regions = dashboard["region_share"]
    repeat = dashboard["repeat_rate"][0]["repeat_rate"] if dashboard["repeat_rate"] else 0

    # The size of the warehouse and the revenue of the paid orders, read from
    # the database the saved queries run over.
    import sqlite3

    connection = sqlite3.connect("artifacts/bi_warehouse.db")
    orders = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    revenue = connection.execute(
        "SELECT COALESCE(ROUND(SUM(quantity * unit_price), 2), 0) FROM orders WHERE status = 'paid'"
    ).fetchone()[0]
    connection.close()

    return jsonify({
        "stats": {
            "queries": len(QUERIES),
            "orders": int(orders),
            "revenue": float(revenue),
            "repeat_rate": round(float(repeat), 2),
        },
        "series": [
            {"label": str(row["month"]), "value": float(row["revenue"])}
            for row in monthly
        ],
        "lists": {
            "monthly": [
                {"month": str(row["month"]), "revenue": float(row["revenue"])}
                for row in monthly
            ],
            "products": [
                {"product": str(row["product"]), "revenue": float(row["revenue"]),
                 "units": int(row["units"])}
                for row in products
            ],
            "regions": [
                {"region": str(row["region"]), "share %": float(row["pct"])}
                for row in regions
            ],
        },
    })


@app.route("/api/queries")
def api_queries():
    """The saved queries and the rows they answered with."""
    dashboard = _dashboard()
    return jsonify({name: dashboard.get(name, []) for name in QUERIES})


@app.route("/api/monthly")
def api_monthly():
    """The revenue of every month of the warehouse."""
    return jsonify({"monthly": _dashboard()["monthly_revenue"]})


@app.route("/api/run", methods=["POST"])
def api_run():
    """Run the saved queries again and answer with the new dashboard."""
    summary = run(quick=True, base_dir="artifacts")
    return jsonify({"ran": True, "summary": summary})


if __name__ == "__main__":
    import os

    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=False)
