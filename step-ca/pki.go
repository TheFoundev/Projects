package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Leaf bundles an issued certificate and its private key.
type Leaf struct {
	Certificate *x509.Certificate
	PrivateKey  *ecdsa.PrivateKey
}

// Authority is a simple root CA.
type Authority struct {
	Name        string
	Certificate *x509.Certificate
	PrivateKey  *ecdsa.PrivateKey
	// Names are the names the authority may sign for. A signing request
	// for anything else is refused.
	Names []string
}

func serial() (*big.Int, error) {
	limit := new(big.Int).Lsh(big.NewInt(1), 128)
	return rand.Int(rand.Reader, limit)
}

// NewAuthority creates a self-signed root with an ECDSA key.
func NewAuthority(name string, names ...string) (*Authority, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, err
	}
	number, err := serial()
	if err != nil {
		return nil, err
	}
	template := &x509.Certificate{
		SerialNumber:          number,
		Subject:               pkix.Name{CommonName: name, Organization: []string{"Foundev Student Projects"}},
		NotBefore:             time.Now().Add(-time.Hour),
		NotAfter:              time.Now().AddDate(5, 0, 0),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
		BasicConstraintsValid: true,
		IsCA:                  true,
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return nil, err
	}
	certificate, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, err
	}
	if len(names) == 0 {
		names = []string{name}
	}
	return &Authority{Name: name, Certificate: certificate, PrivateKey: key, Names: names}, nil
}

// Issue creates a leaf certificate for a common name and SAN list.
// IssueCSR signs a certificate signing request.
//
// The request has to be checked: the name of the request has to be one the
// authority is allowed to sign, and the request has to be signed with a key
// the authority knows.
func (authority *Authority) IssueCSR(csrPEM []byte) (*Leaf, error) {
	block, _ := pem.Decode(csrPEM)
	if block == nil || block.Type != "CERTIFICATE REQUEST" {
		return nil, fmt.Errorf("the certificate signing request could not be read")
	}
	request, err := x509.ParseCertificateRequest(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("the certificate signing request is broken: %w", err)
	}
	if err := request.CheckSignature(); err != nil {
		return nil, fmt.Errorf("the certificate signing request is not signed: %w", err)
	}

	name := request.Subject.CommonName
	if !authority.maySign(name) {
		return nil, fmt.Errorf("the authority may not sign for %q", name)
	}

	hosts := request.DNSNames
	number, err := serial()
	if err != nil {
		return nil, err
	}
	template := &x509.Certificate{
		SerialNumber: number,
		Subject:      request.Subject,
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(365 * 24 * time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		DNSNames:     hosts,
	}
	if len(template.DNSNames) == 0 && request.IPAddresses != nil {
		template.IPAddresses = request.IPAddresses
	}

	der, err := x509.CreateCertificate(rand.Reader, template, authority.Certificate, request.PublicKey, authority.PrivateKey)
	if err != nil {
		return nil, err
	}
	leaf, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, err
	}
	return &Leaf{
		Certificate: leaf,
	}, nil
}

// maySign says whether the authority may sign for a name.
//
// The names of the authority are the ones it was made for.
func (authority *Authority) maySign(commonName string) bool {
	if commonName == "" {
		return false
	}
	for _, allowed := range authority.Names {
		if allowed == commonName || strings.HasSuffix(commonName, "."+allowed) {
			return true
		}
	}
	return false
}

func (authority *Authority) Issue(commonName string, hosts []string) (*Leaf, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, err
	}
	number, err := serial()
	if err != nil {
		return nil, err
	}
	template := &x509.Certificate{
		SerialNumber: number,
		Subject:      pkix.Name{CommonName: commonName},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().AddDate(1, 0, 0),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth, x509.ExtKeyUsageClientAuth},
		DNSNames:     hosts,
	}
	der, err := x509.CreateCertificate(rand.Reader, template, authority.Certificate, &key.PublicKey, authority.PrivateKey)
	if err != nil {
		return nil, err
	}
	certificate, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, err
	}
	return &Leaf{Certificate: certificate, PrivateKey: key}, nil
}

// Verify checks the leaf chain against the root pool.
func (authority *Authority) Verify(certificate *x509.Certificate) error {
	pool := x509.NewCertPool()
	pool.AddCert(authority.Certificate)
	_, err := certificate.Verify(x509.VerifyOptions{Roots: pool, KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}})
	return err
}

func encodeKey(key *ecdsa.PrivateKey) ([]byte, error) {
	der, err := x509.MarshalECPrivateKey(key)
	if err != nil {
		return nil, err
	}
	return pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: der}), nil
}

// Save writes the CA and leaf material to a directory.
func (authority *Authority) Save(directory string, leaf *Leaf) error {
	if err := os.MkdirAll(directory, 0o755); err != nil {
		return err
	}
	if err := writePEM(filepath.Join(directory, "ca.crt"), "CERTIFICATE", authority.Certificate.Raw); err != nil {
		return err
	}
	if err := writePEM(filepath.Join(directory, "leaf.crt"), "CERTIFICATE", leaf.Certificate.Raw); err != nil {
		return err
	}
	keyPEM, err := encodeKey(leaf.PrivateKey)
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(directory, "leaf.key"), keyPEM, 0o600)
}

func writePEM(path, blockType string, der []byte) error {
	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()
	if err := pem.Encode(file, &pem.Block{Type: blockType, Bytes: der}); err != nil {
		return fmt.Errorf("encode %s: %w", path, err)
	}
	return nil
}
