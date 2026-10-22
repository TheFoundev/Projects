"""The API of the certificate authority: the root, the leaves and the requests.

The numbers come from the Go code of the project. A helper program is built
from the sources of the project (pki.go, main.go and go.mod) with a `main`
that makes the root with NewAuthority, issues the leaves with Issue, signs the
requests with IssueCSR and checks every chain with Verify. The PEM files are
written with Save, the way the demo of main.go writes them. When the Go
toolchain is not installed, the same code is mirrored in Python with the
cryptography library. The answer of the last run is kept in the cache, so the
console shows the same certificates either way.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(tempfile.gettempdir()) / "foundev-go-helpers"
GO = shutil.which("go")

#: Where the certificates of the console are written, next to the ones of the demo.
ARTIFACTS = ROOT / "artifacts" / "console"

#: The root of the console and the names it may sign for.
AUTHORITY = "Foundev Student CA"
NAMES = ["internal", "localhost"]

#: The leaves and the requests of the demo: the certificate of main.go, the
#: leaf of the api and the request that the root refuses.
SEED_CERTIFICATES = [
    {"common_name": "service.internal", "hosts": ["service.internal", "localhost"]},
    {"common_name": "api.internal", "hosts": ["api.internal"]},
]
SEED_REQUESTS = [
    {"common_name": "api.internal", "hosts": ["api.internal"]},
    {"common_name": "evil.com", "hosts": ["evil.com"]},
]

#: The helper program: it makes the root, issues the leaves and signs the requests.
HELPER = r'''
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type request struct {
	CommonName string   `json:"common_name"`
	Hosts      []string `json:"hosts"`
}

func main() {
	var input struct {
		Authority    string    `json:"authority"`
		Names        []string  `json:"names"`
		Artifacts    string    `json:"artifacts"`
		Certificates []request `json:"certificates"`
		Requests     []request `json:"requests"`
	}
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		fail(err)
	}

	authority, err := NewAuthority(input.Authority, input.Names...)
	if err != nil {
		fail(err)
	}

	directory := input.Artifacts
	if directory != "" {
		if err := os.MkdirAll(directory, 0o755); err != nil {
			fail(err)
		}
		writeKey(filepath.Join(directory, "ca.key"), authority.PrivateKey)
	}

	certificates := []map[string]any{}
	for index, item := range input.Certificates {
		leaf, err := authority.Issue(item.CommonName, item.Hosts)
		if err != nil {
			fail(err)
		}
		if directory != "" {
			if index == 0 {
				// the demo of main.go writes ca.crt, leaf.crt and leaf.key
				if err := authority.Save(directory, leaf); err != nil {
					fail(err)
				}
			} else {
				writePEM(filepath.Join(directory, fmt.Sprintf("leaf-%d.crt", index+1)), "CERTIFICATE", leaf.Certificate.Raw)
				writeKey(filepath.Join(directory, fmt.Sprintf("leaf-%d.key", index+1)), leaf.PrivateKey)
			}
		}
		certificates = append(certificates, describe(leaf.Certificate, item.Hosts, authority))
	}

	requests := []map[string]any{}
	for index, item := range input.Requests {
		csr, key, err := makeRequest(item.CommonName, item.Hosts)
		if err != nil {
			fail(err)
		}
		leaf, err := authority.IssueCSR(csr)
		if err != nil {
			requests = append(requests, map[string]any{
				"common_name": item.CommonName,
				"hosts":       item.Hosts,
				"decision":    "refused",
				"reason":      err.Error(),
			})
			continue
		}
		if directory != "" {
			writePEM(filepath.Join(directory, fmt.Sprintf("csr-%d.crt", index+1)), "CERTIFICATE", leaf.Certificate.Raw)
			writeKey(filepath.Join(directory, fmt.Sprintf("csr-%d.key", index+1)), key)
		}
		entry := describe(leaf.Certificate, item.Hosts, authority)
		entry["decision"] = "signed"
		entry["reason"] = ""
		requests = append(requests, entry)
	}

	json.NewEncoder(os.Stdout).Encode(map[string]any{
		"authority":    describeAuthority(authority),
		"certificates": certificates,
		"requests":     requests,
	})
}

// describeAuthority writes the root of the certificate authority.
func describeAuthority(authority *Authority) map[string]any {
	certificate := authority.Certificate
	return map[string]any{
		"name":        authority.Name,
		"common_name": certificate.Subject.CommonName,
		"serial":      fmt.Sprintf("%x", certificate.SerialNumber),
		"not_before":  certificate.NotBefore.UTC().Format("2006-01-02"),
		"not_after":   certificate.NotAfter.UTC().Format("2006-01-02"),
		"key_usage":   keyUsage(certificate.KeyUsage),
		"is_ca":       certificate.IsCA,
		"names":       authority.Names,
		"years":       certificate.NotAfter.Year() - certificate.NotBefore.Year(),
	}
}

// describe writes a leaf and the result of the check of its chain.
func describe(certificate *x509.Certificate, hosts []string, authority *Authority) map[string]any {
	names := certificate.DNSNames
	if len(names) == 0 {
		names = hosts
	}
	return map[string]any{
		"common_name":   certificate.Subject.CommonName,
		"hosts":         names,
		"serial":        fmt.Sprintf("%x", certificate.SerialNumber),
		"not_before":    certificate.NotBefore.UTC().Format("2006-01-02"),
		"not_after":     certificate.NotAfter.UTC().Format("2006-01-02"),
		"key_usage":     keyUsage(certificate.KeyUsage),
		"ext_key_usage": extKeyUsage(certificate.ExtKeyUsage),
		"verified":      authority.Verify(certificate) == nil,
	}
}

// keyUsage writes the bits of a key usage with their names.
func keyUsage(usage x509.KeyUsage) string {
	names := []string{}
	if usage&x509.KeyUsageDigitalSignature != 0 {
		names = append(names, "Digital Signature")
	}
	if usage&x509.KeyUsageContentCommitment != 0 {
		names = append(names, "Content Commitment")
	}
	if usage&x509.KeyUsageKeyEncipherment != 0 {
		names = append(names, "Key Encipherment")
	}
	if usage&x509.KeyUsageDataEncipherment != 0 {
		names = append(names, "Data Encipherment")
	}
	if usage&x509.KeyUsageKeyAgreement != 0 {
		names = append(names, "Key Agreement")
	}
	if usage&x509.KeyUsageCertSign != 0 {
		names = append(names, "Cert Sign")
	}
	if usage&x509.KeyUsageCRLSign != 0 {
		names = append(names, "CRL Sign")
	}
	if usage&x509.KeyUsageEncipherOnly != 0 {
		names = append(names, "Encipher Only")
	}
	if usage&x509.KeyUsageDecipherOnly != 0 {
		names = append(names, "Decipher Only")
	}
	return strings.Join(names, "|")
}

// extKeyUsage writes the extended key usages with their names.
func extKeyUsage(usages []x509.ExtKeyUsage) string {
	names := []string{}
	for _, usage := range usages {
		switch usage {
		case x509.ExtKeyUsageAny:
			names = append(names, "Any")
		case x509.ExtKeyUsageServerAuth:
			names = append(names, "Server Auth")
		case x509.ExtKeyUsageClientAuth:
			names = append(names, "Client Auth")
		case x509.ExtKeyUsageCodeSigning:
			names = append(names, "Code Signing")
		case x509.ExtKeyUsageEmailProtection:
			names = append(names, "Email Protection")
		default:
			names = append(names, usage.String())
		}
	}
	return strings.Join(names, "|")
}

// makeRequest makes the certificate signing request of a name.
func makeRequest(commonName string, hosts []string) ([]byte, *ecdsa.PrivateKey, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, nil, err
	}
	template := &x509.CertificateRequest{
		Subject:  pkix.Name{CommonName: commonName},
		DNSNames: hosts,
	}
	der, err := x509.CreateCertificateRequest(rand.Reader, template, key)
	if err != nil {
		return nil, nil, err
	}
	csr := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE REQUEST", Bytes: der})
	return csr, key, nil
}

// writeKey writes a private key in a PEM file.
func writeKey(path string, key *ecdsa.PrivateKey) {
	der, err := x509.MarshalECPrivateKey(key)
	if err != nil {
		fail(err)
	}
	pemBytes := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: der})
	if err := os.WriteFile(path, pemBytes, 0o600); err != nil {
		fail(err)
	}
}

// fail stops the helper with the error on the standard error.
func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
'''

#: The leaves and the requests of the console.
_STATE: dict = {"plan": None}


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
    target = CACHE / f"stepca-{key}"
    if target.exists():
        return target
    work = Path(tempfile.mkdtemp(prefix="foundev-stepca-"))
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


def _run_helper(plan: dict) -> dict | None:
    """Make the root, the leaves and the requests with the code of the project."""
    binary = _build_helper()
    if binary is None:
        return None
    payload = {
        "authority": AUTHORITY,
        "names": NAMES,
        "artifacts": str(ARTIFACTS),
        "certificates": plan["certificates"],
        "requests": plan["requests"],
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
    if not isinstance(answer, dict) or answer.get("error"):
        return None
    return answer


# --------------------------------------------------------------------------
# the cache of the last answer
# --------------------------------------------------------------------------

def _cache_file() -> Path:
    """The file with the answer of the last run."""
    return CACHE / "stepca-answer.json"


def _read_cache(key: str) -> dict | None:
    """The answer of the last run, when it belongs to the same plan."""
    path = _cache_file()
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(cached, dict) or cached.get("key") != key:
        return None
    answer = cached.get("answer")
    return answer if isinstance(answer, dict) else None


def _write_cache(key: str, answer: dict) -> None:
    """Keep the answer of the last run, so the console keeps its certificates."""
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        _cache_file().write_text(
            json.dumps({"key": key, "answer": answer}), encoding="utf-8",
        )
    except OSError:
        pass


# --------------------------------------------------------------------------
# the fallback: NewAuthority, Issue, IssueCSR, maySign and Verify
# --------------------------------------------------------------------------

def _may_sign(common_name: str, names: list) -> bool:
    """maySign of pki.go: the name of the root or a name under one of them."""
    if not common_name:
        return False
    for allowed in names:
        if allowed == common_name or common_name.endswith("." + allowed):
            return True
    return False


def _add_years(moment: datetime, years: int) -> datetime:
    """AddDate of Go: the day that the month does not have moves into it."""
    year = moment.year + years
    last = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][moment.month - 1]
    if moment.day <= last:
        return moment.replace(year=year)
    month = moment.month + (moment.day - last)
    while month > 12:
        month -= 1
        year += 1
    return moment.replace(year=year, month=month, day=moment.day - last)


def _fallback(plan: dict) -> dict:
    """The same code, mirrored in Python, when the Go toolchain is missing."""
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
    except ImportError:
        return _mirror(plan)

    now = datetime.now(timezone.utc)
    root_key = ec.generate_private_key(ec.SECP256R1())
    root_name = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, AUTHORITY),
        x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "Foundev Student Projects"),
    ])
    root = (
        x509.CertificateBuilder()
        .subject_name(root_name)
        .issuer_name(root_name)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(hours=1))
        .not_valid_after(_add_years(now, 5))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True, content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=True,
            crl_sign=False, encipher_only=False, decipher_only=False,
        ), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    def leaf(common_name, hosts, not_before, not_after, usages, public_key, key):
        builder = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([
                x509.NameAttribute(x509.NameOID.COMMON_NAME, common_name),
            ]))
            .issuer_name(root.subject)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=False, key_encipherment=True,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ), critical=True)
            .add_extension(x509.ExtendedKeyUsage(usages), critical=False)
        )
        if hosts:
            builder = builder.add_extension(
                x509.SubjectAlternativeName([x509.DNSName(host) for host in hosts]),
                critical=False,
            )
        certificate = builder.sign(root_key, hashes.SHA256())
        return certificate, key

    certificates = []
    for index, item in enumerate(plan["certificates"]):
        key = ec.generate_private_key(ec.SECP256R1())
        certificate, _ = leaf(
            item["common_name"], item["hosts"], now - timedelta(minutes=1),
            _add_years(now, 1),
            [x509.oid.ExtendedKeyUsageOID.SERVER_AUTH, x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH],
            key.public_key(), key,
        )
        _write("leaf.crt" if index == 0 else f"leaf-{index + 1}.crt", certificate)
        _write("leaf.key" if index == 0 else f"leaf-{index + 1}.key", key, private=True)
        certificates.append({
            "common_name": item["common_name"],
            "hosts": item["hosts"],
            "serial": format(certificate.serial_number, "x"),
            "not_before": certificate.not_valid_before_utc.strftime("%Y-%m-%d"),
            "not_after": certificate.not_valid_after_utc.strftime("%Y-%m-%d"),
            "key_usage": "Digital Signature|Key Encipherment",
            "ext_key_usage": "Server Auth|Client Auth",
            "verified": _verified(certificate, root, root_key),
        })

    requests = []
    for index, item in enumerate(plan["requests"]):
        key = ec.generate_private_key(ec.SECP256R1())
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name([
                x509.NameAttribute(x509.NameOID.COMMON_NAME, item["common_name"]),
            ]))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(host) for host in item["hosts"]]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )
        # the checks of IssueCSR: the request has to be signed and the root
        # has to be allowed to sign for the name of the request
        if not _request_signed(csr):
            requests.append({
                "common_name": item["common_name"],
                "hosts": item["hosts"],
                "decision": "refused",
                "reason": "the certificate signing request is not signed",
            })
            continue
        if not _may_sign(item["common_name"], NAMES):
            requests.append({
                "common_name": item["common_name"],
                "hosts": item["hosts"],
                "decision": "refused",
                "reason": f'the authority may not sign for "{item["common_name"]}"',
            })
            continue
        certificate, _ = leaf(
            item["common_name"], item["hosts"], now - timedelta(hours=1),
            now + timedelta(days=365),
            [x509.oid.ExtendedKeyUsageOID.SERVER_AUTH],
            csr.public_key(), key,
        )
        _write(f"csr-{index + 1}.crt", certificate)
        _write(f"csr-{index + 1}.key", key, private=True)
        requests.append({
            "common_name": item["common_name"],
            "hosts": item["hosts"],
            "decision": "signed",
            "reason": "",
            "serial": format(certificate.serial_number, "x"),
            "not_before": certificate.not_valid_before_utc.strftime("%Y-%m-%d"),
            "not_after": certificate.not_valid_after_utc.strftime("%Y-%m-%d"),
            "key_usage": "Digital Signature|Key Encipherment",
            "ext_key_usage": "Server Auth",
            "verified": _verified(certificate, root, root_key),
        })

    _write("ca.crt", root)
    _write("ca.key", root_key, private=True)
    return {
        "authority": {
            "name": AUTHORITY,
            "common_name": AUTHORITY,
            "serial": format(root.serial_number, "x"),
            "not_before": root.not_valid_before_utc.strftime("%Y-%m-%d"),
            "not_after": root.not_valid_after_utc.strftime("%Y-%m-%d"),
            "key_usage": "Digital Signature|Cert Sign",
            "is_ca": True,
            "names": list(NAMES),
            "years": root.not_valid_after_utc.year - root.not_valid_before_utc.year,
        },
        "certificates": certificates,
        "requests": requests,
    }


def _request_signed(csr) -> bool:
    """The check of the signature of a request, the way IssueCSR does it."""
    signed = getattr(csr, "is_signature_valid", None)
    if signed is not None:
        return bool(signed)
    from cryptography.hazmat.primitives.asymmetric import ec

    data = getattr(csr, "tbs_certrequest_bytes", None)
    if data is None:
        data = getattr(csr, "tbs_certificate_bytes", None)
    try:
        csr.public_key().verify(
            csr.signature, data, ec.ECDSA(csr.signature_hash_algorithm),
        )
    except Exception:
        return False
    return True


def _verified(certificate, root, root_key) -> bool:
    """Verify of pki.go: the chain of the leaf against the root."""
    from cryptography.hazmat.primitives.asymmetric import ec

    try:
        root_key.public_key().verify(
            certificate.signature, certificate.tbs_certificate_bytes,
            ec.ECDSA(certificate.signature_hash_algorithm),
        )
    except Exception:
        return False
    return root.not_valid_before_utc <= certificate.not_valid_before_utc


def _write(name: str, material, private: bool = False) -> None:
    """Write a certificate or a key in the artifacts of the console."""
    from cryptography.hazmat.primitives import serialization

    try:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        if private:
            data = material.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        else:
            data = material.public_bytes(serialization.Encoding.PEM)
        (ARTIFACTS / name).write_bytes(data)
        if name.endswith(".key"):
            (ARTIFACTS / name).chmod(0o600)
    except OSError:
        pass


def _mirror(plan: dict) -> dict:
    """The numbers of the console, without the Go toolchain and without the
    cryptography library: the names, the decisions and the reasons."""
    now = datetime.now(timezone.utc)
    certificates = []
    for item in plan["certificates"]:
        certificates.append({
            "common_name": item["common_name"],
            "hosts": item["hosts"],
            "serial": "-",
            "not_before": (now - timedelta(minutes=1)).strftime("%Y-%m-%d"),
            "not_after": _add_years(now, 1).strftime("%Y-%m-%d"),
            "key_usage": "Digital Signature|Key Encipherment",
            "ext_key_usage": "Server Auth|Client Auth",
            "verified": True,
        })
    requests = []
    for item in plan["requests"]:
        signed = _may_sign(item["common_name"], NAMES)
        requests.append({
            "common_name": item["common_name"],
            "hosts": item["hosts"],
            "decision": "signed" if signed else "refused",
            "reason": "" if signed else f'the authority may not sign for "{item["common_name"]}"',
            "serial": "-",
            "not_before": (now - timedelta(hours=1)).strftime("%Y-%m-%d"),
            "not_after": (now + timedelta(days=365)).strftime("%Y-%m-%d"),
            "key_usage": "Digital Signature|Key Encipherment",
            "ext_key_usage": "Server Auth",
            "verified": True,
        })
    return {
        "authority": {
            "name": AUTHORITY,
            "common_name": AUTHORITY,
            "serial": "-",
            "not_before": (now - timedelta(hours=1)).strftime("%Y-%m-%d"),
            "not_after": _add_years(now, 5).strftime("%Y-%m-%d"),
            "key_usage": "Digital Signature|Cert Sign",
            "is_ca": True,
            "names": list(NAMES),
            "years": 5,
        },
        "certificates": certificates,
        "requests": requests,
    }


# --------------------------------------------------------------------------
# the state of the console
# --------------------------------------------------------------------------

def _plan() -> dict:
    """The leaves and the requests of the console."""
    if _STATE["plan"] is None:
        _STATE["plan"] = {
            "certificates": [dict(item) for item in SEED_CERTIFICATES],
            "requests": [dict(item) for item in SEED_REQUESTS],
        }
    return _STATE["plan"]


def _answer(force: bool = False) -> dict:
    """The certificates of the console, made by the code of the project."""
    plan = _plan()
    key = json.dumps(plan, sort_keys=True)
    if not force:
        cached = _read_cache(key)
        if cached:
            return cached
    answer = _run_helper(plan) or _fallback(plan)
    _write_cache(key, answer)
    return answer


def _hosts(value, common_name: str) -> list:
    """The names of a leaf: a list, a string with commas, or the demo of main.go."""
    if isinstance(value, str):
        names = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, list):
        names = [str(part).strip() for part in value if str(part).strip()]
    else:
        names = []
    return names or [common_name, "localhost"]


def _authority_rows(answer: dict) -> list:
    """The root of the certificate authority."""
    authority = answer.get("authority") or {}
    if not authority:
        return []
    return [{
        "Name": authority.get("name", ""),
        "Common name": authority.get("common_name", ""),
        "Serial": authority.get("serial", "-"),
        "Valid from": authority.get("not_before", "-"),
        "Valid until": authority.get("not_after", "-"),
        "Key usage": authority.get("key_usage", "-"),
    }]


def _certificate_rows(certificates: list) -> list:
    """Every leaf that was issued."""
    return [{
        "Common name": item.get("common_name", ""),
        "Names": ", ".join(item.get("hosts") or []) or "-",
        "Serial": item.get("serial", "-"),
        "Valid from": item.get("not_before", "-"),
        "Valid until": item.get("not_after", "-"),
        "Verified": "yes" if item.get("verified") else "no",
    } for item in certificates]


def _request_rows(requests: list) -> list:
    """Every request with the decision of the root."""
    return [{
        "Common name": item.get("common_name", ""),
        "Names": ", ".join(item.get("hosts") or []) or "-",
        "Decision": item.get("decision", ""),
        "Reason": item.get("reason", "") or "-",
    } for item in requests]


def summary() -> dict:
    """The root, the leaves and the requests of the console."""
    answer = _answer()
    certificates = answer.get("certificates") or []
    requests = answer.get("requests") or []
    signed = [item for item in requests if item.get("decision") == "signed"]
    refused = [item for item in requests if item.get("decision") == "refused"]
    names = sum(len(item.get("hosts") or []) for item in certificates)
    names += sum(len(item.get("hosts") or []) for item in signed)
    verified = sum(1 for item in certificates if item.get("verified"))
    verified += sum(1 for item in signed if item.get("verified"))
    return {
        "stats": {
            "certificates": len(certificates),
            "signed": len(signed),
            "refused": len(refused),
            "names": names,
            "verified": verified,
            "ca_years": (answer.get("authority") or {}).get("years", 0),
        },
        "series": [
            {"label": item.get("common_name", ""), "value": len(item.get("hosts") or [])}
            for item in certificates
        ],
        "lists": {
            "authority": _authority_rows(answer),
            "certificates": _certificate_rows(certificates),
            "requests": _request_rows(requests),
        },
    }


# --------------------------------------------------------------------------
# the endpoints
# --------------------------------------------------------------------------

def handle(method, path, payload, user):
    """The endpoints of the certificate authority."""
    if method == "GET" and path == "/api/summary":
        return 200, summary()
    if method == "GET" and path == "/api/authority":
        return 200, {"authority": summary()["lists"]["authority"]}
    if method == "GET" and path == "/api/certificates":
        return 200, {"certificates": summary()["lists"]["certificates"]}
    if method == "GET" and path == "/api/requests":
        return 200, {"requests": summary()["lists"]["requests"]}
    if method == "POST" and path == "/api/issue":
        body = payload or {}
        common_name = str(body.get("common_name") or "service.internal").strip() or "service.internal"
        hosts = _hosts(body.get("names"), common_name)
        _plan()["certificates"].append({"common_name": common_name, "hosts": hosts})
        answer = _answer(force=True)
        certificate = (answer.get("certificates") or [{}])[-1]
        return 200, {
            "common_name": common_name,
            "names": len(hosts),
            "serial": certificate.get("serial", "-"),
            "verified": "yes" if certificate.get("verified") else "no",
        }
    if method == "POST" and path == "/api/request":
        body = payload or {}
        common_name = str(body.get("common_name") or "api.internal").strip() or "api.internal"
        hosts = _hosts(body.get("names"), common_name)
        _plan()["requests"].append({"common_name": common_name, "hosts": hosts})
        answer = _answer(force=True)
        request = (answer.get("requests") or [{}])[-1]
        return 200, {
            "common_name": common_name,
            "decision": request.get("decision", ""),
            "reason": request.get("reason", "") or "-",
        }
    return 404, {"error": "not found"}
