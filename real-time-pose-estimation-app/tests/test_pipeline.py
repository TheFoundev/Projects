"""Tests for the pose estimator."""
import base64
import io

import numpy as np
from src.data import load_data, make_frame
from src.model import (
    JOINT_NAMES,
    build_training_set,
    crop_features,
    estimate,
    find_people,
    mean_joint_error,
    pck,
    predict_joints,
    target_joints,
    train,
    demo,
)


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


def test_the_detector_finds_the_person():
    frame = make_frame(1)
    boxes = find_people(frame["image"])
    assert len(boxes) == 1
    assert boxes[0]["x1"] > boxes[0]["x0"]
    assert boxes[0]["y1"] > boxes[0]["y0"]


def test_the_detector_finds_nothing_in_an_empty_image():
    empty = np.zeros((32, 32))
    assert find_people(empty) == []


def test_the_regressor_learns_the_joints():
    """The estimated joints have to be close to the true ones."""
    data = load_data(seed=5, quick=True)
    model, metrics = train(data, quick=True)

    assert metrics["pck"] > 0.5, metrics
    assert metrics["mean_joint_error"] < 12, metrics


def test_the_estimation_gives_every_joint():
    frame = make_frame(2)
    data = load_data(seed=5, quick=True)
    model, _ = train(data, quick=True)

    people = estimate(frame["image"], model)
    assert len(people) == 1
    assert people[0]["joints"].shape == (len(JOINT_NAMES), 2)


def test_the_features_have_the_right_size():
    frame = make_frame(3)
    box = find_people(frame["image"])[0]
    features = crop_features(frame["image"], box)
    assert len(features) == 8 * 8 + 2


def test_the_targets_are_relative_to_the_box():
    frame = make_frame(4)
    box = find_people(frame["image"])[0]
    relative = target_joints(frame["joints"], box)
    assert relative.shape == (len(JOINT_NAMES), 2)
    assert (relative >= -0.5).all() and (relative <= 1.5).all()


def test_the_building_set_has_a_row_for_every_frame():
    data = load_data(seed=6, quick=True)
    features, targets = build_training_set(data["frames"])
    assert len(features) == len(targets)
    assert len(features) > 0


def test_the_pck_counts_the_hits():
    truth = np.array([[10.0, 10.0], [12.0, 12.0], [14.0, 14.0]])
    assert pck(truth, truth) == 1.0
    far = truth + 1000
    assert pck(far, truth) == 0.0


def test_the_joint_error_is_the_distance():
    truth = np.array([[10.0, 10.0], [20.0, 20.0]])
    predicted = truth + np.array([3.0, 0.0])
    assert abs(mean_joint_error(predicted, truth) - 3) < 0.001


def test_two_people_are_both_found():
    """Two people in one picture are two people."""
    first = make_frame(1)
    second = make_frame(9)
    # The second figure is moved to the right of the first one.
    image = first["image"].copy()
    offset = 32
    shifted = np.zeros_like(image)
    shifted[:, offset:] = image[:, : image.shape[1] - offset]
    image = np.maximum(image, shifted)

    boxes = find_people(image)
    assert len(boxes) == 2


def test_the_api_serves_a_frame():
    from app import app

    client = app.test_client()
    response = client.get("/frame")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["names"] == JOINT_NAMES
    assert payload["people"]
    assert payload["pck"] > 0


def test_the_api_estimates_an_uploaded_picture():
    from app import app

    frame = make_frame(2)
    try:
        from PIL import Image
        buffer = io.BytesIO()
        Image.fromarray(frame["image"].astype("uint8")).save(buffer, format="PNG")
        payload = base64.b64encode(buffer.getvalue()).decode()
    except ImportError:
        return

    client = app.test_client()
    response = client.post("/frame", json={"image": payload})
    assert response.status_code == 200
    body = response.get_json()
    assert body["source"] == "upload"
    assert body["people"]


def test_the_api_refuses_a_picture_that_is_not_base64():
    from app import app

    client = app.test_client()
    response = client.post("/frame", json={"image": "not base64 !!"})
    assert response.status_code == 400
