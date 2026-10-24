# Named Entity Recognition Pipeline

A token classifier for people, organisations and places.

> Extract structured entities such as names, dates, organizations, and biomedical terms from unstructured text with spaCy rule-based and transformer NER models.

## Overview

An original, self-contained implementation of the **Named Entity Recognition Pipeline** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Gazetteer-based sentence generator with BIO tags
- Token shape, prefix and neighbour features
- Logistic regression token classifier
- Entity-level precision, recall and F1

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. spaCy models are not installed, so this project trains a small feature-based token classifier with scikit-learn.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
named-entity-recognition-pipeline/
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

**The BIO labels are understood now.** A token marked as a continuation (`I-PER`) belongs to the entity before it, so `Ada Lovelace` is one entity and not two. The test proves it.
- 4 tests (`pytest -q`), up from 2.


## Notes and limitations

- Sentences are generated from templates and fixed name lists.
- The model uses hand-built features rather than contextual embeddings.
- Entity-level evaluation is a simple span match, not a full CoNLL scorer.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
