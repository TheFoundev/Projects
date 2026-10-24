# Train a GPT Language Model from Scratch

A character-level transformer trained on a tiny public-domain-style corpus.

> Train a GPT language model from scratch on a domain corpus (code, chats, literature) and study scaling behavior, sampling strategies, and fine-tuning.

## Overview

An original, self-contained implementation of the **Train a GPT Language Model from Scratch** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Character tokeniser built from the training text
- Small embedding plus self-attention block
- Next-character training with sparse categorical loss
- Sampled continuation saved after training

## Stack

`Python; NumPy; TensorFlow`
The CSV stack is Python + NumPy + TensorFlow. PyTorch is unavailable, so the same architecture is built in TensorFlow/Keras without Triton serving.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
train-a-gpt-language-model-from-scratch/
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

- The corpus is a few paragraphs, so the model memorises rather than generalises.
- There is no tokeniser training, positional encoding study or large-scale pretraining.
- Sampling is temperature-based and often produces odd words.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
