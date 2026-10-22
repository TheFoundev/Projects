# Model Explainability with SHAP

Permutation importance and partial dependence for a tabular model.

> Explain black-box classifiers and regressors (churn, fraud, diagnosis) with Shapley-value attributions and build an explainability report for stakeholders.

## Overview

An original, self-contained implementation of the **Model Explainability with SHAP** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic dataset with a known non-linear signal
- Random forest baseline accuracy
- SHAP values for every prediction, with `TreeExplainer`
- Global importance from the mean absolute SHAP value
- A local explanation: why one prediction was made
- A check that the explanation finds the signal the data was built from
- Permutation importance and a partial-dependence curve next to it
- Saved chart with the three explanations

## Stack

`Python; SHAP; scikit-learn; Matplotlib`

The CSV stack is SHAP + scikit-learn + Matplotlib, and that is what the
project uses: the explanations are real SHAP values from `shap.TreeExplainer`.
Permutation importance and partial dependence are kept next to them,
because they answer a different question.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
model-explainability-with-shap/
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

6 tests: the pipeline runs, the SHAP values of a prediction add up to the
difference between the baseline of the model and the prediction, the
importance is ranked, the explanation finds the signal the data was built from
and leaves the noise alone, and a local explanation adds up.

## Notes and limitations

- Permutation importance describes this model on this dataset, not causality.
- The dataset is synthetic, so the 'true' generating features are known by construction.
- There are no per-row SHAP values or interaction effects.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
