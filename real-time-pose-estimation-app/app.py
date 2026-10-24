"""The HTTP API of the pose estimator.

The frames come from the simulator, from an uploaded picture or from a
camera when OpenCV is there.

The site of the project lives in `web/`: the home page, the console and the
theme are served from there, and `/api/summary` answers with the numbers of
the model that is really trained.
"""
import base64
import binascii
import io
import os
import threading
import time
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template_string, request, send_from_directory
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src.data import load_data, make_frame
from src.model import JOINT_NAMES, estimate, mean_joint_error, pck, save_model, train

app = Flask(__name__)
DATA = load_data(seed=3, quick=True)
MODEL, METRICS = train(DATA, quick=True)

#: The site of the project.
WEB = Path(__file__).resolve().parent / "web"

#: The frame that is served next, and the lock that keeps it safe.
STATE = {"frame": 0}
LOCK = threading.Lock()

#: The API key, when there is one.
API_KEY = os.environ.get("POSE_API_KEY", "")

#: The name of the cookie that holds the signed session.
SESSION_COOKIE = "pose_session"

#: How many requests a client may make a minute.
RATE_LIMIT = 120
REQUESTS: dict[str, list[float]] = {}
RATE_LOCK = threading.Lock()

#: The secret of the signed session, kept next to the artifacts.
SECRET_PATH = Path("artifacts/.session-secret")


def load_secret() -> bytes:
    """The secret of the session, written once and read back after a restart."""
    if not SECRET_PATH.exists():
        SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
        SECRET_PATH.write_bytes(os.urandom(32))
        os.chmod(SECRET_PATH, 0o600)
    return SECRET_PATH.read_bytes()


def session_token() -> URLSafeTimedSerializer:
    """The signer of the session cookie."""
    return URLSafeTimedSerializer(load_secret())


PAGE = """
<!doctype html>
<title>Pose demo</title>
<link rel="stylesheet" href="/assets/theme.css">
<style>
 body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; }
 pre { background: #f3f4f6; padding: 12px; border-radius: 8px; }
</style>
<h1>Pose estimation demo</h1>
<p>
  The frames come from the simulator, from a picture you upload or from a
  camera when OpenCV is installed.
</p>
<ul>
  <li><code>/frame</code> returns the joints of the next frame as JSON</li>
  <li><code>POST /frame</code> with a JSON body of <code>{"image": "&lt;base64 png&gt;"}</code>
      estimates the pose of an uploaded picture</li>
  <li><code>GET /camera</code> takes a picture from a camera, when there is one</li>
  <li><code>/api/summary</code> answers with the numbers of the trained model</li>
</ul>
<p><a href="/console.html">Open the console</a></p>
<pre>{{ metrics }}</pre>
"""



