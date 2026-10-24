# Hybrid Recommender with Content Features

Blend collaborative filtering with item tags for recommendations.

> Combine collaborative filtering with content features such as genres and tags using LightFM to solve the cold-start problem and expose recommendations through a REST API.

## Overview

An original, self-contained implementation of the **Hybrid Recommender with Content Features** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic user ratings and item tag vectors
- Truncated SVD collaborative scores
- Content similarity from a user's liked-item profile
- Precision@5 evaluation and a demo recommendation list

## Stack

`Python; NumPy; Pandas; scikit-learn`
The CSV stack is Python + NumPy + Pandas + scikit-learn. LightFM is not installed, so the hybrid scorer is built from scikit-learn's TruncatedSVD plus a content cosine score.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
hybrid-recommender-with-content-features/
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

5 tests (`pytest -q`), up from 2.


## Notes and limitations

- Users, items and ratings are simulated.
- The content profile is a simple average of tags from highly rated items.
- There is no cold-start handling, implicit feedback or online serving layer.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
