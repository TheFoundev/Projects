# Segment Anything (SAM) Fine-tuning

Point-prompted segmentation with thresholding and connected components.

> Build an interactive annotation and segmentation tool by fine-tuning Meta's SAM on a small labeled dataset such as surgical tools or surface defects.

## Overview

An original, self-contained implementation of the **Segment Anything (SAM) Fine-tuning** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic images with one or two foreground shapes
- An encoder that turns an image into an embedding and a decoder that turns a
  prompt and an embedding into a mask
- Three prompt types: a point, a box and a mask
- A fine tuning loop that fits the parameters of the decoder and reports the
  loss after every round
- IoU and success-rate evaluation
- A FastAPI endpoint that answers with the mask (run length encoded), the
  bounding box and the IoU with the truth

## Stack

`Python; PyTorch; SAM; FastAPI`

The CSV stack is PyTorch + SAM + FastAPI. The SAM weights are not available
here, so the model keeps the shape of a promptable segmenter — an encoder, a
decoder and a fine tuning loop — with a handful of learned parameters
instead of the millions of a real model, and with the same point-in,
mask-out contract.

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
segment-anything-sam-fine-tuning/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            encoder, decoder, fine tuning and evaluation
├── tests/test_pipeline.py  the test suite
├── requirements.txt
├── app.py                  FastAPI prompt endpoint
```

## Testing

```bash
pytest -q
```

11 tests: the pipeline runs, a point on an object gives the object, a point
outside an object or outside the image gives an empty mask, a box gives the
object it points at, the encoder finds the objects, the fine tuning lowers
the loss, the evaluation reports the mean and the hits, and the mask can be
encoded and read back.

## Notes and limitations

- Only one bright shape per image is supported.
- The point prompt must land inside the shape.
- There is no encoder training or mask decoder network.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
