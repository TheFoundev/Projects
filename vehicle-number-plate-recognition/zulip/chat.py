"""
The chat domain.

The rules behind a stream and a topic: what a topic may look like, how a
message is checked before it is sent, how the messages of a topic are put
in order, how the unread counts are worked out and how the markdown of a
message is rendered.

Pure functions, no database access, so the rules can be unit tested on their
own.
"""

import html
import re
from typing import Iterable

#: The longest a topic may be.
MAX_TOPIC_LENGTH = 60

#: The longest a message may be.
MAX_MESSAGE_LENGTH = 10_000

#: The topics that are always there.
DEFAULT_TOPIC = "general"

#: The kinds of message there are.
MESSAGE_TYPES = ("stream", "private")

#: A topic is a short phrase, without newlines and without control characters.
_TOPIC_STRIP = re.compile(r"[\x00-\x1f\x7f]")


def is_valid_topic(topic: str) -> bool:
    """True when the topic may be used.

    A topic is a short phrase on one line: a control character, such as a
    newline, is never part of one.
    """
    if not isinstance(topic, str):
        return False
    if _TOPIC_STRIP.search(topic):
        return False
    cleaned = topic.strip()
    return 0 < len(cleaned) <= MAX_TOPIC_LENGTH


def clean_topic(topic: str) -> str:
    """The topic as it is stored: without the control characters and spaces."""
    return _TOPIC_STRIP.sub("", str(topic or "")).strip()


def topic_key(stream: str, topic: str) -> str:
    """The key a topic is filed under: the stream and the topic together."""
    return f"{clean_topic(stream).lower()} > {clean_topic(topic).lower()}"


def validate_message(values: dict, streams: Iterable[dict]) -> str | None:
    """Check a message before it is sent.

    The stream has to exist, the topic has to be a usable one and the body
    has to say something. The error message is returned, or None.
    """
    stream = clean_topic(values.get("channel_name") or values.get("stream") or "")
    topic = clean_topic(values.get("topic") or DEFAULT_TOPIC)
    body = str(values.get("body") or "").strip()

    if not stream:
        return "A message needs a stream."

    known = {clean_topic(s.get("name", "")).lower() for s in streams}
    if stream.lower() not in known:
        return f'The stream "{stream}" does not exist.'

    if not is_valid_topic(topic):
        return f"A topic has to be between 1 and {MAX_TOPIC_LENGTH} characters."

    if not body:
        return "A message needs a body."

    if len(body) > MAX_MESSAGE_LENGTH:
        return f"A message can be at most {MAX_MESSAGE_LENGTH} characters."

    return None


def stream_of_message(message: dict, streams: Iterable[dict]) -> dict | None:
    """The stream a message belongs to."""
    channel_id = message.get("channel_id")
    for stream in streams:
        if int(stream.get("id", -1)) == int(channel_id or -1):
            return stream
    return None


def group_by_topic(messages: Iterable[dict]) -> dict:
    """The messages of a stream, grouped by topic.

    The topics keep the order they were first seen in, and inside a topic
    the messages are in the order they arrived.
    """
    threads: dict[str, list] = {}
    for message in sorted(messages, key=lambda m: int(m.get("id") or 0)):
        topic = clean_topic(message.get("topic") or DEFAULT_TOPIC)
        threads.setdefault(topic, []).append(message)
    return threads


def thread_summary(messages: Iterable[dict], streams: Iterable[dict]) -> list:
    """The threads of a stream, newest first.

    Every thread carries the messages, how many there are, who started it
    and when it was last touched.
    """
    threads = group_by_topic(messages)
    summary = []
    for topic, items in threads.items():
        summary.append(
            {
                "topic": topic,
                "key": topic_key(str(items[0].get("stream_name", "")), topic),
                "messages": items,
                "count": len(items),
                "sender": items[0].get("sender", ""),
                "last_at": items[-1].get("created_at", ""),
            }
        )
    summary.sort(key=lambda thread: thread["last_at"], reverse=True)
    return summary


