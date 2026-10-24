import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="saleor-test-")

import app as application  # noqa: E402


def test_meta_and_home():
    client = application.app.test_client()
    meta = client.get("/api/meta")
    assert meta.status_code == 200
    assert meta.get_json()["name"]
    assert client.get("/").status_code == 200


def test_register_and_create_resource():
    client = application.app.test_client()
    home = client.get("/")
    assert home.status_code == 200
    token = None
    with client.session_transaction() as sess:
        token = sess.get("csrf")
    if token is None:
        client.get("/login")
        with client.session_transaction() as sess:
            token = sess.get("csrf")
    response = client.post("/register", data={
        "name": "Test Owner", "email": "owner@example.test",
        "password": "correct-horse", "csrf": token,
    }, follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        token = sess.get("csrf")
    resource = application.CONFIG["resources"][0]
    payload = {"csrf": token}
    for field in resource["fields"]:
        if field.get("type") in ("int", "real"):
            payload[field["name"]] = "1"
        elif field.get("type") == "bool":
            payload[field["name"]] = "1"
        else:
            payload[field["name"]] = "smoke test"
    created = client.post(f'/r/{resource["name"]}/new', data=payload, follow_redirects=True)
    assert created.status_code == 200
    listing = client.get(f'/api/{resource["name"]}')
    assert listing.status_code == 200
    assert len(listing.get_json()["items"]) >= 1
