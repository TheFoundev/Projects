import os
import pickle

import numpy as np
import cv2
from django.conf import settings

MODEL_PATH = os.path.join(str(settings.BASE_DIR), "cnn_model.h5")
LABEL_PATH = os.path.join(str(settings.BASE_DIR), "label_transform.pkl")

_model = None
_label_binarizer = None
_backend_ready = None


def _ensure_backend():
    global _model, _label_binarizer, _backend_ready
    if _backend_ready is not None:
        return _backend_ready
    try:
        from tensorflow.keras.models import load_model
        from tensorflow.keras.preprocessing.image import img_to_array  # noqa: F401
        _model = load_model(MODEL_PATH)
        with open(LABEL_PATH, "rb") as f:
            _label_binarizer = pickle.load(f)
        _backend_ready = True
    except Exception as exc:  # noqa: BLE001
        _backend_ready = False
        _backend_ready_error = str(exc)
    return _backend_ready


def decode_image(file_bytes):
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    img = cv2.resize(img, (256, 256))
    from tensorflow.keras.preprocessing.image import img_to_array
    return img_to_array(img)


def predict(file_bytes):
    if not _ensure_backend():
        raise RuntimeError("CNN backend is not ready")

    x = decode_image(file_bytes)
    if x is None:
        raise ValueError("could not decode image")

    x = np.array([x], dtype=np.float16) / 225.0
    probs = _model.predict(x, verbose=0)[0]
    idx = int(np.argmax(probs))
    name = str(_label_binarizer.classes_[idx])
    confidence = float(probs[idx])
    healthy = "healthy" in name.lower()

    return {
        "disease": name,
        "healthy": healthy,
        "confidence": confidence,
    }
