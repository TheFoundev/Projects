# Streaming Anomaly Detection

An online EWMA detector for a simulated metric stream.

> Detect anomalies in real-time time series such as server metrics and Twitter volume by implementing and scoring custom detectors on the Numenta Anomaly Benchmark.

## Overview

An original, self-contained implementation of the **Streaming Anomaly Detection** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Streaming values with drift and injected spikes
- Online mean/variance updates with an EWMA
- Point-level precision, recall and detection delay
- Threshold sweep and a saved timeline plot

## Stack

`Python; Matplotlib; NumPy`
The CSV stack is Python + Matplotlib + NumPy. scikit-learn is not needed, so the detector is a dependency-light online implementation evaluated on a NAB-like stream.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
streaming-anomaly-detection/
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

- The stream is generated, not read from NAB.
- The detector is univariate and assumes one value per timestamp.
- Thresholds are tuned on the same simulated distribution.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
