# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
This repository (`projects/`) is the local build workspace and catalog for **Foundev**, containing ~130 standalone, runnable project implementations. Each subdirectory is a self-contained MVP project matching a specific tech stack and goal.

## Project Structure
- Each subdirectory (e.g., `actual-budget/`, `abstractive-document-summarization/`) is an independent project.
- Projects are self-contained with their own `.git`, `LICENSE`, `README.md`, and dependency manifests.
- Most projects follow a clean structure: `src/` (or `server/`/`client/`), `tests/`, and entry point files (`app.py`, `index.js`, etc.).

## Development Commands
Commands should be run inside the specific project's subdirectory.

### Node.js / Web
- **Install dependencies:** `npm install`
- **Run project:** `npm start` or `node <entry-point>.js`
- **Run tests:** `npm test`
- **Lint:** `npm run lint` (if available)

### Python / ML
- **Install dependencies:** `pip install -r requirements.txt`
- **Run project:** `python app.py` or `python main.py`
- **Run tests:** `pytest` or `pytest tests/`
- **Single test:** `pytest tests/test_file.py::test_name`

### Go
- **Run project:** `go run .`
- **Run tests:** `go test ./...`

### C / Systems
- **Build:** `make`
- **Run tests:** `make test`

### Rust
- **Build/Run:** `cargo run`
- **Run tests:** `cargo test`

## Project Management
- **Catalog metadata:** Located in `../Foundev-main/data/exports/projects-to-keep.csv`.
- **Build state:** Tracked in `../.foundev-build-state.json`.
- **Audit results:** Found in `../projects-completeness-audit.md`.
- **Tools:** Management scripts are located in `../tools/` and `../.builder/`.

## Architecture Notes
- Projects are designed to be "production-lean" and student-safe.
- Avoid adding complex frameworks unless specified in the project's `README.md` or CSV stack.
- Each project must remain isolated; do not introduce cross-project dependencies.
