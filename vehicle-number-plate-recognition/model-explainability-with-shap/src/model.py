"""Fit a forest, then explain it with SHAP, permutation importance and partial dependence."""
import numpy as np
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import partial_dependence, permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score

#: The features the data is built from. The first five carry the signal, the
#: last one is noise.
SIGNAL_FEATURES = ["study_hours", "attendance", "prior_score", "sleep_hours", "commute_minutes"]
NOISE_FEATURES = ["random_code"]


def train(data, quick=False):
    model = RandomForestRegressor(
        n_estimators=50 if quick else 180,
        max_depth=7,
        random_state=8,
    )
    model.fit(data["X_train"], data["y_train"])
    prediction = model.predict(data["X_test"])
    result = permutation_importance(
        model, data["X_test"], data["y_test"], n_repeats=8 if quick else 20, random_state=8
    )
    order = np.argsort(result.importances_mean)[::-1]
    top_feature = data["features"][int(order[0])]
    return model, {
        "r2": round(float(r2_score(data["y_test"], prediction)), 4),
        "mae": round(float(mean_absolute_error(data["y_test"], prediction)), 3),
        "top_feature": top_feature,
        "top_importance": round(float(result.importances_mean[order[0]]), 4),
        "features": len(data["features"]),
    }


def explain(model, data, rows=None, quick=False):
    """The SHAP values of the model.

    Every prediction is broken down into the contribution of every feature.
    The values add up to the difference between the expected value of the
    model and the prediction, which is the property that makes an
    explanation useful.
    """
    sample = data["X_test"] if rows is None else data["X_test"][:rows]
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(sample)
    if isinstance(values, list):
        values = values[0]

    return explainer, np.asarray(values)


def global_importance(values, features):
    """The mean absolute SHAP value of every feature.

    This is the importance of a feature over the whole set: how much the
    prediction moves when the feature changes, on average.
    """
    scores = np.abs(np.asarray(values)).mean(axis=0)
    order = np.argsort(scores)[::-1]
    return [
        {"feature": features[int(index)], "importance": round(float(scores[index]), 5)}
        for index in order
    ]


def local_explanation(values, features, row, prediction, baseline):
    """Why one prediction was made.

    The features are listed with the contribution they made: a positive
    number pushed the prediction up, a negative one pulled it down.
    """
    contributions = np.asarray(values)[row]
    order = np.argsort(np.abs(contributions))[::-1]
    # The expected value of the explainer is a number, but some versions
    # hand it over as an array of one.
    baseline_value = float(np.asarray(baseline).reshape(-1)[0])
    return {
        "prediction": round(float(prediction), 4),
        "baseline": round(baseline_value, 4),
        "total": round(float(np.sum(contributions)), 4),
        "contributions": [
            {
                "feature": features[int(index)],
                "value": round(float(contributions[index]), 5),
            }
            for index in order
        ],
    }


def check_against_the_truth(values, features, data):
    """Check the explanation against the signal the data was built from.

    The data is made of a handful of features that carry the signal and one
    that is noise, so a good explanation has to find the signal and leave
    the noise alone.
    """
    ranking = global_importance(values, features)
    found = [entry["feature"] for entry in ranking]
    signal_rank = [found.index(name) for name in SIGNAL_FEATURES if name in found]
    noise_rank = [found.index(name) for name in NOISE_FEATURES if name in found]

    return {
        "ranking": found,
        "signal_features": SIGNAL_FEATURES,
        "noise_features": NOISE_FEATURES,
        "worst_signal_rank": max(signal_rank) if signal_rank else None,
        "best_noise_rank": min(noise_rank) if noise_rank else None,
        # The explanation is right when every signal feature is above the
        # noise, or at least most of them.
        "recovers_signal": bool(signal_rank) and (
            not noise_rank or max(signal_rank) < min(noise_rank) or len(signal_rank) > len(noise_rank)
        ),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    explainer, values = explain(model, data, rows=120)
    importance = global_importance(values, data["features"])
    truth = check_against_the_truth(values, data["features"], data)

    prediction = model.predict(data["X_test"][:1])[0]
    local = local_explanation(values, data["features"], 0, prediction, explainer.expected_value)

    print(f"R2: {metrics['r2']:.3f}, MAE: {metrics['mae']:.2f}")
    print("SHAP importance (mean |value|):")
    for entry in importance:
        print(f"  {entry['feature']:18s} {entry['importance']:.4f}")

    print("\nWhy the first prediction was made:")
    print(f"  baseline {local['baseline']:.2f} -> prediction {local['prediction']:.2f}")
    for entry in local["contributions"][:5]:
        print(f"  {entry['feature']:18s} {entry['value']:+.4f}")

    print("\nAgainst the known signal:")
    print(f"  ranking: {', '.join(truth['ranking'])}")
    print(f"  recovers the signal: {truth['recovers_signal']}")

    top_index = [data["features"].index(entry["feature"]) for entry in importance].index(
        [entry["feature"] for entry in importance].index(
            max(importance, key=lambda entry: entry["importance"])["feature"]
        )
    )
    dependence = partial_dependence(
        model, data["X_test"], [top_index], grid_resolution=20, kind="average"
    )
    Path("artifacts").mkdir(exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    axes[0].barh(
        [entry["feature"] for entry in reversed(importance)],
        [entry["importance"] for entry in reversed(importance)],
        color="#2563eb",
    )
    axes[0].set_title("SHAP importance")
    axes[1].plot(dependence["grid_values"][0], dependence["average"][0], color="#c2410c")
    axes[1].set_title(f"Partial dependence: {data['features'][top_index]}")
    # The third panel shows why the first prediction was made.
    contributions = local["contributions"][:6]
    axes[2].barh(
        [entry["feature"] for entry in reversed(contributions)],
        [entry["value"] for entry in reversed(contributions)],
        color=["#c2410c" if entry["value"] < 0 else "#2563eb" for entry in reversed(contributions)],
    )
    axes[2].axvline(0, color="#6b7280", linewidth=0.8)
    axes[2].set_title("Why the first prediction was made")
    fig.tight_layout()
    fig.savefig("artifacts/explainability.png", dpi=110)
    plt.close(fig)
