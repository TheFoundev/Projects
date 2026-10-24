package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"errors"
	"net"
	"sync"
)

// The parameters of the key derivation.
const (
	// SaltSize is the length of the salt.
	SaltSize = 16
	// DerivationIterations is how often the passphrase is hashed.
	DerivationIterations = 120000
)

// Packet is one tunnelled frame.
type Packet struct {
	Src     uint32
	Dst     uint32
	Payload []byte
}

// DeriveKey turns a passphrase into a 32-byte AES key.
//
// The key is derived with PBKDF2 and a random salt, so the same passphrase
// gives a different key on every machine and a dictionary of passphrases does
// not help against the stored key.
func DeriveKey(secret string) []byte {
	return DeriveKeyWithSalt(secret, NewSalt())
}

// NewSalt returns a new random salt.
func NewSalt() []byte {
	salt := make([]byte, SaltSize)
	if _, err := rand.Read(salt); err != nil {
		return make([]byte, SaltSize)
	}
	return salt
}

// DeriveKeyWithSalt turns a passphrase and a salt into a 32-byte AES key.
func DeriveKeyWithSalt(secret string, salt []byte) []byte {
	return pbkdf2Key([]byte(secret), salt, DerivationIterations, 32)
}

// pbkdf2Key is PBKDF2 with HMAC-SHA256.
func pbkdf2Key(password, salt []byte, iterations, length int) []byte {
	blocks := (length + 31) / 32
	result := make([]byte, 0, blocks*32)
	for block := 1; block <= blocks; block++ {
		mac := hmac.New(sha256.New, password)
		mac.Write(salt)
		mac.Write([]byte{byte(block >> 24), byte(block >> 16), byte(block >> 8), byte(block)})
		current := mac.Sum(nil)
		result = append(result, current...)
		for round := 1; round < iterations; round++ {
			mac.Reset()
			mac.Write(current)
			current = mac.Sum(nil)
			for index := range current {
				result[(block-1)*32+index] ^= current[index]
			}
		}
	}
	return result[:length]
}

// Encrypt seals a plaintext with AES-GCM and a random nonce.
//
// The nonce is written in front of the sealed text, and the sequence number
// is added to the data that is authenticated, so a packet cannot be replayed.
func Encrypt(key, plaintext []byte, sequence uint64) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	nonce := make([]byte, aead.NonceSize())
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}

	header := make([]byte, 8)
	binary.BigEndian.PutUint64(header, sequence)

	sealed := aead.Seal(nil, nonce, plaintext, header)
	return append(append(nonce, header...), sealed...), nil
}

// Decrypt opens a sealed buffer and says which sequence number it had.
//
// The sequence number is given back so the caller can check that the packet
// is newer than the last one it accepted.
func Decrypt(key, data []byte) ([]byte, uint64, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, 0, err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return nil, 0, err
	}
	if len(data) < aead.NonceSize()+8+aead.Overhead() {
		return nil, 0, errors.New("packet too short")
	}
	nonce := data[:aead.NonceSize()]
	header := data[aead.NonceSize() : aead.NonceSize()+8]
	sealed := data[aead.NonceSize()+8:]

	plaintext, err := aead.Open(nil, nonce, sealed, header)
	if err != nil {
		return nil, 0, err
	}
	return plaintext, binary.BigEndian.Uint64(header), nil
}

// ReplayGuard tells whether a packet is new.
type ReplayGuard struct {
	mu       sync.Mutex
	sequence uint64
	seen     map[uint64]bool
}

// NewReplayGuard creates a guard that remembers the packets it has seen.
func NewReplayGuard() *ReplayGuard {
	return &ReplayGuard{seen: map[uint64]bool{}}
}

// Accept says whether the sequence number is new.
//
// A number that was seen before is a replay and is refused, and a number that
// is older than the last one is refused as well.
func (guard *ReplayGuard) Accept(sequence uint64) bool {
	guard.mu.Lock()
	defer guard.mu.Unlock()

	if guard.seen[sequence] {
		return false
	}
	if sequence < guard.sequence {
		return false
	}
	guard.seen[sequence] = true
	guard.sequence = sequence
	return true
}

func encode(packet Packet) []byte {
	header := make([]byte, 8)
	binary.BigEndian.PutUint32(header[0:4], packet.Src)
	binary.BigEndian.PutUint32(header[4:8], packet.Dst)
	return append(header, packet.Payload...)
}

func decode(data []byte) (Packet, error) {
	if len(data) < 8 {
		return Packet{}, errors.New("missing header")
	}
	return Packet{
		Src:     binary.BigEndian.Uint32(data[0:4]),
		Dst:     binary.BigEndian.Uint32(data[4:8]),
		Payload: data[8:],
	}, nil
}

// Switch routes the packets between the peers.
type Switch struct {
	mu        sync.Mutex
	peers     map[uint32]net.PacketConn
	addresses map[uint32]net.Addr
	keys      map[uint32][]byte
	sequence  uint64
}

// NewSwitch creates an empty switch.
func NewSwitch() *Switch {
	return &Switch{
		peers:     map[uint32]net.PacketConn{},
		addresses: map[uint32]net.Addr{},
		keys:      map[uint32][]byte{},
	}
}

// Register adds a peer to the switch.
func (switching *Switch) Register(vip uint32, conn net.PacketConn, key []byte) {
	switching.RegisterAt(vip, conn, nil, key)
}

// RegisterAt adds a peer.
//
// The connection is the local socket the packets to this peer go out of, and
// the address is the address of the peer itself.
func (switching *Switch) RegisterAt(vip uint32, conn net.PacketConn, addr net.Addr, key []byte) {
	switching.mu.Lock()
	defer switching.mu.Unlock()
	switching.peers[vip] = conn
	switching.addresses[vip] = addr
	switching.keys[vip] = key
}

// Send encrypts a packet and sends it to the peer.
func (switching *Switch) Send(packet Packet) error {
	switching.mu.Lock()
	key, ok := switching.keys[packet.Dst]
	sequence := switching.sequence
	switching.sequence++
	switching.mu.Unlock()

	if !ok {
		return errors.New("the peer is not known")
	}

	sealed, err := Encrypt(key, encode(packet), sequence)
	if err != nil {
		return err
	}
	conn := switching.peers[packet.Dst]
	if conn == nil {
		return errors.New("the peer is not connected")
	}
	address := switching.addresses[packet.Dst]
	if address == nil {
		return errors.New("the address of the peer is not known")
	}
	_, err = conn.WriteTo(sealed, address)
	return err
}

// ReadFrom reads a packet from a connection and opens it.
func ReadFrom(conn net.PacketConn, key []byte) (Packet, uint64, error) {
	buffer := make([]byte, 4096)
	count, _, err := conn.ReadFrom(buffer)
	if err != nil {
		return Packet{}, 0, err
	}
	plaintext, sequence, err := Decrypt(key, buffer[:count])
	if err != nil {
		return Packet{}, 0, err
	}
	packet, err := decode(plaintext)
	return packet, sequence, err
}
