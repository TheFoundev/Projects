# MONAI Medical Imaging Pipeline

A small 3D lesion segmentation and classification pipeline.

> Develop a medical imaging pipeline (organ or tumor segmentation, disease classification) using MONAI with pretrained architectures and Dice-based 3D evaluation.

## Overview

An original, self-contained implementation of the **MONAI Medical Imaging Pipeline** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic 3D volumes with spherical lesions
- Intensity normalisation and percentile thresholding
- Dice score for segmentation and accuracy for patient labels
- Slice visualisation saved for inspection

## Stack

`Python; Matplotlib; NumPy; scikit-learn`
The CSV stack is Python + Matplotlib + NumPy + scikit-learn. MONAI and nibabel are not installed, so this build uses NumPy arrays and a threshold baseline with the same workflow.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
monai-medical-imaging-pipeline/
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

- Volumes are generated in memory; no DICOM or NIfTI files are read.
- Segmentation is a threshold, not a trained U-Net.
- The patient classifier uses two hand-built features and logistic regression.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
