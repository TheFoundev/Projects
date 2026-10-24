from src.data import load_data
from src.model import train, demo


def test_pipeline_runs(capsys):
    data = load_data(seed=1, quick=True)
    assert data is not None

    model, metrics = train(data, quick=True)
    assert model is not None
    assert isinstance(metrics, dict) and metrics

    for value in metrics.values():
        if isinstance(value, bool):
            continue
        assert value is None or isinstance(value, (int, float, str))

    demo(data)
    assert capsys.readouterr().out.strip()


def test_seed_is_usable():
    first = load_data(seed=3, quick=True)
    second = load_data(seed=3, quick=True)
    assert first.keys() == second.keys()
    assert first["rows"] == second["rows"]


def test_the_model_is_picklable():
    import pickle

    data = load_data(seed=1, quick=True)
    model, _ = train(data, quick=True)
    restored = pickle.loads(pickle.dumps(model))
    assert restored["duration_model"].mae == model["duration_model"].mae
