"""Tests for the chat API, driven through the Flask test client."""

import os
import tempfile

import pytest


@pytest.fixture()
def client(monkeypatch):
    """A Flask client with a throwaway database."""
    path = tempfile.mktemp(prefix="zulip-test-", suffix=".sqlite")
    # The environment is set before the module is imported, so the schema is
    # created in the throwaway database and not in the real one.
    monkeypatch.setenv("APP_DB", path)

    import app as app_module

    # The path is restored after the test, so the other suites keep their own
    # database.
    monkeypatch.setattr(app_module, "DB_PATH", path)
    app_module.init_db()
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client

    if os.path.exists(path):
        os.unlink(path)


def register(client, name="Ana", email="ana@example.test"):
    """Sign up, the way the form does it."""
    client.get("/register")
    with client.session_transaction() as session:
        token = session.get("csrf")
    response = client.post(
        "/register",
        data={"name": name, "email": email, "password": "correct-horse", "csrf": token},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return response


def stream_id(client, name="engineering"):
    """The id of a stream, by name."""
    streams = client.get("/api/streams").get_json()["streams"]
    for entry in streams:
        if entry["stream"]["name"] == name:
            return entry["stream"]["id"]
    raise AssertionError(f"the stream {name} does not exist")


def csrf(client):
    """The CSRF token of the session."""
    with client.session_transaction() as session:
        return session.get("csrf")


def test_the_streams_are_listed(client):
    register(client)
    response = client.get("/api/streams")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["streams"]
    assert "unread" in payload


def test_a_message_can_be_sent(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    response = client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "hello", "body": "A first message", "csrf": token},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["topic"] == "hello"
    assert payload["body"] == "A first message"


def test_a_message_for_a_stream_that_does_not_exist_is_refused(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    response = client.post(
        "/api/messages",
        data={"channel_name": "nope", "topic": "hello", "body": "A message", "csrf": token},
    )
    assert response.status_code == 400
    assert "does not exist" in response.get_json()["error"]


def test_a_message_without_a_body_is_refused(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    response = client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "hello", "body": "   ", "csrf": token},
    )
    assert response.status_code == 400
    assert "body" in response.get_json()["error"]


def test_a_message_needs_the_csrf_token(client):
    register(client)
    response = client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "hello", "body": "A message"},
    )
    assert response.status_code == 400


def test_the_threads_of_a_stream_are_listed(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    for topic in ("one", "one", "two"):
        client.post(
            "/api/messages",
            data={"channel_name": "engineering", "topic": topic, "body": "A message", "csrf": token},
        )

    response = client.get(f"/api/streams/{stream_id(client)}")
    assert response.status_code == 200
    threads = {thread["topic"]: thread["count"] for thread in response.get_json()["threads"]}
    assert threads["one"] == 2, "the messages of a topic are together"
    assert threads["two"] == 1


def test_the_search_finds_a_message(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "builds", "body": "the build is broken", "csrf": token},
    )

    response = client.get("/api/search?q=broken")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == 1
    assert payload["messages"][0]["body"] == "the build is broken"


def test_a_topic_can_be_marked_as_read(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "hello", "body": "A message", "csrf": token},
    )

    streams = client.get("/api/streams").get_json()
    assert streams["unread"], "the message starts unread"

    response = client.post("/api/read", data={"stream": "engineering", "topic": "hello", "csrf": token})
    assert response.status_code == 200

    streams = client.get("/api/streams").get_json()
    assert "engineering > hello" not in streams["unread"], "the topic is read now"


def test_a_topic_can_be_subscribed_to(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    response = client.post(
        "/api/topics/subscribe",
        data={"stream": "engineering", "topic": "hello", "csrf": token},
    )
    assert response.status_code == 201

    topics = client.get("/api/topics").get_json()["topics"]
    assert topics == [{"stream": "engineering", "topic": "hello"}]


def test_the_channel_page_groups_the_messages_by_topic(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "one", "body": "First", "csrf": token},
    )
    client.post(
        "/api/messages",
        data={"channel_name": "engineering", "topic": "two", "body": "Second", "csrf": token},
    )

    streams = client.get("/api/streams").get_json()["streams"]
    response = client.get(f"/channels/{stream_id(client)}")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Topic: one" in body
    assert "Topic: two" in body


def test_the_markup_of_a_message_is_rendered_and_escaped(client):
    register(client)
    with client.session_transaction() as session:
        token = session.get("csrf")

    client.post(
        "/api/messages",
        data={
            "channel_name": "engineering",
            "topic": "one",
            "body": "**bold** <script>alert(1)</script>",
            "csrf": token,
        },
    )

    body = client.get(f"/channels/{stream_id(client)}").get_data(as_text=True)
    assert "<strong>bold</strong>" in body
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body
