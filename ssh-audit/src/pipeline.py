"""SSH banner/KEXINIT audit against a local fake server."""
import json
import socket
import struct
import threading
from pathlib import Path

WEAK = {
    "diffie-hellman-group1-sha1", "diffie-hellman-group14-sha1", "ssh-dss",
    "3des-cbc", "arcfour", "arcfour128", "hmac-md5", "hmac-md5-96",
    "hmac-sha1-96", "blowfish-cbc", "cast128-cbc",
}


def encode_string(value: str) -> bytes:
    raw = value.encode()
    return struct.pack(">I", len(raw)) + raw


def build_kexinit(kex, host_keys, ciphers, macs):
    cookie = b"0123456789abcdef"
    payload = bytes([20]) + cookie
    for group in (kex, host_keys, ciphers, ciphers, macs, macs, ["none"], ["none"], [], []):
        payload += encode_string(",".join(group))
    payload += b"\x00" + struct.pack(">I", 0)  # first_kex_packet_follows + reserved
    padding_length = 8 - ((len(payload) + 5) % 8)
    if padding_length < 4:
        padding_length += 8
    packet = struct.pack(">I", len(payload) + padding_length + 1) + bytes([padding_length]) + payload
    packet += b"\x00" * padding_length
    return packet


def make_server(good=True):
    # A good server offers the modern key exchange only. The old
    # diffie-hellman-group14-sha1 is on the weak list, so it may not be in
    # the good one.
    weak_kex = ["curve25519-sha256", "sntrup761x25519-sha512@openssh.com"] if good else ["diffie-hellman-group1-sha1"]
    ciphers = ["aes128-gcm@openssh.com"] if good else ["3des-cbc", "aes128-cbc"]
    macs = ["hmac-sha2-256"] if good else ["hmac-md5"]

    def serve(ready):
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        ready.append(server.getsockname()[1])
        connection, _ = server.accept()
        with connection:
            connection.sendall(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5\r\n")
            connection.sendall(build_kexinit(weak_kex, ["rsa-sha2-512", "ssh-rsa"], ciphers, macs))
        server.close()

    return serve


def read_packet(stream):
    header = stream.read(4)
    if len(header) < 4:
        return b""
    length = struct.unpack(">I", header)[0]
    body = stream.read(length)
    padding_length = body[0]
    return body[1:len(body) - padding_length]


def read_string(payload, offset):
    size = struct.unpack(">I", payload[offset:offset + 4])[0]
    start = offset + 4
    return payload[start:start + size].decode(errors="replace"), start + size


def parse_kexinit(payload):
    offset = 17  # message type + 16-byte cookie
    names = ["kex", "host_keys", "enc_c2s", "enc_s2c", "mac_c2s", "mac_s2c"]
    result = {}
    for name in names:
        value, offset = read_string(payload, offset)
        result[name] = value.split(",")
    return result


def audit(port):
    with socket.create_connection(("127.0.0.1", port), timeout=3) as client:
        client.settimeout(3)
        stream = client.makefile("rb")
        banner = stream.readline(256).decode(errors="replace").strip()
        payload = read_packet(stream)
    algorithms = parse_kexinit(payload)
    findings = []
    for name, values in algorithms.items():
        for value in values:
            if value in WEAK:
                findings.append({"group": name, "algorithm": value})
    score = max(0, 100 - 20 * len(findings))
    grade = "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D"
    return banner, algorithms, findings, score, grade


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    ready = []
    thread = threading.Thread(target=make_server(good=not quick), args=(ready,), daemon=True)
    thread.start()
    for _ in range(50):
        if ready:
            break
        threading.Event().wait(0.05)
    banner, algorithms, findings, score, grade = audit(ready[0])
    thread.join(timeout=2)

    report = {
        "banner": banner,
        "server": banner.split("-")[-1] if "-" in banner else banner,
        "algorithms": algorithms,
        "findings": findings,
        "score": score,
        "grade": grade,
    }
    (base / "ssh_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "banner": banner,
        "groups": len(algorithms),
        "weak_findings": len(findings),
        "score": score,
        "grade": grade,
        "report": str(base / "ssh_audit.json"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    report = json.loads((Path(base_dir) / "ssh_audit.json").read_text())
    print(f"Banner: {report['banner']}")
    for group, values in report["algorithms"].items():
        print(f"  {group:9s} {', '.join(values)}")
    print(f"Score: {summary['score']} ({summary['grade']}), weak findings: {summary['weak_findings']}")
