# GAN Image Generation

A tiny GAN that learns to draw simple shapes.

> Implement and stabilize generative adversarial networks (DCGAN, WGAN-GP, CycleGAN) to synthesize faces, digits, or style-transferred images with FID evaluation.

## Overview

An original, self-contained implementation of the **GAN Image Generation** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic 16x16 shape dataset
- Small convolutional generator and discriminator
- Short adversarial training loop
- Saved sample grid after training

## Stack

`Python; Matplotlib; NumPy; TensorFlow`
The CSV stack is Python + Matplotlib + NumPy + TensorFlow. PyTorch is not installed in this environment, so the same idea is implemented with TensorFlow/Keras.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
gan-image-generation/
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


the suite needs TensorFlow, which is in the requirements.

## Notes and limitations

- The dataset only contains simple bright shapes on a dark background.
- Training is deliberately short; the samples are rough blobs, not photorealistic images.
- This is a teaching implementation, not a stable GAN recipe.

## License

MIT. See `LICENSE`.

## What to expect

A normal run uses 90 steps and writes an 8-sample grid. The shapes stay rough; short GAN training mostly shows the pipeline working end to end.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
