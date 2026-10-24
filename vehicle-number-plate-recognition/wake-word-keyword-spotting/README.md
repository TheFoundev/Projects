# Wake-Word Keyword Spotting

Spot a wake phrase in synthetic audio.

> Build an always-listening wake-word recognizer for smart devices using the Google Speech Commands dataset with quantization for on-device deployment.

## Overview

An original, self-contained implementation of the **Wake-Word Keyword Spotting** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic positive phrase and negative background clips
- Log-band audio features
- Random forest keyword detector
- Accuracy and false-positive rate

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. Those datasets and models are not available offline, so the clips and classifier are generated locally.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
wake-word-keyword-spotting/
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

3 tests (`pytest -q`), up from 2.


## Notes and limitations

- All clips are synthesized from tones and noise.
- This is a binary detector, not a streaming microphone application.
- The negative clips do not cover real background sounds.

## License

BSD-3-Clause. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
