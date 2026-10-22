"""Tests for the chat domain."""

import chat


def test_a_topic_has_to_be_usable():
    assert chat.is_valid_topic("general")
    assert chat.is_valid_topic("a topic")
    assert not chat.is_valid_topic("")
    assert not chat.is_valid_topic("   ")
    assert not chat.is_valid_topic("a" * (chat.MAX_TOPIC_LENGTH + 1))
    assert not chat.is_valid_topic("two\nlines")
    assert chat.is_valid_topic("a" * chat.MAX_TOPIC_LENGTH)


def test_a_topic_is_cleaned():
    assert chat.clean_topic("  general  ") == "general"
    assert chat.clean_topic("two\nlines") == "twolines"
    assert chat.clean_topic(None) == ""


def test_the_topic_key_holds_the_stream_and_the_topic():
    assert chat.topic_key("General", "general") == "general > general"
    assert chat.topic_key("General", "General") == chat.topic_key("general", "general")


def test_a_message_needs_a_stream_a_topic_and_a_body():
    streams = [{"id": 1, "name": "general"}]
    assert chat.validate_message({"channel_name": "general", "topic": "x", "body": "hi"}, streams) is None
    assert "stream" in chat.validate_message({"topic": "x", "body": "hi"}, streams)
    assert "does not exist" in chat.validate_message({"channel_name": "nope", "body": "hi"}, streams)
    # A message without a topic goes to the default one.
    assert chat.validate_message({"channel_name": "general", "topic": "", "body": "hi"}, streams) is None
    assert "topic" in chat.validate_message(
        {"channel_name": "general", "topic": "a" * (chat.MAX_TOPIC_LENGTH + 1), "body": "hi"}, streams
    )
    assert "body" in chat.validate_message({"channel_name": "general", "topic": "x", "body": "  "}, streams)
    assert "at most" in chat.validate_message(
        {"channel_name": "general", "topic": "x", "body": "a" * (chat.MAX_MESSAGE_LENGTH + 1)}, streams
    )


def test_the_messages_of_a_topic_are_grouped():
    messages = [
        {"id": 2, "topic": "b", "body": "second", "created_at": "2"},
        {"id": 1, "topic": "a", "body": "first", "created_at": "1"},
        {"id": 3, "topic": "a", "body": "third", "created_at": "3"},
    ]
    threads = chat.group_by_topic(messages)
    assert list(threads.keys()) == ["a", "b"]
    assert [m["id"] for m in threads["a"]] == [1, 3]


def test_the_threads_are_newest_first():
    messages = [
        {"id": 1, "topic": "a", "sender": "Ana", "created_at": "1"},
        {"id": 2, "topic": "b", "sender": "Bo", "created_at": "3"},
    ]
    threads = chat.thread_summary(messages, [])
    assert threads[0]["topic"] == "b"
    assert threads[0]["count"] == 1


def test_the_unread_messages_are_counted():
    messages = [
        {"id": 1, "topic": "a", "stream_name": "general"},
        {"id": 2, "topic": "a", "stream_name": "general"},
        {"id": 3, "topic": "b", "stream_name": "general"},
    ]
    markers = [{"stream": "general", "topic": "a", "message_id": 1}]
    counts = chat.unread_counts(messages, markers)
    assert counts["general > a"] == 1
    assert counts["general > b"] == 1

    assert chat.unread_counts(messages, [])["general > a"] == 2


def test_the_search_looks_in_the_body_the_topic_and_the_sender():
    messages = [
        {"id": 1, "body": "the build is broken", "topic": "x", "sender": "Ana"},
        {"id": 2, "body": "nothing here", "topic": "kubernetes", "sender": "Bo"},
        {"id": 3, "body": "nothing here", "topic": "x", "sender": "kubernetes"},
    ]
    assert len(chat.search_messages(messages, "broken")) == 1
    assert len(chat.search_messages(messages, "kubernetes")) == 2
    assert chat.search_messages(messages, "") == []
    assert chat.search_messages(messages, "zzz") == []


def test_the_summary_counts_the_messages_and_the_topics():
    streams = [{"id": 1, "name": "general"}]
    messages = [
        {"id": 1, "channel_id": 1, "topic": "a", "stream_name": "general"},
        {"id": 2, "channel_id": 1, "topic": "a", "stream_name": "general"},
        {"id": 3, "channel_id": 1, "topic": "b", "stream_name": "general"},
    ]
    summary = chat.stream_summary(streams, messages)
    assert summary[0]["messages"] == 3
    assert summary[0]["topics"] == 2


def test_the_markdown_is_rendered():
    assert "<strong>bold</strong>" in chat.render_markdown("**bold**")
    assert "<em>italic</em>" in chat.render_markdown("*italic*")
    assert "<code>code</code>" in chat.render_markdown("`code`")
    assert '<a href="https://example.test"' in chat.render_markdown("[link](https://example.test)")
    assert "<li>one</li>" in chat.render_markdown("- one")
    assert "<blockquote>" in chat.render_markdown("> quoted")


def test_the_markdown_never_lets_markup_through():
    rendered = chat.render_markdown("<script>alert(1)</script>")
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_the_markdown_keeps_the_code_as_it_is():
    rendered = chat.render_markdown("`**not bold**`")
    assert "<code>**not bold**</code>" in rendered
    assert "<strong>" not in rendered
