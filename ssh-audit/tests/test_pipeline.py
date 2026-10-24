"""Tests for the SSH audit."""
import socket
import threading

from src.pipeline import (
    audit,
    build_kexinit,
    demo,
    encode_string,
    make_server,
    parse_kexinit,
    read_string,
    run,
)


def _start(serve):
    """Start the fake server and give back the port it listens on."""
    ready = []
    thread = threading.Thread(target=serve, args=(ready,), daemon=True)
    thread.start()
    while not ready:
        pass
    return ready[0], thread


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_a_string_is_encoded_with_its_length():
    encoded = encode_string("abc")
    assert len(encoded) == 7
    assert encoded[:4] == b"\x00\x00\x00\x03"
    assert encoded[4:] == b"abc"


def test_a_string_is_read_at_its_offset():
    """The string is read and the offset behind it is given back."""
    payload = b"\x00\x00\x00\x03abc"
    value, offset = read_string(payload, 0)
    assert value == "abc"
    assert offset == 7


def test_the_kexinit_is_parsed():
    packet = build_kexinit(
        ["diffie-hellman-group14-sha256"], ["ssh-rsa"], ["aes128-ctr"], ["hmac-sha2-256"]
    )
    # The packet starts with its length and the padding length; the parser
    # works on the message behind them.
    parsed = parse_kexinit(packet[5:])

    assert parsed["kex"]
    assert "diffie-hellman-group14-sha256" in parsed["kex"]
    assert "aes128-ctr" in parsed["enc_c2s"]
    assert "hmac-sha2-256" in parsed["mac_c2s"]


def test_the_audit_of_a_good_server_finds_nothing():
    port, thread = _start(make_server(good=True))
    try:
        banner, _algorithms, findings, _score, grade = audit(port)
        assert banner.startswith("SSH-2.0")
        assert findings == []
        assert grade == "A"
    finally:
        thread.join(timeout=2)


def test_the_audit_of_a_weak_server_finds_the_weak_algorithms():
    port, thread = _start(make_server(good=False))
    try:
        _banner, _algorithms, findings, _score, grade = audit(port)
        assert findings
        assert grade in ("C", "D")
    finally:
        thread.join(timeout=2)
