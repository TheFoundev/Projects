"""Formant synthesis, the WAV codec and the objective evaluation.

The synthesizer turns a phrase into a waveform with four steps:

1. :mod:`src.g2p` turns the text into phonemes,
2. :mod:`src.duration` says how long every phoneme lasts,
3. :mod:`src.prosody` gives the pitch of every phoneme,
4. the phonemes are rendered: vowels with their three formants, consonants
   with noise or with a burst.

The evaluation is objective instead of a matter of taste: the formant peaks
of the synthesized vowels are measured with an FFT and compared with the
targets of the phonemes, which gives the **formant error in Hz**. The lower
it is, the closer the synthesis is to the intended phonemes.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from src.data import PHRASES
from src.duration import DurationModel, fit as fit_duration_model
from src.g2p import (
    CONSONANTS,
    VOWEL_FORMANTS,
    VOWELS,
    Word,
    phonemize,
    kind_of,
    word_to_syllables,
)
from src.prosody import Prosody, pitch_curve, syllable_durations

DEFAULT_SAMPLE_RATE = 16000


def _resonate(signal: np.ndarray, frequency: float, bandwidth: float, sample_rate: int) -> np.ndarray:
    """Filter a signal with a two pole resonator."""
    if signal.size == 0:
        return signal
    r = float(np.exp(-np.pi * bandwidth / sample_rate))
    theta = 2.0 * np.pi * frequency / sample_rate
    a1 = 2.0 * r * np.cos(theta)
    a2 = -r * r
    gain = (1.0 - r) * np.sqrt(1.0 - 2.0 * r * np.cos(2.0 * theta) + r * r)
    output = np.zeros_like(signal, dtype=float)
    previous = 0.0
    before = 0.0
    for index, sample in enumerate(signal):
        value = gain * sample + a1 * previous + a2 * before
        output[index] = value
        before = previous
        previous = value
    return output


def _render_vowel(
    phone: str,
    count: int,
    sample_rate: int,
    pitch: float,
    stress: float,
    seed: int = 0,
) -> np.ndarray:
    """Render a vowel with its three formants.

    The fundamental carries a slow jitter and the whole voice a slow
    shimmer, so the result does not sound like a pure tone.
    """
    first, second, third = VOWEL_FORMANTS[phone]
    time = np.arange(count) / sample_rate
    voice = np.zeros(count)
    # The first formant carries the most energy, the third the least.
    for frequency, amplitude in ((first, 1.0), (second, 0.45), (third, 0.18)):
        if frequency <= 0 or frequency >= sample_rate / 2:
            continue
        voice += amplitude * np.sin(2.0 * np.pi * frequency * time)
    # A little of the fundamental keeps the voice from sounding like a flute.
    rng = np.random.default_rng(seed)
    jitter = 1.0 + 0.01 * np.sin(2.0 * np.pi * 4.7 * time + rng.random() * 6.28)
    phase = 2.0 * np.pi * pitch * np.cumsum(jitter) / sample_rate
    voice += 0.25 * np.sin(phase)
    shimmer = 1.0 + 0.05 * np.sin(2.0 * np.pi * 3.1 * time + 0.7)
    voice = voice * shimmer
    return voice * (0.75 + 0.25 * stress)


def _render_consonant(phone: str, count: int, sample_rate: int, pitch: float) -> np.ndarray:
    """Render a consonant: noise, a burst or a nasal murmur."""
    kind, centre = CONSONANTS.get(phone, ("silence", 0.0))
    if kind == "silence" or count <= 0:
        return np.zeros(count)
    rng = np.random.default_rng(abs(hash(phone)) % (2**32))
    if kind in ("fricative", "aspirate", "affricate"):
        noise = rng.normal(0.0, 1.0, count)
        if kind == "affricate":
            # A fricative that grows into a burst.
            noise[: max(1, count // 2)] *= 0.4
        shaped = _resonate(noise, centre, 900.0, sample_rate)
        peak = np.max(np.abs(shaped))
        if peak > 0:
            shaped = shaped / peak
        return 0.35 * shaped
    if kind == "stop":
        # A closure, then a short burst of noise.
        burst = np.zeros(count)
        start = max(0, count - max(1, count // 4))
        noise = rng.normal(0.0, 1.0, count - start)
        shaped = _resonate(noise, 2500.0, 1800.0, sample_rate)
        peak = np.max(np.abs(shaped))
        if peak > 0:
            shaped = shaped / peak
        burst[start:] = 0.3 * shaped
        return burst
    if kind == "nasal":
        time = np.arange(count) / sample_rate
        murmur = 0.3 * np.sin(2.0 * np.pi * pitch * time)
        return _resonate(murmur, centre, 300.0, sample_rate)
    # Sonorants: a voiced glide.
    time = np.arange(count) / sample_rate
    return 0.25 * np.sin(2.0 * np.pi * pitch * time)


def _envelope(count: int, attack: float = 0.15, release: float = 0.25) -> np.ndarray:
    """A simple attack/decay envelope, so the phonemes do not click."""
    if count <= 0:
        return np.zeros(0)
    envelope = np.ones(count)
    attack_samples = max(1, int(count * attack))
    release_samples = max(1, int(count * release))
    envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)
    envelope[-release_samples:] *= np.linspace(1.0, 0.0, release_samples)
    return envelope


def _render_phrase(
    phrase: str,
    sample_rate: int,
    duration: float | None,
    duration_model: DurationModel | None,
    prosody: Prosody | None,
    seed: int,
) -> tuple[np.ndarray, list[tuple[str, int, int]]]:
    """Render a phrase and report where every phoneme is."""
    prosody = (prosody or Prosody()).with_text(phrase)
    words = phonemize(phrase)
    if not words:
        return np.zeros(0, dtype=np.int16), []

    model = duration_model
    if model is None:
        model = fit_duration_model([("x", 5, 2, 0.6)])

    word_durations = []
    for word in words:
        if duration is not None:
            word_durations.append(duration / len(words))
        else:
            word_durations.append(model.predict_word(len(word.text), word.syllable_count))
    total_duration = sum(word_durations)

    rng = np.random.default_rng(seed)
    pieces: list[np.ndarray] = []
    layout: list[tuple[str, int, int]] = []
    elapsed = 0.0
    cursor = 0

    for word, word_duration in zip(words, word_durations):
        syllables = word_to_syllables(word)
        syllable_times = syllable_durations(word, word_duration, prosody)
        phoneme_times: list[float] = []
        for syllable, syllable_time in zip(syllables, syllable_times):
            weights = [1.0] * len(syllable)
            phoneme_times.extend(
                syllable_time * weight / max(sum(weights), 1e-9) for weight in weights
            )
        if len(phoneme_times) < len(word.phones):
            phoneme_times.extend(
                [word_duration / max(1, len(word.phones))] * (len(word.phones) - len(phoneme_times))
            )

        for index, (phone, phone_duration) in enumerate(zip(word.phones, phoneme_times)):
            count = max(1, int(round(phone_duration * sample_rate)))
            pitch = prosody.pitch_at(elapsed, total_duration)
            stressed = index == word.stress_index
            if phone in VOWELS:
                segment = _render_vowel(
                    phone, count, sample_rate, pitch, 1.0 if stressed else 0.0, seed + cursor
                )
            else:
                segment = _render_consonant(phone, count, sample_rate, pitch)
            segment = segment * _envelope(count)
            pieces.append(segment)
            layout.append((phone, cursor, cursor + count))
            cursor += count
            elapsed += phone_duration

    if not pieces:
        return np.zeros(0, dtype=np.int16), []

    signal = np.concatenate(pieces)
    signal = signal + 0.004 * rng.normal(0.0, 1.0, signal.size)
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal = signal / peak
    return (0.85 * signal * 32767).astype(np.int16), layout


def synthesize(
    phrase: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    duration: float | None = None,
    duration_model: DurationModel | None = None,
    prosody: Prosody | None = None,
    seed: int = 0,
) -> np.ndarray:
    """Synthesize a phrase into a waveform of 16 bit samples.

    ``duration`` overrides the duration model when it is given.
    """
    samples, _ = _render_phrase(
        phrase, sample_rate, duration, duration_model, prosody, seed
    )
    return samples


def write_wav(path: str | Path, samples: np.ndarray, sample_rate: int = DEFAULT_SAMPLE_RATE) -> Path:
    """Write 16 bit mono samples to a WAV file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(np.asarray(samples, dtype=np.int16).tobytes())
    return target


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a WAV file back into its samples and its sample rate."""
    with wave.open(str(path), "rb") as handle:
        frames = handle.readframes(handle.getnframes())
        sample_rate = handle.getframerate()
    samples = np.frombuffer(frames, dtype=np.int16)
    return samples, sample_rate


def spectrum_peaks(signal: np.ndarray, sample_rate: int, limit: int = 3) -> list[float]:
    """The strongest frequencies of a signal, in Hz."""
    if signal.size < 32:
        return []
    windowed = signal * np.hanning(signal.size)
    spectrum = np.abs(np.fft.rfft(windowed))
    frequencies = np.fft.rfftfreq(signal.size, 1.0 / sample_rate)
    spectrum[0] = 0.0
    peaks: list[float] = []
    for index in range(1, len(spectrum) - 1):
        if spectrum[index] > spectrum[index - 1] and spectrum[index] >= spectrum[index + 1]:
            peaks.append(float(frequencies[index]))
    peaks.sort(key=lambda frequency: spectrum[int(frequency * len(signal) / sample_rate)], reverse=True)
    return sorted(peaks[:limit])


def formant_error(
    phrase: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    duration_model: DurationModel | None = None,
) -> dict:
    """How far the synthesized formants are from the intended ones.

    The phrase is synthesized as it is, and the middle of every vowel is
    analysed with an FFT. The formant peaks that are found are compared with
    the targets of the phoneme: the measure is the mean distance in Hz
    between a target and the closest peak.
    """
    model = duration_model or fit_duration_model([("x", 5, 2, 0.6)])
    samples, layout = _render_phrase(phrase, sample_rate, None, model, Prosody(), 0)
    errors: list[float] = []
    for phone, start, end in layout:
        if phone not in VOWELS:
            continue
        middle = start + (end - start) // 4
        stop = end - (end - start) // 4
        segment = samples[middle:stop].astype(float)
        if segment.size < 64:
            continue
        peaks = spectrum_peaks(segment, sample_rate, limit=6)
        if not peaks:
            continue
        for target in VOWEL_FORMANTS[phone]:
            errors.append(min(abs(target - peak) for peak in peaks))
    if not errors:
        return {"formant_error_hz": 0.0, "measurements": 0}
    return {
        "formant_error_hz": float(np.mean(errors)),
        "measurements": len(errors),
    }


def train(data: dict, quick: bool = False) -> tuple[dict, dict]:
    """Fit the duration model on the corpus."""
    rows = data["rows"]
    model = fit_duration_model(rows)
    metrics = {
        "duration_mae": round(model.mae, 4),
        "phrases": len(rows),
        "sample_rate": data["sample_rate"],
    }
    return {"duration_model": model}, metrics


def demo(data: dict) -> dict:
    """Synthesize one phrase, write the WAV file and the waveform plot."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    model, metrics = train(data, quick=True)
    phrase = data["phrases"][0]
    duration_model = model["duration_model"]
    samples = synthesize(phrase, data["sample_rate"], duration_model=duration_model)
    output = Path("artifacts/tts_demo.wav")
    write_wav(output, samples, data["sample_rate"])

    figure, axes = plt.subplots(figsize=(10, 3))
    axes.plot(np.arange(samples.size) / data["sample_rate"], samples, linewidth=0.5)
    axes.set_title(f"Synthesized '{phrase}'")
    axes.set_xlabel("time (s)")
    axes.set_ylabel("amplitude")
    figure.tight_layout()
    figure.savefig("artifacts/tts_waveform.png", dpi=120)
    plt.close(figure)

    score = formant_error(phrase, data["sample_rate"], duration_model)
    print(f"Synthesized '{phrase}' to {output} ({len(samples) / data['sample_rate']:.2f}s)")
    print(f"Duration model MAE: {metrics['duration_mae']:.3f}s")
    print(f"Formant error: {score['formant_error_hz']:.0f} Hz over {score['measurements']} measurements")
    return {"path": str(output), "samples": len(samples), **metrics, **score}
