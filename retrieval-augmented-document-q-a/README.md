# Retrieval-Augmented Document Q&A

Retrieve passages with TF-IDF and answer with the best sentence.

> Build a retrieval-augmented question-answering assistant over PDFs or wiki pages with embeddings, vector stores, and evaluation of answer faithfulness.

## Overview

An original, self-contained implementation of the **Retrieval-Augmented Document Q&A** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Small built-in document collection
- TF-IDF passage retrieval
- Extractive answer selection with source attribution
- Retrieval hit rate and answer overlap metrics

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. No API key or vector database is available here, so the project uses TF-IDF retrieval and extractive answers.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
retrieval-augmented-document-q-a/
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

- Answers are sentences copied from the documents, not generated text.
- The corpus has twelve short passages and a handful of questions.
- There are no embeddings, chunking strategies or LLM calls.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
