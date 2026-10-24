# Neural Text-to-Speech Synthesis

A formant-based text-to-speech engine that writes WAV files.

> Generate natural speech from text with attention-based Tacotron2 plus WaveGlow vocoders, fine-tuning on a small custom voice corpus and evaluating output quality.

## Overview

An original, self-contained implementation of the **Neural Text-to-Speech Synthesis** concept, built for the Foundev portfolio. The pipeline is explicit and every stage is testable on its own:

```text
text ──▶ G2P (src/g2p.py) ──▶ phonemes ──▶ duration model (src/duration.py)
                              │                     │
                              └──▶ prosody (src/prosody.py) ──▶ waveform
```

The engine is **not** a neural TTS: there is no acoustic model and no vocoder here, and the README says so. What it does have is a real pronunciation engine, a real prosody model and an **objective** quality measure instead of "it sounds okay to me".

## Features

- A rule-based grapheme-to-phoneme engine: digraphs (`ch`, `sh`, `th`, `ph`, `ng`, `ck`, ...), r-coloured vowels, the magic `e` (`phone` → /fow-n/), the silent `e` and a lexicon of the most frequent English words
- Formant synthesis: every vowel is rendered with its three formants (F1, F2, F3), every consonant with noise, a burst or a nasal murmur
- A duration model: a linear regression over the length of a word and its number of syllables, fitted on a corpus of 44 phrases, with the time shared between the syllables and the phonemes
- A prosody model: the pitch declines over a phrase, a question rises at the end, a stressed syllable gets an accent and is a little longer, and the voice carries a small jitter and shimmer
- WAV output and a waveform plot
- An **objective** evaluation: the formant peaks of the synthesized vowels are measured with an FFT and compared with the targets of the phonemes (the *formant error* in Hz)

## Stack

`Python; Matplotlib; NumPy; scikit-learn`
The stack is Python + Matplotlib + NumPy + scikit-learn. The duration model is a scikit-learn linear regression; the rest is NumPy. No neural framework is used (see the limitations).

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

`python main.py demo` writes `artifacts/tts_demo.wav` and `artifacts/tts_waveform.png` and prints the duration MAE and the formant error.

## Structure

```text
neural-text-to-speech-synthesis/
├── main.py                 train / demo CLI
├── src/g2p.py              the letter-to-sound rules, the lexicon and the phoneme table
├── src/prosody.py          the pitch contour, the stress and the syllable weights
├── src/duration.py         the duration model and the phoneme timings
├── src/data.py             the corpus and the target durations
├── src/model.py            the synthesis, the WAV codec and the evaluation
├── tests/                  the tests of every stage
└── requirements.txt
```

## Testing

```bash
pytest -q          # 39 tests
```

The suite covers every stage of the pipeline:

| File | What it checks |
| --- | --- |
| `tests/test_g2p.py` | The letter-to-sound rules: digraphs, the magic `e`, the doubled letters, the lexicon, the syllable split and the stress. |
| `tests/test_duration.py` | The corpus, the target durations, the regression, and the way a word shares its duration between its syllables and its phonemes. |
| `tests/test_synthesis.py` | The waveform (the range, the silence, the determinism, the honoured duration), the pitch contour, the question rise and the formant error. |
| `tests/test_wav.py` | The WAV codec: what is written can be read back, byte for byte. |
| `tests/test_pipeline.py` | The end-to-end smoke test: load, train, demo. |

## Notes and limitations

- **This is not a neural TTS.** There is no acoustic model, no attention, no vocoder and no learned pronunciation; the project implements the classical pipeline that such a system would replace. A real Tacotron2 + WaveGlow build needs a GPU, a training corpus of hours and a dependency on TensorFlow, none of which fit in this environment.
- The pronunciation is rule based: the rules cover the common patterns of English and the lexicon covers the most frequent words, but an arbitrary proper noun will be pronounced wrongly. CMUdict would be the right source; it is not bundled.
- The duration model is fitted on 44 phrases whose target durations come from the usual rule of thumb (a word costs about 140 ms, a syllable about 85 ms). It is not fitted on a recorded corpus, so the MAE (about 0.1 s) measures how well the regression fits that formula, not how well it matches a speaker.
- The formant error measures that the waveform **contains** the formants that were asked for. It is a fidelity measure, not an intelligibility score: a MOS panel or an ASR round trip (synthesise → recognise → word error rate) would be the objective test this project still lacks.
- The speech is robotic: the formants do not move inside a vowel (no coarticulation), the pitch is a simple contour and there is no stress model beyond the first vowel of a word.

## License

BSD-3-Clause. See `LICENSE`.
