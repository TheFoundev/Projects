# End-to-End Speech Recognition with SpeechBrain

A digit recognizer built on synthetic speech-like audio.

> Train end-to-end speech systems (ASR, speaker verification, or TTS) with SpeechBrain recipes on public corpora and package the model behind a servable interface.

## Overview

An original, self-contained implementation of the **End-to-End Speech Recognition with SpeechBrain** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic spoken digits made from tone formants
- Log-band audio features without external audio libraries
- Random forest classifier with a confusion summary
- Demo that recognizes a freshly generated word

## Stack

`Python; NumPy; SciPy; scikit-learn`
The CSV stack is Python + NumPy + SciPy + scikit-learn. Those packages are not installed here, so the project uses NumPy audio synthesis plus a classical classifier to demonstrate the same train/evaluate/recognize flow.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
end-to-end-speech-recognition-with-speechbrain/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
pytest -q
```

6 tests (`pytest -q`), up from 2.

## Notes and limitations

- Audio is synthesized from tones, not recorded human speech.
- The feature extractor is a simplified log-band energy representation, not real MFCCs.
- Accuracy on synthetic tones does not transfer to a real speech dataset.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
