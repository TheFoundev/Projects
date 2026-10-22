# Userspace TCP/IP Stack

Parse and build Ethernet, IPv4 and TCP headers in userspace.

> A small userspace TCP/IP stack written for learning how protocols are implemented end to end.

## Overview

An original, self-contained implementation of the **Userspace TCP/IP Stack** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Header parsing with length checks
- Internet checksum computation and verification
- Packet builder for IPv4 and TCP
- Loopback stack that maps ports to handlers

## Stack

`C; POSIX`
The CSV stack is C + POSIX. This build works on raw byte buffers and an in-process loopback; the TUN/TAP device is documented but not opened in tests.

## Run

```bash
make
./build/app
make test
```

## Structure

```text
userspace-tcp-ip-stack/
├── src/packet.c            header parsing and building
├── src/packet.h            structs and API
├── src/main.c              demo program
├── tests/test_main.c       unit tests
└── Makefile
```

## Testing

```bash
make test
```

6 tests (`make test`), up from 2: the checksum, the byte order helpers, the headers and a packet that is built.


## Notes and limitations

- There is no congestion control, retransmission or TCP state machine.
- The TUN device code is optional and needs root to run.
- Only IPv4 is supported.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project. The build and tests run locally with GCC; there is no portability work beyond the platforms named in the notes.
