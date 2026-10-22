# Real-Time Pose Estimation App

A single-person pose estimator with a small Flask API.

> Create real-time human pose, hand, and face-mesh applications such as a fitness rep counter, gesture controller, or rehabilitation angle-measuring app.

## Overview

An original, self-contained implementation of the **Real-Time Pose Estimation App** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Moving synthetic figure across frames
- A detector that finds the people in a frame and joins the parts of one
  person together
- A trained keypoint regressor: the joints are learned from the frames with
  a ridge regression, not read off the bounding box
- PCK and the mean joint error as the metrics
- Flask endpoint returning joint coordinates as JSON
- A picture you upload, and a camera when OpenCV is installed
- An API key, a rate limit and a model that can be saved and trained again

## Stack

`Python; MediaPipe; OpenCV; Flask`

The CSV stack is MediaPipe + OpenCV + Flask. MediaPipe is not installed here,
so the project keeps the shape of a top-down pose estimator — a detector, a
keypoint regressor that is trained on the frames, and the PCK as the metric —
with a handful of learned parameters instead of a neural network. The frames
come from the simulator, from a picture you upload, or from a camera when
OpenCV is there.

## Run

```bash
pip install -r requirements.txt
python main.py train
python app.py
python main.py demo
pytest -q
```

## Structure

```text
real-time-pose-estimation-app/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  the test suite
├── requirements.txt
├── app.py                  Flask API and demo page
```

## Testing

```bash
pytest -q
```

15 tests: the detector finds the person and nothing in an empty picture, the
regressor learns the joints (the PCK has to be above a floor), the features
and the targets have the right shape, the PCK and the joint error are
computed right, two people in one picture are two people, and the API
serves a frame, estimates an uploaded picture and refuses a picture that is
not base64.

## Notes and limitations

- MediaPipe is not used, so the regressor is a ridge regression over the
  brightness of a small grid of the person, not a neural network. The
  detector also assumes bright figures on a dark background.
- The camera needs OpenCV and a camera; without them the simulator and the
  upload are the inputs.
- The person is found by the bright pixels, so a person on a bright
  background is not found.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
