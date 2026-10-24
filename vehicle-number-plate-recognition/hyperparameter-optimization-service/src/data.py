"""A compact synthetic classification problem."""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split


def load_data(seed=42, quick=False):
    X, y = make_classification(
        n_samples=320 if quick else 900,
        n_features=12,
        n_informative=6,
        n_redundant=2,
        n_classes=2,
        class_sep=0.9,
        flip_y=0.04,
        random_state=seed,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y
    )
    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}
