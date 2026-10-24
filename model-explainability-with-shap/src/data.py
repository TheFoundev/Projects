"""Tabular data with a non-linear target and two noise columns."""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    count = 260 if quick else 700
    frame = pd.DataFrame({
        "study_hours": rng.normal(5, 1.8, count).clip(0, 12),
        "attendance": rng.normal(0.82, 0.10, count).clip(0, 1),
        "prior_score": rng.normal(65, 12, count).clip(0, 100),
        "sleep_hours": rng.normal(7, 1.2, count).clip(3, 11),
        "commute_minutes": rng.normal(25, 12, count).clip(0, 90),
        "random_code": rng.integers(0, 100, count),
    })
    signal = (
        0.8 * frame["study_hours"]
        + 22 * frame["attendance"]
        + 0.28 * frame["prior_score"]
        + 0.9 * np.minimum(frame["sleep_hours"], 8)
        - 0.05 * frame["commute_minutes"]
        + 0.004 * frame["study_hours"] * frame["prior_score"]
        + rng.normal(0, 2.4, count)
    )
    frame["final_score"] = signal.clip(0, 100)

    features = [column for column in frame.columns if column != "final_score"]
    train, test = train_test_split(frame, test_size=0.25, random_state=seed)
    return {
        "train": train,
        "test": test,
        "features": features,
        "X_train": train[features].to_numpy(),
        "X_test": test[features].to_numpy(),
        "y_train": train["final_score"].to_numpy(),
        "y_test": test["final_score"].to_numpy(),
    }