def unread_counts(messages: Iterable[dict], read_markers: Iterable[dict]) -> dict:
    """How many messages are unread in every topic.

    A read marker says the last message of a topic that was read. A topic
    without a marker is unread from the start.
    """
    markers = {}
    for marker in read_markers:
        key = topic_key(marker.get("stream", ""), marker.get("topic", ""))
        markers[key] = int(marker.get("message_id") or 0)

    counts: dict[str, int] = {}
    for message in messages:
        key = topic_key(message.get("stream_name", ""), message.get("topic", ""))
        last_read = markers.get(key, 0)
        if int(message.get("id") or 0) > last_read:
            counts[key] = counts.get(key, 0) + 1
    return counts


def search_messages(messages: Iterable[dict], query: str) -> list:
    """The messages that match the query.

    The body, the topic and the sender are searched. The newest message
    comes first.
    """
    needle = str(query or "").strip().lower()
    if not needle:
        return []

    found = []
    for message in messages:
        haystack = " ".join(
            str(message.get(key) or "") for key in ("body", "topic", "sender", "stream_name")
        ).lower()
        if needle in haystack:
            found.append(message)
    found.sort(key=lambda m: int(m.get("id") or 0), reverse=True)
    return found


def stream_summary(streams: Iterable[dict], messages: Iterable[dict]) -> list:
    """The streams, with the number of messages and of unread ones."""
    unread = unread_counts(messages, [])
    summary = []
    for stream in streams:
        stream_messages = [
            message
            for message in messages
            if int(message.get("channel_id") or -1) == int(stream.get("id") or -1)
        ]
        topics = {clean_topic(m.get("topic") or DEFAULT_TOPIC) for m in stream_messages}
        summary.append(
            {
                "stream": stream,
                "messages": len(stream_messages),
                "topics": len(topics),
                "unread": sum(
                    count
                    for key, count in unread.items()
                    if key.startswith(f"{clean_topic(stream.get('name', '')).lower()} >")
                ),
            }
        )
    summary.sort(key=lambda entry: entry["stream"].get("name", "").lower())
    return summary


# --------------------------------------------------------------------- #
# Markdown                                                            #
# --------------------------------------------------------------------- #

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def render_markdown(text: str) -> str:
    """Render the markdown of a message.

    Everything is escaped first, so no markup in a message can become
    markup in the page. After that the small set of markdown the app
    supports is applied: inline code, bold, italic, links, bullet lists
    and quotes.
    """
    if not text:
        return ""

    codes: list[str] = []

    def stash_code(match: re.Match) -> str:
        codes.append(f"<code>{html.escape(match.group(1), quote=True)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    # The lines are handled first, because the markers of a list or a quote
    # have to be recognised before the text is escaped.
    blocks: list[str] = []
    in_list = False
    in_quote = False

    def close_blocks() -> None:
        nonlocal in_list, in_quote
        if in_list:
            blocks.append("</ul>")
            in_list = False
        if in_quote:
            blocks.append("</blockquote>")
            in_quote = False

    for raw_line in str(text).split("\n"):
        stripped = raw_line.strip()
        if stripped.startswith("- "):
            if not in_list:
                close_blocks()
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li>{render_inline(stripped[2:], codes, stash_code)}</li>")
        elif stripped.startswith("> "):
            if not in_quote:
                close_blocks()
                blocks.append("<blockquote>")
                in_quote = True
            blocks.append(f"<p>{render_inline(stripped[2:], codes, stash_code)}</p>")
        elif stripped == "":
            close_blocks()
        else:
            close_blocks()
            blocks.append(f"<p>{render_inline(stripped, codes, stash_code)}</p>")

    close_blocks()
    rendered = "".join(blocks)

    for index, code in enumerate(codes):
        rendered = rendered.replace(f"\x00{index}\x00", code)

    return rendered


def render_inline(text: str, codes: list, stash_code) -> str:
    """Render the inline markdown of one line."""
    escaped = html.escape(text, quote=True)
    escaped = _INLINE_CODE.sub(stash_code, escaped)
    escaped = _LINK.sub(
        lambda m: f'<a href="{m.group(2)}" rel="noopener noreferrer" target="_blank">{m.group(1)}</a>',
        escaped,
    )
    escaped = _BOLD.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC.sub(r"<em>\1</em>", escaped)
    return escaped
