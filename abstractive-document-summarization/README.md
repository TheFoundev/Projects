# Abstractive Document Summarization

A compact document summarizer using sentence ranking.

> Build a document summarization system for news, legal, or meeting transcripts using BART, T5, or PEGASUS with ROUGE evaluation and chunking for long documents.

## Overview

An original, self-contained implementation of the **Abstractive Document Summarization** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- TF-IDF sentence scoring with a position bonus
- The length of the summary is searched over the corpus, and the length that
  scores best is the one that is kept
- ROUGE-L evaluation against reference summaries, with the score of every
  length
- A small Flask page that summarizes a pasted document
- Demo mode that prints an original document and its summary

## Stack

`Python; scikit-learn; Flask`

The CSV stack of the brief is Transformers + PyTorch + Gradio. A transformer
model cannot be downloaded in this environment, so the build is an
**extractive** summarizer (TF-IDF sentence ranking) with the same train, demo
and evaluate flow. It does not write new sentences: every sentence of the
summary is a sentence of the document.

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
abstractive-document-summarization/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  the test suite
├── requirements.txt
├── app.py                  small Flask demo page
```

## Testing

```bash
pytest -q
```

15 tests: the length of the summary, the ROUGE-L score (of a text with
itself, of two unrelated texts and of a partial overlap), the search over the
lengths, the mean of the corpus and the Flask page.

## Notes and limitations

- The brief says abstractive, but this implementation is extractive: it selects whole sentences.
- There is no neural encoder-decoder, tokenizer download or generation step.
- Evaluation uses a small hand-written set of documents and reference summaries.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
