# Speech-to-Text Transcription Service

Transcribe synthetic spoken digit strings.

> Build a transcription and subtitle-generation service around OpenAI Whisper, optionally fine-tuned on domain vocabulary such as medical or legal speech.

## Overview

An original, self-contained implementation of the **Speech-to-Text Transcription Service** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Tone-based synthetic words with silence between them
- Energy-based word segmentation
- Random forest word classifier and sentence decode
- Word error rate plus a Flask transcription page

## Stack

`Python; Flask; NumPy; scikit-learn`
The CSV stack is Python + Flask + NumPy + scikit-learn. Those are not installed, so this build demonstrates segmentation, classification and decoding on synthetic audio.

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
speech-to-text-transcription-service/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  Flask transcription demo
```

## Testing

```bash
pytest -q
```

5 tests (`pytest -q`), up from 2.


## Notes and limitations

- No real speech is recorded or recognized.
- The vocabulary is ten digits and the audio is generated from tones.
- A real service needs a trained acoustic model, language model and audio decoding.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
