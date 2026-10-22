# Recommender Algorithm Benchmark

Compare four recommendation strategies on the same ratings.

> Systematically compare dozens of recommender algorithms (matrix factorization, GNN, sequential models) on public datasets with unified, reproducible pipelines.

## Overview

An original, self-contained implementation of the **Recommender Algorithm Benchmark** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic ratings with popularity and genre effects
- Popularity, item-item cosine, SVD and NMF recommenders
- Precision@5, recall@5 and catalogue coverage
- Recommendation samples for one user

## Stack

`Python; NumPy; Pandas; scikit-learn`
The CSV stack is Python + NumPy + Pandas + scikit-learn. RecBole is not installed, so the benchmark uses scikit-learn matrix factorisation and simple baselines.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
recommender-algorithm-benchmark/
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

8 tests (`pytest -q`), up from 2.


## Notes and limitations

- The dataset is small and synthetic.
- Only top-5 recommendations are evaluated.
- There is no hyperparameter search or neural recommender.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
