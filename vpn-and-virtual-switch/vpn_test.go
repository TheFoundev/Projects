package main

import (
	"bytes"
	"net"
	"testing"
)

func TestTheKeyIsDerivedWithASalt(t *testing.T) {
	// The same passphrase with two salts gives two keys, so a dictionary of
	// passphrases does not help against a stored key.
	salt := NewSalt()
	first := DeriveKeyWithSalt("secret", salt)
	second := DeriveKeyWithSalt("secret", salt)
	if !bytes.Equal(first, second) {
		t.Fatal("the same salt has to give the same key")
	}
	other := DeriveKeyWithSalt("secret", NewSalt())
	if bytes.Equal(first, other) {
		t.Fatal("another salt has to give another key")
	}
	if len(first) != 32 {
		t.Fatalf("unexpected key length %d", len(first))
	}
}

func TestThePacketCarriesItsSequenceNumber(t *testing.T) {
	key := DeriveKey("secret")
	sealed, err := Encrypt(key, []byte("payload"), 42)
	if err != nil {
		t.Fatal(err)
	}
	_, sequence, err := Decrypt(key, sealed)
	if err != nil {
		t.Fatal(err)
	}
	if sequence != 42 {
		t.Fatalf("unexpected sequence %d", sequence)
	}
}

func TestAPacketThatIsTamperedWithIsRefused(t *testing.T) {
	key := DeriveKey("secret")
	sealed, err := Encrypt(key, []byte("payload"), 1)
	if err != nil {
		t.Fatal(err)
	}
	tampered := append([]byte{}, sealed...)
	tampered[len(tampered)-1] ^= 0xff
	if _, _, err := Decrypt(key, tampered); err == nil {
		t.Fatal("a tampered packet should be refused")
	}
}

func TestAReplayIsRefused(t *testing.T) {
	guard := NewReplayGuard()
	if !guard.Accept(1) {
		t.Fatal("the first packet is new")
	}
	if guard.Accept(1) {
		t.Fatal("the same packet again is a replay")
	}
	if !guard.Accept(2) {
		t.Fatal("the next packet is new")
	}
	if guard.Accept(1) {
		t.Fatal("an older packet is refused")
	}
}

func TestEncryptRoundTrip(t *testing.T) {
	key := DeriveKey("secret")
	sealed, err := Encrypt(key, []byte("payload"), 1)
	if err != nil {
		t.Fatal(err)
	}
	plaintext, _, err := Decrypt(key, sealed)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(plaintext, []byte("payload")) {
		t.Fatalf("got %q", plaintext)
	}
	if _, _, err := Decrypt(DeriveKey("other"), sealed); err == nil {
		t.Fatal("wrong key should fail")
	}
}

func TestSwitchForwards(t *testing.T) {
	key := DeriveKey("secret")
	left, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer left.Close()
	right, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer right.Close()

	switching := NewSwitch()
	// The packets to peer one go out of the left socket, the packets to peer
	// two out of the right one.
	switching.RegisterAt(1, left, left.LocalAddr(), key)
	switching.RegisterAt(2, right, right.LocalAddr(), key)
	if err := switching.Send(Packet{Src: 1, Dst: 2, Payload: []byte("frame")}); err != nil {
		t.Fatal(err)
	}
	packet, _, err := ReadFrom(right, key)
	if err != nil {
		t.Fatal(err)
	}
	if packet.Src != 1 || string(packet.Payload) != "frame" {
		t.Fatalf("unexpected packet %#v", packet)
	}
	if err := switching.Send(Packet{Dst: 99}); err == nil {
		t.Fatal("expected a missing route error")
	}
}
