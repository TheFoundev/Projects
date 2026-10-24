# Weed Species Detection

Classify synthetic weed species from leaf features.

> Classify eight Australian weed species in pasture imagery with transfer-learned ResNet50 and InceptionV3 models and discuss precision-agriculture deployment on drones.

## Overview

An original, self-contained implementation of the **Weed Species Detection** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Procedurally drawn leaves for four species
- Shape and colour summary features
- Random forest classifier with per-species accuracy
- Sample leaf images saved for inspection

## Stack

`Python; Matplotlib; NumPy; scikit-learn`
The CSV stack is Python + Matplotlib + NumPy + scikit-learn. Pretrained ImageNet weights are not available, so the build uses hand-built features and a random forest.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
weed-species-detection/
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

- Leaves are simple geometric shapes, not field photographs.
- Features are hand-built instead of learned by a CNN.
- There is no augmentation, transfer learning or background variation.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
