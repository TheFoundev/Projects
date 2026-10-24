# step-ca

A tiny certificate authority that issues and verifies leaf certificates.

> A private certificate authority and ACME server for issuing short-lived certificates inside a zero-trust network.

## Overview

An original, self-contained implementation of the **step-ca** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- ECDSA root and intermediate certificates
- CSR based leaf issuance with SAN and validity
- Certificate chain verification
- PEM files for the CA and issued certificate

## Stack

`Go`
The CSV stack is Go. This build implements the PKI flow with crypto/x509; there is no ACME server, provisioner database or certificate revocation.

## Run

```bash
go run . -cn service.internal
go test ./...
```

## Structure

```text
step-ca/
├── main.go                issue a certificate from the CLI
├── pki.go                 CA and issuance logic
├── pki_test.go            unit tests
└── go.mod
```

## Testing

```bash
# see the Run section
```

## Notes and limitations

- Private keys are written to local PEM files in the demo.
- There is no revocation list, OCSP responder or HSM backing.
- Only ECDSA P-256 keys are supported.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project written in Go with the standard library only. It is not a hardened production service; the notes above list the missing pieces.
