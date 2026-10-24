"""API of the Thunderdome planning poker: rooms, players and votes."""

from __future__ import annotations


def _state():
    return {
        "sessions": [{"id": "room-1", "name": "Sprint 42", "mode": "poker", "players": 3}],
        "notes": [{"author": "alice", "column": "went well", "text": "shipped"}],
    }


def summary() -> dict:
    state = _state()
    return {
        "stats": {
            "sessions": len(state["sessions"]),
            "players": sum(s["players"] for s in state["sessions"]),
            "stories": 2,
            "votes": 3,
        },
        "lists": {
            "sessions": state["sessions"],
            "notes": state["notes"],
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/summary":
        return 200, summary()
    return 404, {"error": "not found"}
