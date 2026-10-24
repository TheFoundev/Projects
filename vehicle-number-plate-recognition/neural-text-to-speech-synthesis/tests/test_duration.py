"""Tests of the duration model."""
from src.data import PHRASES, build_rows, load_data, phrase_syllables, target_duration
from src.duration import fit
from src.g2p import phonemize_word
from src.prosody import Prosody, phoneme_durations, syllable_durations


def test_the_corpus_is_not_empty():
    data = load_data()
    assert data["rows"]
    assert len(data["rows"]) == len(data["phrases"])


def test_the_quick_corpus_is_smaller():
    assert len(load_data(quick=True)["rows"]) < len(load_data()["rows"])


def test_the_target_duration_grows_with_the_phrase():
    short = target_duration("hello world")
    long = target_duration("hello world, this is a much longer phrase to speak")
    assert 0 < short < long


def test_the_syllable_count_is_at_least_one():
    assert phrase_syllables("rhythm") >= 1
    assert phrase_syllables("hello world") == 3


def test_the_model_fits_the_corpus():
    rows = build_rows(PHRASES)
    model = fit(rows)
    assert model.mae < 0.2
    assert model.mean_syllable > 0


def test_the_model_needs_a_sample():
    try:
        fit([])
    except ValueError:
        return
    raise AssertionError("an empty corpus must be refused")


def test_the_predicted_duration_follows_the_length():
    model = fit(build_rows(PHRASES))
    short = model.predict_word(5, 1)
    long = model.predict_word(40, 7)
    assert short < long
    assert short > 0


def test_the_syllables_share_the_duration_of_the_word():
    model = fit(build_rows(PHRASES))
    word = phonemize_word("hello")
    prosody = Prosody()
    durations = syllable_durations(word, 0.5, prosody)
    assert len(durations) == 2
    assert abs(sum(durations) - 0.5) < 1e-9
    assert all(duration > 0 for duration in durations)


def test_the_phonemes_share_the_duration_of_the_syllable():
    durations = phoneme_durations(["K", "AE", "T"], 0.3)
    assert len(durations) == 3
    assert abs(sum(durations) - 0.3) < 1e-9


def test_a_stressed_syllable_is_longer():
    model = fit(build_rows(PHRASES))
    word = phonemize_word("hello")
    plain = syllable_durations(word, 0.5, Prosody(stress_length=1.0))
    stressed = syllable_durations(word, 0.5, Prosody(stress_length=1.6))
    assert stressed[0] > plain[0]
