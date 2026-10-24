# Topic Modeling with BERTopic

Group short news snippets into topics with TF-IDF and NMF.

> Uncover latent themes in large text corpora such as research abstracts, reviews, or support tickets with transformer embeddings, HDBSCAN clustering, and interactive charts.

## Overview

An original, self-contained implementation of the **Topic Modeling with BERTopic** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Small built-in news corpus
- TF-IDF vectorisation and NMF topic factors
- Document assignment with confidence scores
- Top terms and representative documents per topic

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. Those models need pretrained weights and a vector index, so this build uses TF-IDF and NMF for the same topic-assignment workflow.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
topic-modeling-with-bertopic/
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

4 tests (`pytest -q`), up from 2.


## Notes and limitations

- Documents are short synthetic news snippets.
- Topics come from word frequencies, not sentence embeddings.
- The number of topics is fixed rather than discovered.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