def session_user():
    """The key of the signed session of the browser, when there is one."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        return session_token().loads(token, max_age=8 * 3600)
    except BadSignature:
        return None


def check_api_key():
    """The API key, when there is one, has to be right."""
    if not API_KEY:
        return None
    given = request.headers.get("X-API-Key", "")
    if given == API_KEY:
        return None
    # A signed session of the portal counts as the key as well.
    if session_user() == API_KEY:
        return None
    return jsonify({"error": "the API key is not right"}), 401


def rate_limited():
    """True when the client made too many requests."""
    client = request.remote_addr or "unknown"
    now = time.time()
    with RATE_LOCK:
        history = [stamp for stamp in REQUESTS.get(client, []) if now - stamp < 60]
        if len(history) >= RATE_LIMIT:
            REQUESTS[client] = history
            return True
        history.append(now)
        REQUESTS[client] = history
    return False


def decode_image(payload):
    """Read a base64 encoded picture into an array."""
    if not payload:
        raise ValueError("no picture was sent")
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError(f"the picture is not base64: {error}")

    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - only without Pillow
        raise ValueError("Pillow is needed to read an uploaded picture") from error

    with Image.open(io.BytesIO(raw)) as image:
        return np.asarray(image.convert("L"), dtype=float)


def summary_payload():
    """The state of the estimator.

    The metrics are the ones of the trained model, the error of every frame is
    measured again with the estimator and the joints of the last frame are
    read out of it.
    """
    errors = []
    frame_rows = []
    for frame in DATA["frames"]:
        people = estimate(frame["image"], MODEL)
        error = mean_joint_error(people[0]["joints"], frame["joints"]) if people else -1.0
        errors.append(error)
        frame_rows.append({
            "frame": int(frame["frame"]),
            "people": len(people),
            "error": round(float(error), 2),
            "pck": round(float(pck(people[0]["joints"], frame["joints"])) if people else 0.0, 3),
        })

    last = DATA["frames"][-1]
    people = estimate(last["image"], MODEL)
    joints = [
        {"person": index + 1, "joint": name,
         "x": round(float(point[0]), 1), "y": round(float(point[1]), 1)}
        for index, person in enumerate(people)
        for name, point in zip(JOINT_NAMES, person["joints"])
    ]

    return {
        "stats": {
            "pck": METRICS["pck"],
            "error": METRICS["mean_joint_error"],
            "frames": METRICS["frames"],
            "joints": METRICS["joints_per_frame"],
        },
        "series": [{"label": f"frame {row['frame']}", "value": row["error"]} for row in frame_rows],
        "lists": {
            "joints": joints,
            "frames": frame_rows,
        },
    }


@app.route("/")
def index():
    """The home page of the site of the project."""
    return site_file("index.html")


@app.route("/demo")
def demo():
    """The demo page of the project, with the list of its routes."""
    return render_template_string(PAGE, metrics=METRICS)


@app.route("/console.html")
def console():
    return site_file("console.html")


@app.route("/login.html")
def login():
    return site_file("login.html")


@app.route("/assets/<path:name>")
def assets(name):
    """The theme and the runtime of the site."""
    return send_from_directory(WEB / "assets", name)


def site_file(name: str):
    """A page of the site, or the demo page when the site is not built yet."""
    if not (WEB / name).exists():
        return render_template_string(PAGE, metrics=METRICS)
    return send_from_directory(WEB, name)


@app.route("/api/summary")
def api_summary():
    """The numbers of the model that is really trained."""
    denied = check_api_key()
    if denied:
        return denied
    return jsonify(summary_payload())


@app.post("/api/session")
def sign_in():
    """Sign in with the API key of the server.

    The key is the secret of the project, so the session that is signed with
    it is what the console shows. Without a key on the server any password
    opens a local session.
    """
    body = request.get_json(silent=True) or {}
    key = str(body.get("api_key") or body.get("password") or "").strip()
    if not key:
        return jsonify({"error": "the API key is missing"}), 400
    if API_KEY and key != API_KEY:
        return jsonify({"error": "the API key is not right"}), 401
    token = session_token().dumps(key)
    response = jsonify({"user": {"name": "demo", "role": "operator"}})
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="Lax", max_age=8 * 3600)
    return response


@app.delete("/api/session")
def sign_out():
    """Sign out: the cookie of the session is cleared."""
    response = jsonify({"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.route("/frame")
def frame():
    denied = check_api_key()
    if denied:
        return denied
    if rate_limited():
        return jsonify({"error": "too many requests"}), 429

    with LOCK:
        STATE["frame"] += 1
        number = STATE["frame"]

    sample = make_frame(number)
    people = estimate(sample["image"], MODEL)
    return jsonify({
        "frame": sample["frame"],
        "source": "simulator",
        "people": [
            {"box": {key: round(value, 1) for key, value in person["box"].items()},
             "joints": person["joints"].round(1).tolist()}
            for person in people
        ],
        "names": JOINT_NAMES,
        "error_px": round(mean_joint_error(
            people[0]["joints"], sample["joints"]) if people else -1, 2),
        "pck": round(pck(people[0]["joints"], sample["joints"]) if people else 0.0, 3),
    })


@app.post("/frame")
def uploaded_frame():
    """Estimate the pose of a picture that was uploaded."""
    denied = check_api_key()
    if denied:
        return denied
    if rate_limited():
        return jsonify({"error": "too many requests"}), 429

    body = request.get_json(silent=True) or {}
    try:
        image = decode_image(body.get("image"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    people = estimate(image, MODEL)
    return jsonify({
        "source": "upload",
        "people": [
            {"box": {key: round(value, 1) for key, value in person["box"].items()},
             "joints": person["joints"].round(1).tolist()}
            for person in people
        ],
        "names": JOINT_NAMES,
    })


@app.route("/camera")
def camera():
    """Take a picture from a camera and estimate the pose."""
    denied = check_api_key()
    if denied:
        return denied
    if rate_limited():
        return jsonify({"error": "too many requests"}), 429

    try:
        import cv2
    except ImportError:
        return jsonify({"error": "OpenCV is not installed, so there is no camera"}), 501

    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        capture.release()
        return jsonify({"error": "no camera could be opened"}), 503
    ok, frame = capture.read()
    capture.release()
    if not ok:
        return jsonify({"error": "the camera did not give a picture"}), 503

    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    people = estimate(np.asarray(grey, dtype=float), MODEL)
    return jsonify({
        "source": "camera",
        "people": [
            {"box": {key: round(value, 1) for key, value in person["box"].items()},
             "joints": person["joints"].round(1).tolist()}
            for person in people
        ],
        "names": JOINT_NAMES,
    })


@app.post("/train")
def train_endpoint():
    """Fit the model again and save it."""
    denied = check_api_key()
    if denied:
        return denied

    global MODEL, METRICS
    MODEL, METRICS = train(DATA, quick=True)
    path = save_model(MODEL)
    return jsonify({"metrics": METRICS, "model": path})


if __name__ == "__main__":
    port = int(os.environ.get("POSE_PORT", os.environ.get("PORT", "5000")))
    # The development server is fine for a demo, but it is not the way to
    # serve this for real.
    app.run(host=os.environ.get("POSE_HOST", "127.0.0.1"), port=port, debug=False)
