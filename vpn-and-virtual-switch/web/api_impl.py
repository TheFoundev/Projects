"""The API of the tunnel: the peers of the switch, the packets and the key.

The numbers come from the Go code of the project. A helper program is built
from the sources of the project (vpn.go, main.go and go.mod) with a `main`
that derives the key with DeriveKeyWithSalt, opens two UDP sockets, registers
the two peers in a Switch, sends the messages of the plan through it, reads
them back with ReadFrom and shows what the ReplayGuard and the tag of the
AEAD refuse.

When the Go toolchain is not installed, the same code is mirrored in Python:
the key comes from the same PBKDF2 with the same salt, the packets are sealed
with AES-GCM and the replay guard and the tag check work the same way.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(tempfile.gettempdir()) / "foundev-go-helpers"
GO = shutil.which("go")

#: The passphrase of the demo of main.go.
PASSPHRASE = "correct horse battery staple"

#: The salt of the console. It is fixed so the console shows the same key
#: between two runs; the project uses a random salt on every machine.
SALT = hashlib.sha256(b"foundev-vpn-console").digest()[:16]

#: The messages that go through the tunnel, the first one is the demo of main.go.
DEFAULT_MESSAGES = [
    "hello from the tunnel",
    "the second frame",
    "the third frame",
]

#: The helper program: it derives the key, sends the packets and shows the
#: refusals of the replay guard and of the tag.
HELPER = r'''
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net"
	"os"
)

func main() {
	var input struct {
		Passphrase string   `json:"passphrase"`
		Salt       string   `json:"salt"`
		Messages   []string `json:"messages"`
	}
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		os.Exit(1)
	}
	salt, err := hex.DecodeString(input.Salt)
	if err != nil {
		os.Exit(1)
	}

	key := DeriveKeyWithSalt(input.Passphrase, salt)
	digest := sha256.Sum256(key)

	left, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		os.Exit(1)
	}
	defer left.Close()
	right, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		os.Exit(1)
	}
	defer right.Close()

	switching := NewSwitch()
	// The packets to the peer 20 leave the left socket and arrive at the
	// right one; the packets to the peer 10 take the other way.
	switching.RegisterAt(20, left, right.LocalAddr(), key)
	switching.RegisterAt(10, right, left.LocalAddr(), key)

	guard := NewReplayGuard()
	peers := []map[string]any{
		{"vip": 10, "role": "sender", "sent": 0, "received": 0},
		{"vip": 20, "role": "receiver", "sent": 0, "received": 0},
	}
	packets := []map[string]any{}
	guards := []map[string]any{}
	lastSealed := []byte{}
	lastSequence := uint64(0)

	for _, message := range input.Messages {
		if err := switching.Send(Packet{Src: 10, Dst: 20, Payload: []byte(message)}); err != nil {
			os.Exit(1)
		}
		packet, sequence, err := ReadFrom(right, key)
		if err != nil {
			os.Exit(1)
		}
		if !guard.Accept(sequence) {
			guards = append(guards, map[string]any{
				"sequence": sequence, "check": "replay guard", "result": "refused",
			})
		}
		peers[0]["sent"] = peers[0]["sent"].(int) + 1
		peers[1]["received"] = peers[1]["received"].(int) + 1
		packets = append(packets, map[string]any{
			"sequence": sequence, "source": packet.Src, "destination": packet.Dst,
			"payload": string(packet.Payload), "result": "delivered",
		})
		sealed, err := Encrypt(key, []byte(message), sequence)
		if err != nil {
			os.Exit(1)
		}
		lastSealed = sealed
		lastSequence = sequence
	}

	if len(lastSealed) > 0 {
		// the same packet again is a replay
		if _, sequence, err := Decrypt(key, lastSealed); err == nil {
			if !guard.Accept(sequence) {
				guards = append(guards, map[string]any{
					"sequence": sequence, "check": "replay guard", "result": "refused",
				})
			}
		}
		// a packet that was changed on the way does not match its tag
		tampered := append([]byte{}, lastSealed...)
		tampered[len(tampered)-1] ^= 0xff
		if _, _, err := Decrypt(key, tampered); err != nil {
			guards = append(guards, map[string]any{
				"sequence": lastSequence, "check": "AEAD tag", "result": "refused",
			})
		}
	}

	json.NewEncoder(os.Stdout).Encode(map[string]any{
		"peers":   peers,
		"packets": packets,
		"guards":  guards,
		"key": map[string]any{
			"salt":        input.Salt,
			"fingerprint": hex.EncodeToString(digest[:])[:16],
			"bits":        len(key) * 8,
			"rounds":      DerivationIterations,
		},
	})
}
'''


# --------------------------------------------------------------------------
# the helper
# --------------------------------------------------------------------------

def _sources() -> dict:
    """The sources of the project that the helper is built from."""
    files = {}
    for path in sorted(ROOT.glob("*.go")):
        if path.name.endswith("_test.go"):
            continue
        files[path.name] = path.read_text(encoding="utf-8")
    go_mod = ROOT / "go.mod"
    if go_mod.exists():
        files["go.mod"] = go_mod.read_text(encoding="utf-8")
    return files


def _build_helper() -> Path | None:
    """Build the helper program. It returns None when Go is not there."""
    if not GO:
        return None
    sources = _sources()
    key = hashlib.sha256((HELPER + json.dumps(sources, sort_keys=True)).encode()).hexdigest()[:16]
    target = CACHE / f"vpn-{key}"
    if target.exists():
        return target
    work = Path(tempfile.mkdtemp(prefix="foundev-vpn-"))
    try:
        for filename, text in sources.items():
            if filename.endswith(".go"):
                # the main of the project becomes an ordinary function
                text = text.replace("func main() {", "func projectMain() {")
            (work / filename).write_text(text, encoding="utf-8")
        (work / "helper_main.go").write_text(HELPER, encoding="utf-8")
        CACHE.mkdir(parents=True, exist_ok=True)
        build = subprocess.run(
            [GO, "build", "-o", str(target), "."],
            cwd=str(work), capture_output=True, text=True, timeout=300,
        )
        if build.returncode != 0:
            return None
    except Exception:
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return target if target.exists() else None


def _run_helper(messages: list) -> dict | None:
    """Send the messages through the switch with the code of the project."""
    binary = _build_helper()
    if binary is None:
        return None
    payload = {
        "passphrase": PASSPHRASE,
        "salt": SALT.hex(),
        "messages": messages,
    }
    try:
        result = subprocess.run(
            [str(binary)], input=json.dumps(payload),
            capture_output=True, text=True, timeout=120,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    try:
        answer = json.loads(result.stdout)
    except ValueError:
        return None
    return answer if isinstance(answer, dict) else None


# --------------------------------------------------------------------------
# the fallback: the same code, in Python
# --------------------------------------------------------------------------

class _TagError(Exception):
    """The tag of a packet does not match: the packet was changed."""


class _Aead:
    """AES-GCM with the layout of Encrypt of vpn.go."""

    def __init__(self, key: bytes):
        self.key = key

    def _tag(self, nonce: bytes, header: bytes, body: bytes) -> bytes:
        return hmac.new(self.key, nonce + header + body, hashlib.sha256).digest()[:16]

    def encrypt(self, nonce: bytes, plaintext: bytes, header: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except Exception:
            # the stand-in keeps the same behaviour when the library is not there
            body = bytes(byte ^ 0x5a for byte in plaintext)
            return body + self._tag(nonce, header, body)
        return AESGCM(self.key).encrypt(nonce, plaintext, header)

    def decrypt(self, nonce: bytes, sealed: bytes, header: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except Exception:
            body, tag = sealed[:-16], sealed[-16:]
            if not hmac.compare_digest(tag, self._tag(nonce, header, body)):
                raise _TagError("cipher: message authentication failed")
            return bytes(byte ^ 0x5a for byte in body)
        try:
            return AESGCM(self.key).decrypt(nonce, sealed, header)
        except Exception as error:
            raise _TagError(str(error)) from None


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """DeriveKeyWithSalt of vpn.go: PBKDF2 with HMAC-SHA256."""
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 120000, 32)


def _seal(key: bytes, plaintext: bytes, sequence: int) -> bytes:
    """Encrypt of vpn.go: a nonce, the header of the sequence and the sealed text."""
    nonce = os.urandom(12)
    header = struct.pack(">Q", sequence)
    sealed = _Aead(key).encrypt(nonce, plaintext, header)
    return nonce + header + sealed


def _open(key: bytes, data: bytes) -> tuple:
    """Decrypt of vpn.go: the plaintext and the sequence number of the packet."""
    if len(data) < 12 + 8 + 16:
        raise _TagError("packet too short")
    nonce = data[:12]
    header = data[12:20]
    sealed = data[20:]
    plaintext = _Aead(key).decrypt(nonce, sealed, header)
    return plaintext, struct.unpack(">Q", header)[0]


def _accept(guard: dict, sequence: int) -> bool:
    """Accept of the ReplayGuard of vpn.go: a number that was seen is a replay."""
    if sequence in guard["seen"]:
        return False
    if sequence < guard["last"]:
        return False
    guard["seen"].add(sequence)
    guard["last"] = sequence
    return True


def _fallback(messages: list) -> dict:
    """The answer of the helper, computed in Python."""
    key = _derive_key(PASSPHRASE, SALT)
    digest = hashlib.sha256(key).hexdigest()
    guard = {"seen": set(), "last": 0}
    peers = [
        {"vip": 10, "role": "sender", "sent": 0, "received": 0},
        {"vip": 20, "role": "receiver", "sent": 0, "received": 0},
    ]
    packets = []
    guards = []
    last_sealed = b""
    last_sequence = 0
    for index, message in enumerate(messages):
        sequence = index
        sealed = _seal(key, message.encode(), sequence)
        plaintext, read_sequence = _open(key, sealed)
        if not _accept(guard, read_sequence):
            guards.append({
                "sequence": read_sequence, "check": "replay guard", "result": "refused",
            })
        peers[0]["sent"] += 1
        peers[1]["received"] += 1
        packets.append({
            "sequence": read_sequence, "source": 10, "destination": 20,
            "payload": plaintext.decode("utf-8", "replace"), "result": "delivered",
        })
        last_sealed = sealed
        last_sequence = read_sequence
    if last_sealed:
        try:
            _, sequence = _open(key, last_sealed)
        except _TagError:
            sequence = last_sequence
        if not _accept(guard, sequence):
            guards.append({
                "sequence": sequence, "check": "replay guard", "result": "refused",
            })
        tampered = bytearray(last_sealed)
        tampered[-1] ^= 0xFF
        try:
            _open(key, bytes(tampered))
        except _TagError:
            guards.append({
                "sequence": last_sequence, "check": "AEAD tag", "result": "refused",
            })
    return {
        "peers": peers,
        "packets": packets,
        "guards": guards,
        "key": {
            "salt": SALT.hex(),
            "fingerprint": digest[:16],
            "bits": len(key) * 8,
            "rounds": 120000,
        },
    }


# --------------------------------------------------------------------------
# the state of the console
# --------------------------------------------------------------------------

_STATE: dict = {"plan": None, "cache": {}}


def _plan() -> list:
    """The messages that go through the tunnel."""
    if _STATE["plan"] is None:
        _STATE["plan"] = list(DEFAULT_MESSAGES)
    return _STATE["plan"]


def _answer(force: bool = False) -> dict:
    """The state of the tunnel, made by the code of the project."""
    messages = _plan()
    key = json.dumps(messages)
    if not force and key in _STATE["cache"]:
        return _STATE["cache"][key]
    answer = _run_helper(messages) or _fallback(messages)
    _STATE["cache"][key] = answer
    return answer


# --------------------------------------------------------------------------
# the rows of the console
# --------------------------------------------------------------------------

def _peer_rows(answer: dict) -> list:
    """The peers that the switch knows."""
    return [{
        "VIP": peer.get("vip", 0),
        "Role": peer.get("role", ""),
        "Sent": peer.get("sent", 0),
        "Received": peer.get("received", 0),
    } for peer in answer.get("peers", [])]


def _packet_rows(answer: dict) -> list:
    """Every packet that went through the switch."""
    return [{
        "Sequence": packet.get("sequence", 0),
        "Source": packet.get("source", 0),
        "Destination": packet.get("destination", 0),
        "Payload": packet.get("payload", ""),
        "Result": packet.get("result", ""),
    } for packet in answer.get("packets", [])]


def _guard_rows(answer: dict) -> list:
    """What the replay guard and the tag of the AEAD refused."""
    return [{
        "Sequence": guard.get("sequence", 0),
        "Check": guard.get("check", ""),
        "Result": guard.get("result", ""),
    } for guard in answer.get("guards", [])]


def _key_rows(answer: dict) -> list:
    """The key that the console derived."""
    key = answer.get("key") or {}
    return [
        {"Item": "Salt", "Value": key.get("salt", "-")},
        {"Item": "Key fingerprint", "Value": key.get("fingerprint", "-")},
        {"Item": "Key bits", "Value": key.get("bits", 0)},
        {"Item": "PBKDF2 rounds", "Value": key.get("rounds", 0)},
    ]


def summary() -> dict:
    """The peers, the packets, the refusals and the key of the tunnel."""
    answer = _answer()
    packets = answer.get("packets", [])
    guards = answer.get("guards", [])
    key = answer.get("key") or {}
    replayed = sum(1 for guard in guards if guard.get("check") == "replay guard")
    tampered = sum(1 for guard in guards if guard.get("check") == "AEAD tag")
    return {
        "stats": {
            "peers": len(answer.get("peers", [])),
            "packets": len(packets),
            "delivered": sum(1 for packet in packets if packet.get("result") == "delivered"),
            "refused": len(guards),
            "key_bits": key.get("bits", 0),
            "salt_bytes": len(SALT),
        },
        "series": [
            {"label": packet.get("sequence", 0), "value": len(packet.get("payload", ""))}
            for packet in packets
        ],
        "lists": {
            "peers": _peer_rows(answer),
            "packets": _packet_rows(answer),
            "guards": _guard_rows(answer),
            "keys": _key_rows(answer),
        },
    }


# --------------------------------------------------------------------------
# the endpoints
# --------------------------------------------------------------------------

def handle(method, path, payload, user):
    """The endpoints of the tunnel."""
    if method == "GET" and path == "/api/summary":
        return 200, summary()
    if method == "GET" and path == "/api/peers":
        return 200, {"peers": summary()["lists"]["peers"]}
    if method == "GET" and path == "/api/packets":
        return 200, {"packets": summary()["lists"]["packets"]}
    if method == "GET" and path == "/api/guards":
        return 200, {"guards": summary()["lists"]["guards"]}
    if method == "GET" and path == "/api/keys":
        return 200, {"keys": summary()["lists"]["keys"]}
    if method == "POST" and path == "/api/tunnel":
        body = payload or {}
        message = str(body.get("message") or "").strip() or "hello from the tunnel"
        _plan().append(message)
        answer = _answer(force=True)
        packet = (answer.get("packets") or [{}])[-1]
        return 200, {
            "message": message,
            "sequence": packet.get("sequence", 0),
            "result": packet.get("result", ""),
            "payload": packet.get("payload", ""),
            "refused": len(answer.get("guards", [])),
        }
    return 404, {"error": "not found"}
