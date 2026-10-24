"use strict";

const http = require("node:http");
const crypto = require("node:crypto");
const { users, comments } = require("./store");

// The app is vulnerable on purpose. With NODEGOAT_HARDENED=1 the fixes are
// applied as well, so the two ways can be compared.
const HARDENED = process.env.NODEGOAT_HARDENED === "1";

// The key of the signed cookies and of the CSRF tokens.
const SECRET = process.env.NODEGOAT_SECRET || crypto.randomBytes(32).toString("hex");

/**
 * The text of a page, with the markup of the text taken out.
 *
 * The vulnerable version puts the text into the page as it is, which is the
 * XSS of the exercise.
 */
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** The value that goes into a page. */
function forOutput(text) {
  return HARDENED ? escapeHtml(text) : String(text);
}

/**
 * A token that ties a form to the session.
 *
 * The token is the signature of the session id, so it cannot be made up.
 */
function csrfToken(sessionId) {
  return crypto.createHmac("sha256", SECRET).update(String(sessionId)).digest("hex");
}

/** True when the token of a form belongs to the session. */
function csrfValid(sessionId, token) {
  if (!HARDENED) return true;
  const expected = csrfToken(sessionId);
  if (!token || token.length !== expected.length) return false;
  return crypto.timingSafeEqual(Buffer.from(token), Buffer.from(expected));
}

/**
 * A cookie with the role, signed.
 *
 * The vulnerable version reads the role straight from the cookie, so a
 * visitor can make themself an administrator.
 */
function roleCookie(role) {
  const value = Buffer.from(String(role)).toString("base64");
  if (!HARDENED) return `role=${role}; Path=/`;
  const signature = crypto.createHmac("sha256", SECRET).update(value).digest("base64");
  return `role=${value}.${signature}; Path=/; HttpOnly; SameSite=Lax`;
}

/** The role of a signed cookie, or an empty string when it is not right. */
function roleFromCookie(value) {
  if (!HARDENED) return value;
  const parts = String(value || "").split(".");
  if (parts.length !== 2) return "";
  const expected = crypto.createHmac("sha256", SECRET).update(parts[0]).digest("base64");
  if (expected.length !== parts[1].length) return "";
  if (!crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(parts[1]))) return "";
  return Buffer.from(parts[0], "base64").toString("utf8");
}

/** The password of a user, hashed. */
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.scryptSync(String(password), salt, 32).toString("hex");
  return `${salt}:${hash}`;
}

/** True when the password is the one of the user. */
function passwordMatches(user, password) {
  if (!HARDENED) return user.password === password;
  const [salt, hash] = String(user.password || "").split(":");
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(String(password), salt, 32).toString("hex");
  return crypto.timingSafeEqual(Buffer.from(candidate), Buffer.from(hash));
}

const INDEX = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>NodeGoat practice app</title></head>
<body>
  <h1>NodeGoat practice app</h1>
  <p>This application is intentionally vulnerable. Run it locally only.</p>
  <h2>Search</h2>
  <form action="/search" method="get">
    <input name="q" placeholder="username">
    <button type="submit">Search</button>
  </form>
  <h2>Login</h2>
  <form action="/login" method="post">
    <input name="username" placeholder="username">
    <input name="password" type="password" placeholder="password">
    <input type="hidden" name="csrf" value="${csrfToken("public")}">
    <button type="submit">Sign in</button>
  </form>
  <h2>Comment</h2>
  <form action="/comments" method="post">
    <input name="text" placeholder="comment">
    <button type="submit">Post</button>
  </form>
</body>
</html>`;

function send(response, status, body, contentType = "text/html; charset=utf-8") {
  response.writeHead(status, { "content-type": contentType });
  response.end(body);
}

function readBody(request) {
  return new Promise((resolve) => {
    let data = "";
    request.on("data", (chunk) => {
      data += chunk;
    });
    request.on("end", () => resolve(data));
  });
}

function parseCookies(request) {
  const cookies = {};
  for (const part of (request.headers.cookie || "").split(";")) {
    const trimmed = part.trim();
    if (!trimmed) {
      continue;
    }
    const separator = trimmed.indexOf("=");
    if (separator === -1) {
      continue;
    }
    cookies[trimmed.slice(0, separator)] = trimmed.slice(separator + 1);
  }
  return cookies;
}

function createApp() {
  return http.createServer(async (request, response) => {
    const url = new URL(request.url, "http://localhost");

    if (request.method === "GET" && url.pathname === "/") {
      send(response, 200, INDEX);
      return;
    }

    if (request.method === "GET" && url.pathname === "/search") {
      const query = url.searchParams.get("q") || "";
      // Deliberately naive: this stands in for a string-built database query.
      const injected = query.includes("' OR '1'='1") || query.includes("1=1");
      const results = injected ? users : users.filter((user) => user.username.includes(query));
      send(response, 200, JSON.stringify({ query, results }), "application/json");
      return;
    }

    if (request.method === "GET" && url.pathname === "/api/users") {
      // Broken access control: no authentication at all.
      send(response, 200, JSON.stringify(users), "application/json");
      return;
    }

    if (request.method === "GET" && url.pathname.startsWith("/api/users/")) {
      // IDOR: any caller can read any user record.
      const id = Number(url.pathname.split("/").pop());
      const user = users.find((entry) => entry.id === id);
      if (!user) {
        send(response, 404, JSON.stringify({ error: "not found" }), "application/json");
        return;
      }
      send(response, 200, JSON.stringify(user), "application/json");
      return;
    }

    if (request.method === "GET" && url.pathname === "/profile") {
      const name = url.searchParams.get("name") || "guest";
      // Reflected XSS: the value is placed in the page without escaping.
      send(response, 200, `<html><body><h1>Profile</h1><p>Hello ${forOutput(name)}</p></body></html>`);
      return;
    }

    if (request.method === "POST" && url.pathname === "/login") {
      const body = await readBody(request);
      const form = new URLSearchParams(body);
      const username = form.get("username") || "";
      const password = form.get("password") || "";
      const user = users.find((entry) => entry.username === username && passwordMatches(entry, password));
      if (!user) {
        send(response, 401, "invalid credentials");
        return;
      }
      response.writeHead(302, {
        location: "/admin",
        "set-cookie": roleCookie(user.role),
      });
      response.end();
      return;
    }

    if (request.method === "GET" && url.pathname === "/admin") {
      const cookies = parseCookies(request);
      // Trusting a client-controlled cookie is the point of the exercise.
      if (roleFromCookie(cookies.role) !== "admin") {
        send(response, 403, "admin only");
        return;
      }
      send(response, 200, "<html><body><h1>Admin</h1><p>All user records are visible here.</p></body></html>");
      return;
    }

    if (request.method === "POST" && url.pathname === "/comments") {
      const body = await readBody(request);
      const form = new URLSearchParams(body);
      const text = form.get("text") || "";
      // Stored XSS: raw markup is kept and rendered later.
      comments.push({ text, createdAt: Date.now() });
      send(response, 201, "stored");
      return;
    }

    if (request.method === "GET" && url.pathname === "/comments") {
      const rendered = comments.map((comment) => `<div>${forOutput(comment.text)}</div>`).join("");
      send(response, 200, `<html><body>${rendered}</body></html>`);
      return;
    }

    send(response, 404, "not found");
  });
}

module.exports = { createApp };
