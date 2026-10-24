"""A small kiosk page for the synthetic face classifier."""
from pathlib import Path

from flask import Flask, render_template_string, send_from_directory
import numpy as np

from src.data import draw_face
from src.model import train
from src.data import load_data

app = Flask(__name__)
DATA = load_data(seed=5, quick=True)
MODEL, METRICS = train(DATA, quick=True)

PAGE = """
<!doctype html>
<title>Face attribute kiosk</title>
<style>
 body { font-family: system-ui, sans-serif; max-width: 680px; margin: 40px auto; }
 .grid { display: grid; grid-template-columns: repeat(32, 12px); width: 384px; }
 .cell { width: 12px; height: 12px; }
 .card { background: #f3f4f6; border-radius: 10px; padding: 16px; margin-top: 18px; }
</style>
<h1>Face attribute kiosk</h1>
<p>Synthetic sample. The classifier predicts glasses and smile from pixels.</p>
<div class="grid">
{% for row in rows %}
  {% for value in row %}
    <div class="cell" style="background: rgb({{ value }}, {{ value }}, {{ value }})"></div>
  {% endfor %}
{% endfor %}
</div>
<div class="card">
  <p><strong>Prediction:</strong> glasses={{ prediction[0] }}, smiling={{ prediction[1] }}</p>
  <p><strong>Test accuracy:</strong> glasses={{ metrics.glasses_accuracy }}, smile={{ metrics.smile_accuracy }}</p>
  <p>Reload to generate another sample.</p>
</div>
"""


WEB_DIR = Path(__file__).resolve().parent / "web"


@app.route("/")
def index():
    image, _, _ = draw_face(seed=np.random.randint(0, 100000))
    pixels = (np.clip(image, 0, 1) * 255).astype(int)
    prediction = MODEL.predict(image.reshape(1, -1))[0]
    return render_template_string(
        PAGE,
        rows=pixels.tolist(),
        prediction=[bool(prediction[0]), bool(prediction[1])],
        metrics=METRICS,
    )


@app.route("/console.html")
def console():
    """The console of the site."""
    return send_from_directory(WEB_DIR, "console.html")


@app.route("/assets/<path:name>")
def assets(name):
    """The theme and the runtime of the site."""
    return send_from_directory(WEB_DIR / "assets", name)


@app.route("/api/summary")
def summary():
    """The state of the running instance."""
    return {
        "stats": {
            "glasses_accuracy": METRICS["glasses_accuracy"],
            "smile_accuracy": METRICS["smile_accuracy"],
            "features": 1024,
            "samples": len(DATA["X_test"]),
        },
        "series": [
            {"label": "glasses", "value": METRICS["glasses_accuracy"]},
            {"label": "smile", "value": METRICS["smile_accuracy"]},
        ],
        "lists": {
            "attributes": [
                {"attribute": "glasses", "accuracy": METRICS["glasses_accuracy"]},
                {"attribute": "smile", "accuracy": METRICS["smile_accuracy"]},
            ]
        },
    }


if __name__ == "__main__":
    import os
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
