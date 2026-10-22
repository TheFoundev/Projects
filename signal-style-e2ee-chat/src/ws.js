"use strict";

const crypto = require("node:crypto");

const GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

function acceptKey(key) {
  return crypto.createHash("sha1").update(key + GUID).digest("base64");
}

function encodeFrame(opcode, payload) {
  const body = Buffer.isBuffer(payload) ? payload : Buffer.from(String(payload), "utf8");
  let header;
  if (body.length < 126) {
    header = Buffer.alloc(2);
    header[0] = 0x80 | opcode;
    header[1] = body.length;
  } else if (body.length < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x80 | opcode;
    header[1] = 126;
    header.writeUInt16BE(body.length, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x80 | opcode;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(body.length), 2);
  }
  return Buffer.concat([header, body]);
}

function encodeText(text) {
  return encodeFrame(0x1, text);
}

function parseFrame(buffer) {
  if (buffer.length < 2) {
    return null;
  }
  const opcode = buffer[0] & 0x0f;
  const masked = (buffer[1] & 0x80) !== 0;
  let length = buffer[1] & 0x7f;
  let offset = 2;
  if (length === 126) {
    if (buffer.length < 4) {
      return null;
    }
    length = buffer.readUInt16BE(2);
    offset = 4;
  } else if (length === 127) {
    if (buffer.length < 10) {
      return null;
    }
    const big = buffer.readBigUInt64BE(2);
    if (big > BigInt(Number.MAX_SAFE_INTEGER)) {
      throw new Error("frame too large");
    }
    length = Number(big);
    offset = 10;
  }
  let mask = null;
  if (masked) {
    if (buffer.length < offset + 4) {
      return null;
    }
    mask = buffer.subarray(offset, offset + 4);
    offset += 4;
  }
  if (buffer.length < offset + length) {
    return null;
  }
  const payload = Buffer.from(buffer.subarray(offset, offset + length));
  if (mask) {
    for (let index = 0; index < payload.length; index++) {
      payload[index] ^= mask[index % 4];
    }
  }
  return { opcode, payload, rest: buffer.subarray(offset + length) };
}

function attachWebSocket(httpServer, handlers) {
  const clients = new Set();
  httpServer.on("upgrade", (request, socket) => {
    const key = request.headers["sec-websocket-key"];
    if (!key) {
      socket.destroy();
      return;
    }
    socket.write([
      "HTTP/1.1 101 Switching Protocols",
      "Upgrade: websocket",
      "Connection: Upgrade",
      "Sec-WebSocket-Accept: " + acceptKey(key),
      "",
      "",
    ].join("\r\n"));

    const client = {
      socket,
      send(text) {
        if (!socket.destroyed) {
          socket.write(encodeText(text));
        }
      },
      close() {
        socket.end();
      },
    };
    clients.add(client);
    let buffer = Buffer.alloc(0);

    socket.on("data", (chunk) => {
      buffer = Buffer.concat([buffer, chunk]);
      let frame = parseFrame(buffer);
      while (frame !== null) {
        buffer = frame.rest;
        if (frame.opcode === 0x8) {
          socket.end();
          return;
        }
        if (frame.opcode === 0x9) {
          socket.write(encodeFrame(0x0a, frame.payload));
        } else if (frame.opcode === 0x1) {
          handlers.message(client, frame.payload.toString("utf8"), clients);
        }
        frame = parseFrame(buffer);
      }
    });
    socket.on("close", () => clients.delete(client));
    socket.on("error", () => clients.delete(client));
    handlers.open(client, clients);
  });
  return clients;
}

function broadcast(clients, data, except) {
  const text = typeof data === "string" ? data : JSON.stringify(data);
  for (const client of clients) {
    if (client !== except) {
      client.send(text);
    }
  }
}

module.exports = { acceptKey, encodeFrame, encodeText, parseFrame, attachWebSocket, broadcast };
