package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	commonName := flag.String("cn", "service.internal", "leaf common name")
	output := flag.String("out", "artifacts", "output directory")
	flag.Parse()

	authority, err := NewAuthority("Foundev Student CA")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	leaf, err := authority.Issue(*commonName, []string{*commonName, "localhost"})
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := authority.Verify(leaf.Certificate); err != nil {
		fmt.Fprintln(os.Stderr, "verification failed:", err)
		os.Exit(1)
	}
	if err := authority.Save(*output, leaf); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("issued %s valid until %s\n", leaf.Certificate.Subject.CommonName, leaf.Certificate.NotAfter.Format("2006-01-02"))
}
