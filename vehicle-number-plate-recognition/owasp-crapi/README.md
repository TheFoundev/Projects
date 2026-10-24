# OWASP crAPI

A vulnerable REST API for practising the OWASP API Top 10.

> A deliberately vulnerable API-first application for practising modern API security testing in an authorised lab.

## Overview

An original, self-contained implementation of the **OWASP crAPI** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- User and vehicle REST resources with insecure direct object references
- Tokens issued as unsigned JWTs and accepted without verification
- Mass assignment on the signup endpoint
- Seed data for the standard practice scenarios

## Stack

`JUnit; Java; Spring Boot`
The CSV stack is JUnit + Java + Spring Boot. javac is not installed here, so this is source-only: the Maven project, Spring controllers and Dockerfile are complete but were not compiled.

## Run

```bash
mvn spring-boot:run  # needs a JDK (javac is not installed here)
```

## Structure

```text
owasp-crapi/
├── pom.xml                 Maven project
├── src/main/java/          Spring Boot controllers and models
├── src/test/java/          the token test and the MockMvc scenario tests
├── Dockerfile
└── k8s/deployment.yaml
```

## Testing

```bash
mvn test        # 9 tests: the token service and the MockMvc scenarios
```

The suite has two parts:

- `TokenServiceTest`: the token service reads the subject it issued.
- `VulnerabilityScenarioTest`: the MockMvc tests that prove every practice
  scenario is reachable — the IDOR on `/identity/api/users/{id}`, the
  unsigned token, the mass assignment at signup (the client chooses its own
  role), the duplicate email and the vehicle endpoints that need no
  authentication. They assert that the vulnerable behaviour is still there, so
  a fix has to be a deliberate change.

The project is compiled with `-parameters` (set in `pom.xml`), without which
Spring cannot bind the `@PathVariable` names and every path endpoint fails
at runtime.

## Notes and limitations

- The application is deliberately vulnerable; do not deploy it publicly.
- Password hashing is intentionally absent for the practice scenarios.
- Only the main endpoints from the practice guide are implemented.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project. The listed toolchain was not available in this environment, so the repository is source-only and was checked by structural validation.
