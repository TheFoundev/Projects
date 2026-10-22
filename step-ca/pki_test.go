package main

import "testing"

func TestIssueAndVerify(t *testing.T) {
	authority, err := NewAuthority("Test CA")
	if err != nil {
		t.Fatal(err)
	}
	if !authority.Certificate.IsCA {
		t.Fatal("authority should be a CA")
	}
	leaf, err := authority.Issue("api.internal", []string{"api.internal", "localhost"})
	if err != nil {
		t.Fatal(err)
	}
	if err := authority.Verify(leaf.Certificate); err != nil {
		t.Fatalf("verify failed: %v", err)
	}
	if leaf.Certificate.Subject.CommonName != "api.internal" {
		t.Fatalf("unexpected common name %s", leaf.Certificate.Subject.CommonName)
	}
	if len(leaf.Certificate.DNSNames) != 2 {
		t.Fatalf("unexpected SANs %v", leaf.Certificate.DNSNames)
	}
}

func TestSerialNumbersDiffer(t *testing.T) {
	authority, _ := NewAuthority("Test CA")
	first, _ := authority.Issue("a.internal", nil)
	second, _ := authority.Issue("b.internal", nil)
	if first.Certificate.SerialNumber.Cmp(second.Certificate.SerialNumber) == 0 {
		t.Fatal("serial numbers should differ")
	}
}
