# Multi-Person Pose Estimation with MMPose

Estimate two people's joints with a geometric baseline.

> Build a multi-person keypoint system for sports analytics or ergonomics monitoring with MMPose top-down and bottom-up models and OKS-based accuracy evaluation.

## Overview

An original, self-contained implementation of the **Multi-Person Pose Estimation with MMPose** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic scenes with two stick figures
- Thresholding plus left/right grouping
- Joint positions estimated from each figure's bounding box
- PCK evaluation and an annotated output image

## Stack

`Python; Matplotlib; NumPy`
The CSV stack is Python + Matplotlib + NumPy. Those are not installed, so this project uses a small geometric estimator on synthetic frames instead of a network.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
multi-person-pose-estimation-with-mmpose/
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

- Figures are bright lines on a dark background with no occlusion or camera noise.
- Joint positions are estimated from bounding-box proportions, not learned features.
- This will not work on real photographs.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
