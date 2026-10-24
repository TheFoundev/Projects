# Industrial Defect Detection

Find scratches and blotches on synthetic material textures.

> Detect manufacturing defects without defect labels by training unsupervised anomaly models (PatchCore, PaDiM) on MVTec AD and visualizing anomaly heatmaps.

## Overview

An original, self-contained implementation of the **Industrial Defect Detection** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Procedural fabric-like texture with optional defects
- PCA reconstruction error as an anomaly score
- ROC AUC and threshold-based precision/recall
- Sample defect images saved for inspection

## Stack

`Python; Matplotlib; NumPy; scikit-learn`
The CSV stack is Python + Matplotlib + NumPy + scikit-learn. This build uses a PCA reconstruction baseline on NumPy patches instead of a trained anomaly model.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
industrial-defect-detection/
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

- Textures and defects are generated; there is no MVTec or camera data.
- Only image-level labels are evaluated; defect localisation is not scored.
- A production line would need per-material calibration and much more data.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
