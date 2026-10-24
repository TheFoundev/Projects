"""Shared ORB denomination matcher for the Note Sense backend.

Same pipeline as ``Currency Detection using OpenCV in ML/detect.py``:
ORB keypoints -> brute-force matching -> Lowe's ratio test at 0.789 ->
the reference note with the most good matches wins.

The difference is the reference set: ``detect.py`` compares against six
hand-picked photographs, this module compares against every reference photo
shipped in ``files/`` and groups the results per denomination, so a note
uploaded from the browser is matched against all of them at once.
"""

import os
import re

import cv2

ROOT = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(ROOT, "Currency Detection using OpenCV in ML", "files")

LOWE_RATIO = 0.789
MIN_GOOD_MATCHES = 8
MAX_UPLOAD_BYTES = 12 * 1024 * 1024

_orb = cv2.ORB_create()
_bf = cv2.BFMatcher()
_references = None


def denomination_of(filename):
    """Map a reference file name to its denomination string ('200', '2000', ...)."""
    base = os.path.splitext(os.path.basename(filename))[0]
    base = re.sub(r"\(.*?\)", "", base)
    base = re.sub(r"^test_", "", base)
    base = re.sub(r"[ _]\d+$", "", base)
    match = re.match(r"^(\d+)", base)
    return match.group(1) if match else None


def load_references():
    """Return [(name, denomination, descriptors), ...], cached after the first call."""
    global _references
    if _references is not None:
        return _references

    references = []
    if os.path.isdir(REFERENCE_DIR):
        for name in sorted(os.listdir(REFERENCE_DIR)):
            if not name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            image = cv2.imread(os.path.join(REFERENCE_DIR, name))
            if image is None:
                continue
            denomination = denomination_of(name)
            if denomination is None:
                continue
            _, descriptors = _orb.detectAndCompute(image, None)
            if descriptors is None or len(descriptors) < 2:
                continue
            references.append((name, denomination, descriptors))

    _references = references
    return references


def _good_matches(test_descriptors, reference_descriptors):
    if test_descriptors is None or len(test_descriptors) < 2:
        return 0
    pairs = _bf.knnMatch(test_descriptors, reference_descriptors, k=2)
    good = 0
    for pair in pairs:
        if len(pair) != 2:
            continue
        best, second = pair
        if best.distance < LOWE_RATIO * second.distance:
            good += 1
    return good


def detect_image(image):
    """Match a BGR image against the reference set and return a result dict."""
    references = load_references()
    if not references:
        return {
            "ok": False,
            "error": "no references",
            "message": "No reference photographs were found in " + REFERENCE_DIR,
        }

    _, test_descriptors = _orb.detectAndCompute(image, None)
    if test_descriptors is None:
        return {
            "ok": False,
            "error": "no keypoints",
            "message": "No keypoints could be detected in that photo. "
                       "Try a sharper, well lit picture of one side of the note.",
        }

    per_denomination = {}
    for name, denomination, descriptors in references:
        good = _good_matches(test_descriptors, descriptors)
        current = per_denomination.get(denomination)
        if current is None or good > current["count"]:
            per_denomination[denomination] = {"count": good, "reference": name}

    ranked = sorted(per_denomination.items(), key=lambda item: -item[1]["count"])
    winner_denomination, winner = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    result = {
        "ok": winner["count"] > MIN_GOOD_MATCHES,
        "denomination": winner_denomination,
        "label": "Rs. " + winner_denomination,
        "reference": winner["reference"],
        "good_matches": winner["count"],
        "runner_up": runner_up[0] if runner_up else None,
        "runner_up_matches": runner_up[1]["count"] if runner_up else 0,
        "method": "ORB + brute force matching + Lowe's ratio %.3f" % LOWE_RATIO,
        "reference_count": len(references),
        "counts": {denomination: data["count"] for denomination, data in ranked},
    }

    if not result["ok"]:
        result["message"] = (
            "Only %d good keypoint matches — below the threshold of %d, so no "
            "denomination is claimed. Try a sharper, well lit photo of the note."
            % (winner["count"], MIN_GOOD_MATCHES)
        )
    return result


def detect_bytes(data):
    """Decode an image file (bytes) and detect its denomination."""
    if not data:
        return {"ok": False, "error": "empty upload", "message": "The photo did not arrive."}
    buffer = np_frombytes(data)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        return {
            "ok": False,
            "error": "unreadable image",
            "message": "That file could not be read as an image.",
        }
    return detect_image(image)


def np_frombytes(data):
    import numpy as np

    return np.frombuffer(data, dtype=np.uint8)
