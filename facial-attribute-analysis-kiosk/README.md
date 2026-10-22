# Facial Attribute Analysis Kiosk

A small synthetic face-attribute classifier with a Flask kiosk page.

> Wrap state-of-the-art face verification and attribute analysis (age, gender, emotion, anti-spoofing) into a REST API or real-time interactive kiosk.

## Overview

An original, self-contained implementation of the **Facial Attribute Analysis Kiosk** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Procedural 32x32 face images with glasses and smile variants
- Pixel features and a multi-output random forest
- Per-attribute accuracy metrics
- Flask page that shows a sample and its predictions

## Stack

`Python; Flask; NumPy; scikit-learn`
The CSV stack is Python + Flask + NumPy + scikit-learn. DeepFace model weights are not available offline, so the project trains a tiny classifier on synthetic faces.

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
facial-attribute-analysis-kiosk/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  Flask kiosk page
```

## Testing

```bash
pytest -q
```

6 tests (`pytest -q`), up from 2.


## Notes and limitations

- The faces are drawn with rectangles and ellipses; there are no photos or real people.
- The model reads pixel patterns from the synthetic generator, not facial structure.
- Glasses and smile are the only two attributes; there is no face detection step.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
