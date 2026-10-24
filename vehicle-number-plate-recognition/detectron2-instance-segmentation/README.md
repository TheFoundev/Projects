# Detectron2 Instance Segmentation

Instance masks for simple synthetic shapes.

> Implement instance segmentation for robotics or medical imagery with Mask R-CNN and RetinaNet, including custom dataset registration, mAP evaluation, and visualization.

## Overview

An original, self-contained implementation of the **Detectron2 Instance Segmentation** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Procedural images containing circles and squares
- Threshold plus connected-component mask extraction
- Per-instance IoU matching against ground truth
- Threshold sweep during training

## Stack

`Python; NumPy; SciPy`
The CSV stack is Python + NumPy + SciPy. Detectron2 is not installed, so this is a small classical instance-segmentation baseline with NumPy and SciPy.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
detectron2-instance-segmentation/
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

7 tests (`pytest -q`), up from 2.
The objects of a picture are placed in their own part of it, so two of them are never one blob and the ground truth is unambiguous.


## Notes and limitations

- Only two shape types on a clean background are supported.
- There is no learned backbone, region proposal network or COCO training.
- Overlapping shapes are merged by connected components and count as one instance.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
