# AI Recruitment and Resume Screening Team

Rank resumes against a job description with skills and a small classifier.

> Automate a hiring pipeline with collaborating agents that parse resumes, match skills to job descriptions, shortlist candidates and draft interview questions.

## Overview

An original, self-contained implementation of the **AI Recruitment and Resume Screening Team** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A resume parser that reads the facts (the years, the degree, the number of
  the projects and the skills) out of the text of the resume
- A logistic regression over the text, with the candidates stored in SQLite
- The interview questions drafted from the resume: a question for every skill
  it mentions, a question for every skill of the job it does not mention, and
  a few general ones
- A read-only dashboard over the candidates

## Stack

`Python; CrewAI; Streamlit; SQLite`

The CSV stack is CrewAI + Streamlit + SQLite. CrewAI and Streamlit are not installed, so the pipeline uses a small classifier and Flask with a SQLite table.

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
ai-recruitment-and-resume-screening-team/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  Flask candidate dashboard
```

## Testing

```bash
pytest -q
```

13 tests: the parser, the label (the same skills can give both labels, so
the label is not a function of the skills), the metrics, the candidates in the
database, the ranking, the questions for the interview and the dashboard.

## Notes and limitations

- Resumes are synthetic; no real applicant data is used.
- The label is generated from a simple skills/experience policy, so the model learns that policy.
- There is no PDF parsing, bias audit or human-in-the-loop review.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
