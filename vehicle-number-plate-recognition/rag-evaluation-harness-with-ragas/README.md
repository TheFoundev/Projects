# RAG Evaluation Harness with RAGAS

Measure retrieval and answer quality on a small synthetic QA set.

> Measure and improve retrieval quality with automated metrics for faithfulness, context recall and answer relevancy plus regression tests.

## Overview

An original, self-contained implementation of the **RAG Evaluation Harness with RAGAS** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic question, answer and context triples
- TF-IDF retrieval with a hit-rate metric
- Token overlap F1 for short answers
- Faithfulness check against the retrieved context

## Stack

`Python; NumPy; Pandas; scikit-learn`
The CSV stack is Python + NumPy + Pandas + scikit-learn. Those packages are not installed, so the evaluation metrics and retrieval are implemented directly with scikit-learn and plain Python.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
rag-evaluation-harness-with-ragas/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
pytest -q
```

5 tests (`pytest -q`), up from 2.


## Notes and limitations

- Questions and contexts are synthetic and very small in number.
- Retrieval is TF-IDF, not an embedding index.
- The answer extractor picks a sentence from the context, so the evaluation is optimistic.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
