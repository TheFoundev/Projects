# Wav2Vec2 Low-Resource ASR Fine-tuning

Frame-level phonetic classification with greedy decoding.

> Adapt self-supervised speech representations by fine-tuning Wav2Vec 2.0 with very limited labels for low-resource language or accented ASR.

## Overview

An original, self-contained implementation of the **Wav2Vec2 Low-Resource ASR Fine-tuning** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic words made from phoneme-like tone segments
- Frame features and frame-level labels
- Random forest frame classifier
- Greedy collapse decoding and word error rate

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. Pretrained models are not available here, so the project uses frame-level features and a small classifier.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
wav2vec2-low-resource-asr-fine-tuning/
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

- The audio is synthesized and the 'phonemes' are tone bands.
- The model classifies independent frames; it is not a self-supervised speech model.
- Greedy decoding is simple and has no language model.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
