"""The API of the speech synthesiser.

The synthesis of the project really runs: the text is phonemised by the
letter-to-sound rules, the duration model says how long every phoneme lasts,
the prosody gives the pitch and the formant synthesiser writes the samples.
The WAV file is written into artifacts/ and the objective measure of the
project, the formant error in hertz, is computed on the result.
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.g2p import phonemize  # noqa: E402
from src.model import formant_error, synthesize, train, write_wav  # noqa: E402

#: The fitted duration model, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The corpus, the fitted duration model and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _number(payload, key: str, default: int) -> int:
    """One number of the request; a query string arrives as a list."""
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _words(text: str) -> list[dict]:
    """The words of a phrase with the phonemes the rules give them."""
    return [
        {"word": word.text, "phonemes": " ".join(word.phones), "syllables": word.syllable_count}
        for word in phonemize(text)
    ]


def _corpus_rows(data, duration_model) -> list[dict]:
    """The phrases of the corpus with the duration and the formant error."""
    rows = []
    for phrase in data["phrases"][:8]:
        error = formant_error(phrase, data["sample_rate"], duration_model)
        rows.append({
            "phrase": phrase,
            "words": len(phrase.split()),
            "formant_error_hz": round(float(error["formant_error_hz"]), 1),
            "measurements": error["measurements"],
        })
    return rows


def summary():
    data, model, metrics = _state()
    duration_model = model["duration_model"]
    first = data["phrases"][0]
    error = formant_error(first, data["sample_rate"], duration_model)

    return {
        "stats": {
            "duration_mae": metrics["duration_mae"],
            "formant_error_hz": round(float(error["formant_error_hz"]), 1),
            "phrases": metrics["phrases"],
            "sample_rate": metrics["sample_rate"],
        },
        "series": [{"label": row["phrase"][:22], "value": row["formant_error_hz"]}
                   for row in _corpus_rows(data, duration_model)],
        "lists": {
            "corpus": _corpus_rows(data, duration_model),
            "phonemes": _words(first),
        },
    }


def handle(method, path, payload, user):
    if method == "POST" and path == "/api/synthesize":
        text = str((payload or {}).get("text", "")).strip()
        if not text:
            return 400, {"error": "no text was sent"}
        seed = _number(payload, "seed", 42)
        data, model, _ = _state(seed)
        duration_model = model["duration_model"]
        samples = synthesize(text, data["sample_rate"], duration_model=duration_model)
        target = ROOT / "artifacts" / "tts_console.wav"
        write_wav(target, samples, data["sample_rate"])
        error = formant_error(text, data["sample_rate"], duration_model)
        encoded = base64.b64encode(target.read_bytes()).decode()
        return 200, {
            "text": text,
            "samples": int(samples.size),
            "seconds": round(float(samples.size) / data["sample_rate"], 2),
            "formant_error_hz": round(float(error["formant_error_hz"]), 1),
            "wav": str(target.relative_to(ROOT)),
            "audio": f"data:audio/wav;base64,{encoded}",
            "words": _words(text),
        }

    if method == "GET" and path == "/api/phonemes":
        text = str((payload or {}).get("text", "") or "")
        if isinstance(text, list):
            text = text[0] if text else ""
        if not text.strip():
            return 400, {"error": "no text was sent"}
        return 200, {"text": text, "words": _words(text)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
