const fs = require("node:fs");
const path = require("node:path");

const PUBLIC_DIR = path.join(__dirname, "..", "public");
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

function servePublic(request, response) {
  const url = new URL(request.url, "http://localhost");
  const name = url.pathname === "/" ? "index.html" : url.pathname.replace(/^\/+/, "");
  const file = path.resolve(PUBLIC_DIR, name);
  if (!file.startsWith(PUBLIC_DIR)) {
    response.writeHead(403, { "content-type": "text/plain" });
    response.end("forbidden");
    return;
  }
  let data;
  try {
    data = fs.readFileSync(file);
  } catch (error) {
    response.writeHead(404, { "content-type": "text/plain" });
    response.end("not found");
    return;
  }
  response.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  response.end(data);
}

module.exports = { servePublic };
