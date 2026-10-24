"""A rule-based grapheme-to-phoneme (G2P) engine for English.

The engine is deterministic and dependency free. It applies an ordered list
of letter rules (longest match first, with a left and a right context) and
falls back to a per-letter table. A small exception lexicon covers the words
that the rules get wrong often ("the", "one", "said", ...).

The phoneme inventory is the usual reduced ARPAbet set without the
stress marks; the stress is computed by :mod:`src.prosody`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: The vowels of the inventory and their formant targets (F1, F2, F3) in Hz.
VOWEL_FORMANTS: dict[str, tuple[float, float, float]] = {
    "AA": (730, 1090, 2440),
    "AE": (660, 1720, 2410),
    "AH": (640, 1190, 2390),
    "AO": (570, 840, 2410),
    "AW": (570, 840, 2410),
    "AY": (660, 1720, 2410),
    "EH": (530, 1840, 2480),
    "ER": (490, 1350, 1690),
    "EY": (400, 2100, 2650),
    "IH": (390, 1990, 2550),
    "IY": (270, 2290, 3010),
    "OW": (570, 840, 2410),
    "OY": (570, 840, 2410),
    "UH": (440, 1020, 2240),
    "UW": (300, 870, 2240),
}

#: The consonants, their kind and the frequency of their noise.
CONSONANTS: dict[str, tuple[str, float]] = {
    "B": ("stop", 0.0),
    "CH": ("affricate", 3200.0),
    "D": ("stop", 0.0),
    "DH": ("fricative", 1800.0),
    "F": ("fricative", 4500.0),
    "G": ("stop", 0.0),
    "HH": ("aspirate", 1400.0),
    "JH": ("affricate", 3200.0),
    "K": ("stop", 0.0),
    "L": ("sonorant", 0.0),
    "M": ("nasal", 250.0),
    "N": ("nasal", 250.0),
    "NG": ("nasal", 250.0),
    "P": ("stop", 0.0),
    "R": ("sonorant", 0.0),
    "S": ("fricative", 6000.0),
    "SH": ("fricative", 3000.0),
    "T": ("stop", 0.0),
    "TH": ("fricative", 1800.0),
    "V": ("fricative", 4500.0),
    "W": ("sonorant", 0.0),
    "Y": ("sonorant", 0.0),
    "Z": ("fricative", 6000.0),
    "ZH": ("fricative", 3000.0),
}

#: Every phoneme of the inventory.
PHONEMES = tuple(VOWEL_FORMANTS) + tuple(CONSONANTS)

#: The phonemes that are vowels.
VOWELS = frozenset(VOWEL_FORMANTS)

#: How long a phoneme of each kind lasts, relative to a vowel.
KIND_WEIGHT: dict[str, float] = {
    "vowel": 1.0,
    "sonorant": 0.6,
    "nasal": 0.6,
    "fricative": 0.8,
    "affricate": 0.7,
    "aspirate": 0.4,
    "stop": 0.45,
    "silence": 0.5,
}


def kind_of(phoneme: str) -> str:
    """The kind of a phoneme: ``vowel``, ``stop``, ``fricative`` ..."""
    if phoneme in VOWEL_FORMANTS:
        return "vowel"
    return CONSONANTS.get(phoneme, ("silence", 0.0))[0]


@dataclass(frozen=True)
class Rule:
    """One letter rule.

    ``letters`` is matched at the current position of the word. The rule only
    applies when the word ends with ``left`` before the match and continues
    with ``right`` after it.
    """

    letters: str
    phones: tuple[str, ...]
    left: str | None = None
    right: str | None = None
    #: The word must have at least this many letters for the rule to apply.
    min_length: int = 0
    note: str = ""


def _rule(letters, phones, left=None, right=None, note="", min_length=0) -> Rule:
    return Rule(letters, tuple(phones), left, right, min_length, note)


#: The ordered rule table. The first rule that matches wins, so the table is
#: sorted from the longest letter sequences to the shortest.
RULES: tuple[Rule, ...] = (
    # --- multi-letter endings -------------------------------------------
    _rule("tion", ("SH", "AH", "N"), note="-tion"),
    _rule("sion", ("ZH", "AH", "N"), right="", note="-sion at the end"),
    _rule("cious", ("SH", "AH", "S")),
    _rule("tious", ("SH", "AH", "S")),
    _rule("ture", ("CH", "ER")),
    _rule("sure", ("ZH", "ER"), left="s"),
    _rule("augh", ("AO",)),
    _rule("ough", ("AH", "F"), note="could be OW, AH is used here"),
    _rule("eigh", ("EY",)),
    _rule("ight", ("AY", "T")),
    _rule("igh", ("AY",)),
    _rule("tch", ("CH",)),
    _rule("dge", ("JH",)),
    _rule("ph", ("F",)),
    _rule("gh", ()),
    _rule("th", ("TH",)),
    _rule("sh", ("SH",)),
    _rule("ch", ("CH",)),
    _rule("ck", ("K",)),
    _rule("ng", ("NG",), right=""),
    _rule("nk", ("NG", "K")),
    _rule("qu", ("K", "W")),
    _rule("wh", ("W",)),
    _rule("wr", ("R",), left=""),
    _rule("kn", ("N",), left=""),
    _rule("gn", ("N",), left=""),
    _rule("ps", ("S",), left=""),
    # --- vowel digraphs --------------------------------------------------
    _rule("eau", ("OW",)),
    _rule("ee", ("IY",)),
    _rule("ea", ("IY",)),
    _rule("ie", ("IY",)),
    _rule("ei", ("EY",)),
    _rule("ai", ("EY",)),
    _rule("ay", ("EY",)),
    _rule("oa", ("OW",)),
    _rule("oe", ("OW",)),
    _rule("oo", ("UW",)),
    _rule("ou", ("AW",)),
    _rule("ow", ("AW",), right=""),
    _rule("oi", ("OY",)),
    _rule("oy", ("OY",)),
    _rule("au", ("AO",)),
    _rule("aw", ("AO",)),
    _rule("ue", ("UW",)),
    _rule("ui", ("UW",)),
    _rule("eu", ("UW",)),
    _rule("ew", ("UW",)),
    # --- the silent e at the end of a word ------------------------------
    _rule("e", (), right="", min_length=3, note="the silent e at the end"),
    # --- r-coloured vowels ----------------------------------------------
    _rule("ar", ("AA", "R")),
    _rule("er", ("ER",)),
    _rule("ir", ("ER",)),
    _rule("ur", ("ER",)),
    _rule("or", ("AO", "R")),
    _rule("yr", ("ER",)),
    # --- single letters ---------------------------------------------------
    _rule("a", ("AE",)),
    _rule("b", ("B",)),
    _rule("c", ("K",)),
    _rule("d", ("D",)),
    _rule("e", ("EH",)),
    _rule("f", ("F",)),
    _rule("g", ("G",)),
    _rule("h", ("HH",)),
    _rule("i", ("IH",)),
    _rule("j", ("JH",)),
    _rule("k", ("K",)),
    _rule("l", ("L",)),
    _rule("m", ("M",)),
    _rule("n", ("N",)),
    _rule("o", ("AA",)),
    _rule("p", ("P",)),
    _rule("q", ("K",)),
    _rule("r", ("R",)),
    _rule("s", ("S",)),
    _rule("t", ("T",)),
    _rule("u", ("AH",)),
    _rule("v", ("V",)),
    _rule("w", ("W",)),
    _rule("x", ("K", "S")),
    _rule("y", ("IY",)),
    _rule("z", ("Z",)),
)

#: The long counterpart of a short vowel, used by the silent ``e``.
LONG_VOWEL: dict[str, str] = {
    "AE": "EY",   # a -> e
    "EH": "IY",   # e -> i
    "IH": "AY",   # i -> a
    "AA": "OW",   # o -> o
    "AH": "UW",   # u -> u
    "IY": "AY",   # y -> a
}

#: Words the rules get wrong. The value is the phoneme sequence.
LEXICON: dict[str, tuple[str, ...]] = {
    "a": ("AH",),
    "again": ("AH", "G", "EH", "N"),
    "all": ("AO", "L"),
    "am": ("AE", "M"),
    "an": ("AE", "N"),
    "and": ("AE", "N", "D"),
    "are": ("AA", "R"),
    "as": ("AE", "Z"),
    "at": ("AE", "T"),
    "be": ("B", "IY"),
    "been": ("B", "IH", "N"),
    "brown": ("B", "R", "AW", "N"),
    "but": ("B", "AH", "T"),
    "by": ("B", "AY"),
    "can": ("K", "AE", "N"),
    "come": ("K", "AH", "M"),
    "done": ("D", "AH", "N"),
    "give": ("G", "IH", "V"),
    "have": ("HH", "AE", "V"),
    "love": ("L", "AH", "V"),
    "some": ("S", "AH", "M"),
    "do": ("D", "UW"),
    "does": ("D", "AH", "Z"),
    "for": ("F", "AO", "R"),
    "fox": ("F", "AA", "K", "S"),
    "from": ("F", "R", "AH", "M"),
    "go": ("G", "OW"),
    "good": ("G", "UH", "D"),
    "has": ("HH", "AE", "Z"),
    "he": ("HH", "IY"),
    "hello": ("HH", "AH", "L", "OW"),
    "her": ("HH", "ER"),
    "him": ("HH", "IH", "M"),
    "his": ("HH", "IH", "Z"),
    "i": ("AY",),
    "if": ("IH", "F"),
    "in": ("IH", "N"),
    "is": ("IH", "Z"),
    "it": ("IH", "T"),
    "me": ("M", "IY"),
    "morning": ("M", "AO", "R", "N", "IH", "NG"),
    "my": ("M", "AY"),
    "no": ("N", "OW"),
    "not": ("N", "AA", "T"),
    "of": ("AH", "V"),
    "on": ("AA", "N"),
    "one": ("W", "AH", "N"),
    "or": ("AO", "R"),
    "our": ("AW", "ER"),
    "out": ("AW", "T"),
    "please": ("P", "L", "IY", "Z"),
    "quick": ("K", "W", "IH", "K"),
    "ready": ("R", "EH", "D", "IY"),
    "said": ("S", "EH", "D"),
    "she": ("SH", "IY"),
    "should": ("SH", "UH", "D"),
    "so": ("S", "OW"),
    "system": ("S", "IH", "S", "T", "AH", "M"),
    "than": ("DH", "AE", "N"),
    "that": ("DH", "AE", "T"),
    "the": ("DH", "AH"),
    "their": ("DH", "EH", "R"),
    "them": ("DH", "EH", "M"),
    "then": ("DH", "EH", "N"),
    "there": ("DH", "EH", "R"),
    "they": ("DH", "EY"),
    "this": ("DH", "IH", "S"),
    "to": ("T", "UW"),
    "two": ("T", "UW"),
    "up": ("AH", "P"),
    "us": ("AH", "S"),
    "was": ("W", "AA", "Z"),
    "we": ("W", "IY"),
    "were": ("W", "ER"),
    "what": ("W", "AH", "T"),
    "when": ("W", "EH", "N"),
    "where": ("W", "EH", "R"),
    "which": ("W", "IH", "CH"),
    "who": ("HH", "UW"),
    "why": ("W", "AY"),
    "will": ("W", "IH", "L"),
    "with": ("W", "IH", "DH"),
    "world": ("W", "ER", "L", "D"),
    "would": ("W", "UH", "D"),
    "yes": ("Y", "EH", "S"),
    "you": ("Y", "UW"),
    "your": ("Y", "AO", "R"),
}


@dataclass
class Word:
    """The phonemes of one word with its syllable structure."""

    text: str
    phones: list[str] = field(default_factory=list)
    #: The index of the vowel that carries the primary stress.
    stress_index: int = 0

    @property
    def syllable_count(self) -> int:
        return sum(1 for phone in self.phones if phone in VOWELS)


def _apply_rules(word: str) -> list[str]:
    """Turn a word into phonemes with the rule table."""
    phones: list[str] = []
    position = 0
    length = len(word)
    while position < length:
        for rule in RULES:
            end = position + len(rule.letters)
            if word[position:end] != rule.letters:
                continue
            if rule.left is not None and not word[:position].endswith(rule.left):
                continue
            if rule.min_length and len(word) < rule.min_length:
                continue
            if rule.right is not None:
                following = word[end:]
                if rule.right == "":
                    if following:
                        continue
                elif not following.startswith(rule.right):
                    continue
            phones.extend(rule.phones)
            position = end
            break
        else:
            # No rule matched: skip the character rather than guessing.
            position += 1
    return phones


def _strip_magic_e(word: str) -> tuple[str, bool]:
    """Remove the silent ``e`` of a magic-e word.

    "phone" is written with a silent ``e``: the vowel before it is long
    ("pho-ne" is /fow-n/). The word is returned without that ``e`` and the
    flag says that the last vowel has to be made long.
    """
    if len(word) > 2 and word.endswith("e") and word[-2] not in "aeiou":
        return word[:-1], True
    return word, False


def _apply_magic_e(phones: list[str]) -> list[str]:
    """Turn the last vowel of a magic-e word into its long counterpart."""
    for index in range(len(phones) - 1, -1, -1):
        if phones[index] in VOWELS:
            long = LONG_VOWEL.get(phones[index])
            if long:
                phones[index] = long
            return phones
    return phones


def _collapse_doubles(phones: list[str]) -> list[str]:
    """Collapse doubled consonants ("letter" -> "L EH T ER")."""
    collapsed: list[str] = []
    for phone in phones:
        if collapsed and collapsed[-1] == phone and phone not in VOWELS:
            continue
        collapsed.append(phone)
    return collapsed


def phonemize_word(word: str) -> Word:
    """Turn a word into its phoneme sequence."""
    cleaned = "".join(character for character in word.lower() if character.isalpha())
    if not cleaned:
        return Word(text=word, phones=[])
    if cleaned in LEXICON:
        phones = list(LEXICON[cleaned])
    else:
        stripped, magic = _strip_magic_e(cleaned)
        phones = _apply_rules(stripped)
        phones = _collapse_doubles(phones)
        if magic:
            phones = _apply_magic_e(phones)
    vowels = [index for index, phone in enumerate(phones) if phone in VOWELS]
    stress_index = vowels[0] if vowels else 0
    return Word(text=cleaned, phones=phones, stress_index=stress_index)


def phonemize(text: str) -> list[Word]:
    """Turn a phrase into its words with their phonemes."""
    return [phonemize_word(word) for word in text.split() if word]


def syllable_offsets(phones: list[str]) -> list[int]:
    """The index of the vowel that starts each syllable."""
    return [index for index, phone in enumerate(phones) if phone in VOWELS]


def word_to_syllables(word: Word) -> list[list[str]]:
    """Split the phonemes of a word into syllables.

    A syllable starts at the consonant that precedes its vowel, so the
    clusters are onsets and only the tail of the word is a coda.
    """
    phones = word.phones
    vowels = syllable_offsets(phones)
    if not vowels:
        return [phones] if phones else []
    starts: list[int] = []
    previous_end = 0
    for vowel in vowels:
        starts.append(previous_end)
        previous_end = vowel + 1
    syllables: list[list[str]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(phones)
        syllables.append(phones[start:end])
    return syllables
