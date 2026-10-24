"use strict";

const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const { attachWebSocket, broadcast } = require("./ws");

const PUBLIC_DIR = path.join(__dirname, "..", "public");
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

function createChatServer() {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://localhost");
    const name = url.pathname === "/" ? "index.html" : url.pathname.replace(/^\/+/, "");
    const file = path.resolve(PUBLIC_DIR, name);
    if (!file.startsWith(PUBLIC_DIR)) {
      response.writeHead(403, { "content-type": "text/plain" });
      response.end("forbidden");
      return;
    }
    fs.readFile(file, (error, data) => {
      if (error) {
        response.writeHead(404, { "content-type": "text/plain" });
        response.end("not found");
        return;
      }
      response.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
      response.end(data);
    });
  });

  attachWebSocket(server, {
    open() {},
    message(client, text, clients) {
      let message;
      try {
        message = JSON.parse(text);
      } catch (error) {
        client.send(JSON.stringify({ type: "error", error: "invalid json" }));
        return;
      }
      if (message.type === "hello" || message.type === "message") {
        // Only the envelope is relayed; the server has no key to read it.
        broadcast(clients, message);
      }
    },
  });

  return server;
}

module.exports = { createChatServer };
