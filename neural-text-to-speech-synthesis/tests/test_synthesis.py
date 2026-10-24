"""Tests of the synthesis itself and of the objective evaluation."""
import numpy as np

from src.data import build_rows, PHRASES
from src.duration import fit
from src.model import formant_error, spectrum_peaks, synthesize
from src.prosody import Prosody


def _model():
    return fit(build_rows(PHRASES))


def test_a_phrase_becomes_audio():
    samples = synthesize("hello world", 16000, duration_model=_model())
    assert samples.dtype == np.int16
    assert samples.size > 16000 // 4
    assert np.max(np.abs(samples)) > 0


def test_the_audio_is_not_silent():
    samples = synthesize("hello world", 16000, duration_model=_model())
    assert float(np.mean(np.abs(samples.astype(float)))) > 50


def test_the_samples_stay_in_range():
    samples = synthesize("the quick brown fox", 16000, duration_model=_model())
    assert int(np.max(samples)) <= 32767
    assert int(np.min(samples)) >= -32768


def test_a_longer_phrase_is_longer():
    model = _model()
    short = synthesize("hello", 16000, duration_model=model)
    long = synthesize("hello world this is a much longer phrase", 16000, duration_model=model)
    assert long.size > short.size


def test_the_synthesis_is_deterministic():
    model = _model()
    first = synthesize("hello world", 16000, duration_model=model)
    second = synthesize("hello world", 16000, duration_model=model)
    assert np.array_equal(first, second)


def test_the_duration_is_honoured():
    samples = synthesize("hello world", 16000, duration=1.0, duration_model=_model())
    assert abs(samples.size / 16000 - 1.0) < 0.35


def test_an_empty_phrase_is_silent():
    samples = synthesize("   ", 16000, duration_model=_model())
    assert samples.size == 0


def test_the_spectrum_peaks_of_a_tone():
    sample_rate = 16000
    time = np.arange(sample_rate) / sample_rate
    tone = np.sin(2 * np.pi * 1000.0 * time)
    peaks = spectrum_peaks(tone, sample_rate, limit=3)
    assert any(abs(peak - 1000.0) < 30.0 for peak in peaks), peaks


def test_the_formant_error_is_reported():
    score = formant_error("hello world", 16000, _model())
    assert score["measurements"] > 0
    assert score["formant_error_hz"] >= 0
    assert score["formant_error_hz"] < 1500


def test_the_pitch_declines_over_a_statement():
    prosody = Prosody(base_pitch=120.0, declination=20.0)
    assert prosody.pitch_at(0.0, 1.0) > prosody.pitch_at(1.0, 1.0)


def test_a_question_rises_at_the_end():
    statement = Prosody(base_pitch=120.0, declination=20.0, question=False)
    question = Prosody(base_pitch=120.0, declination=20.0, question=True)
    assert question.pitch_at(1.0, 1.0) > statement.pitch_at(1.0, 1.0)


def test_the_punctuation_decides_the_contour():
    assert Prosody().with_text("is it ready?").question is True
    assert Prosody().with_text("it is ready.").question is False
