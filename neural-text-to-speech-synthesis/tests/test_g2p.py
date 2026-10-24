"""Tests of the letter-to-sound rules."""
from src.g2p import (
    LEXICON,
    VOWELS,
    kind_of,
    phonemize,
    phonemize_word,
    syllable_offsets,
    word_to_syllables,
)


def test_every_phoneme_is_known():
    for word in ["hello world", "the quick brown fox jumps", "system ready"]:
        for phone in phonemize_word(word).phones:
            assert kind_of(phone) in {
                "vowel",
                "stop",
                "fricative",
                "affricate",
                "aspirate",
                "sonorant",
                "nasal",
            }, phone


def test_a_word_becomes_phonemes():
    word = phonemize_word("cat")
    assert list(word.phones) == ["K", "AE", "T"]


def test_digraphs_use_one_phoneme():
    assert list(phonemize_word("ship").phones) == ["SH", "IH", "P"]
    assert list(phonemize_word("chip").phones) == ["CH", "IH", "P"]
    assert list(phonemize_word("think").phones) == ["TH", "IH", "NG", "K"]
    assert list(phonemize_word("phone").phones) == ["F", "OW", "N"]


def test_a_silent_e_makes_the_vowel_long():
    short = phonemize_word("kit").phones
    long = phonemize_word("kite").phones
    assert short[0] == "K" and long[0] == "K"
    assert short[1] in VOWELS and long[1] in VOWELS
    assert short[1] != long[1]


def test_a_doubled_letter_is_one_sound():
    assert list(phonemize_word("letter").phones) == ["L", "EH", "T", "ER"]
    assert list(phonemize_word("hello").phones) == ["HH", "AH", "L", "OW"]


def test_the_lexicon_wins_over_the_rules():
    for word, phones in LEXICON.items():
        assert list(phonemize_word(word).phones) == list(phones), word


def test_a_word_without_letters_is_empty():
    assert phonemize_word("123!").phones == []
    assert phonemize_word("").phones == []


def test_the_syllables_are_the_vowels():
    word = phonemize_word("hello")
    offsets = syllable_offsets(word.phones)
    assert len(offsets) == 2
    syllables = word_to_syllables(word)
    assert len(syllables) == 2
    assert syllables[0] == ["HH", "AH"]
    assert syllables[1] == ["L", "OW"]


def test_a_phrase_is_split_into_words():
    words = phonemize("hello world")
    assert [word.text for word in words] == ["hello", "world"]
    assert all(word.phones for word in words)


def test_the_stress_is_on_a_vowel():
    for word in phonemize("hello world the fox"):
        if word.phones:
            assert word.phones[word.stress_index] in VOWELS
