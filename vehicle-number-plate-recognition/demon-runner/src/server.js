"use strict";

const http = require("node:http");
const { servePublic } = require("./static");

function createGameServer() {
  return http.createServer((request, response) => {
    servePublic(request, response);
  });
}

if (require.main === module) {
  const port = Number(process.env.PORT || 8080);
  createGameServer().listen(port, () => {
    console.log(`play at http://localhost:${port}`);
  });
}

module.exports = { createGameServer };
