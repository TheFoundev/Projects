# SQLite-like Database Engine

A small sorted key-value store with a binary file format.

> A step-by-step C implementation of a SQLite-like database covering a REPL, B-tree and persistence.

## Overview

An original, self-contained implementation of the **SQLite-like Database Engine** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Sorted key array with binary-search lookup
- Insert, overwrite, delete and scan
- Length-prefixed binary persistence
- Command line shell for put, get and delete

## Stack

`C; POSIX`
The CSV stack is C + POSIX. This build keeps an in-memory sorted table and persists it to a file; the index is an array rather than a full B-tree.

## Run

```bash
make
./build/app
make test
```

## Structure

```text
sqlite-like-database-engine/
├── src/db.c               sorted table and file format
├── src/db.h               public API
├── src/main.c             command line shell
├── tests/test_main.c      unit tests
└── Makefile
```

## Testing

```bash
make test
```

4 tests (`make test`), up from 2: the values, the delete, a key that is not there and the database that is written and read back.


## Notes and limitations

- There are no transactions, pages or write-ahead logging.
- The whole table is rewritten on save, so it is not suitable for large data.
- Concurrency and crash recovery are out of scope.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project. The build and tests run locally with GCC; there is no portability work beyond the platforms named in the notes.
