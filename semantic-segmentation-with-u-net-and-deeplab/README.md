# Semantic Segmentation with U-Net and DeepLab

A tiny U-Net for synthetic shape segmentation.

> Segment road scenes, cells, or organs by training U-Net/DeepLabV3+/PSPNet backbones with pretrained encoders and comparing Dice and IoU metrics across architectures.

## Overview

An original, self-contained implementation of the **Semantic Segmentation with U-Net and DeepLab** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic 32x32 images and binary masks
- Small encoder-decoder U-Net in Keras
- Dice and pixel accuracy metrics
- Prediction panel saved after training

## Stack

`Python; Matplotlib; NumPy; TensorFlow`
The CSV stack is Python + Matplotlib + NumPy + TensorFlow.pytorch + Albumentations. PyTorch is unavailable, so the same U-Net shape is implemented in TensorFlow/Keras.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
semantic-segmentation-with-u-net-and-deeplab/
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

- Images are simple shapes on a noisy background, not photographs.
- Training is very short; this is a pipeline demonstration, not a strong segmenter.
- There is no augmentation library or pretrained encoder.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
