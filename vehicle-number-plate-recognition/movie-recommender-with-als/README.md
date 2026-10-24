# Movie Recommender with ALS

Matrix factorisation for movie recommendations, written from scratch.

> Create an implicit-feedback recommender on MovieLens with alternating least squares, evaluating ranking quality with MAP@K and building a lightweight Flask demo.

## Overview

An original, self-contained implementation of the **Movie Recommender with ALS** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic users, movies, genres and ratings
- Biased matrix factorisation trained with SGD
- RMSE and precision@5 evaluation
- Demo recommendation list with titles

## Stack

`Python; implicit; Pandas; SciPy`

The CSV stack is implicit + Pandas + SciPy. The implicit library is not installed, so the project implements a small explicit-feedback SGD factoriser with NumPy.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
movie-recommender-with-als/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
# see the Run section
```

## Notes and limitations

- Ratings are simulated from genre preferences plus noise.
- There is no implicit feedback, temporal drift or production serving path.
- Only a small dense matrix is supported; scaling to real catalogues is out of scope.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
