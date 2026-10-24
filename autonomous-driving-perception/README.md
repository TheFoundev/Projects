# Autonomous Driving Perception

A tiny road-scene perception pipeline using thresholding and connected components.

> Study and extend an open-source driver-assistance perception stack: lane detection, vehicle detection, and driver-attention monitoring on real driving video.

## Overview

An original, self-contained implementation of the **Autonomous Driving Perception** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A lane detector and a vehicle detector over a road scene
- The lane threshold is fitted on one part of the scenes and the metrics are
  measured on the rest, so the numbers are not the ones the threshold was
  chosen for
- The lane edges are not reported as vehicles: the mask is thinned before
  the blobs are found, and a blob has to fill its own box
- The IoU of two boxes is the matching rule, and every detection is used at
  most once
- A demo that writes the scene and the lane mask to a picture

## Stack

`Python; Matplotlib; NumPy; SciPy`
The CSV stack is Python + Matplotlib + NumPy + SciPy. This build is a dependency-light Python baseline using NumPy and SciPy, since OpenCV is not installed here.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
autonomous-driving-perception/
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

13 tests: the IoU of the lanes and of the boxes, the matching of the
detections, the vehicles of a scene (and that the lane edges are not one),
the empty scene, the split of the scenes and the metrics on the scenes the
threshold was not chosen for.

## Notes and limitations

- Scenes are drawn procedurally; there is no real camera or driving dataset.
- Lane and vehicle detection are classical image operations, not a trained network.
- The evaluation is a sanity check, not a benchmark against KITTI or nuScenes.

## License

MIT. See `LICENSE`.

## What to expect

The smoke run uses small 64-pixel scenes. Expect a lane IoU around 0.8 and imperfect vehicle boxes when cars touch the lane edges.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
