"use strict";

const state = { socket: null, key: null };

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function toBase64(bytes) {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function fromBase64(text) {
  return Uint8Array.from(atob(text), (character) => character.charCodeAt(0));
}

async function deriveKey(passphrase) {
  const material = await crypto.subtle.importKey("raw", encoder.encode(passphrase), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: encoder.encode("signal-style-chat"), iterations: 120000, hash: "SHA-256" },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

async function encrypt(text) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, state.key, encoder.encode(text));
  return { iv: toBase64(iv), data: toBase64(new Uint8Array(data)) };
}

async function decrypt(envelope) {
  const iv = fromBase64(envelope.iv);
  const data = fromBase64(envelope.data);
  const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, state.key, data);
  return decoder.decode(plain);
}

function log(line) {
  const element = document.createElement("p");
  element.textContent = line;
  document.getElementById("log").appendChild(element);
}

async function connect() {
  const name = document.getElementById("name").value || "guest";
  const passphrase = document.getElementById("passphrase").value || "change-me";
  state.key = await deriveKey(passphrase);

  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  state.socket = new WebSocket(`${protocol}//${location.host}`);

  state.socket.addEventListener("open", () => {
    document.getElementById("status").textContent = "connected";
    document.getElementById("send").disabled = false;
    state.socket.send(JSON.stringify({ type: "hello", name }));
  });

  state.socket.addEventListener("message", async (event) => {
    const message = JSON.parse(event.data);
    if (message.type !== "message") {
      return;
    }
    try {
      const text = await decrypt(message.payload);
      log(`${message.name}: ${text}`);
    } catch (error) {
      log("[could not decrypt a message from another room]");
    }
  });

  state.socket.addEventListener("close", () => {
    document.getElementById("status").textContent = "offline";
    document.getElementById("send").disabled = true;
  });
}

async function send() {
  const input = document.getElementById("message");
  const text = input.value;
  if (!text || !state.socket || state.socket.readyState !== WebSocket.OPEN) {
    return;
  }
  const name = document.getElementById("name").value || "guest";
  const payload = await encrypt(text);
  state.socket.send(JSON.stringify({ type: "message", name, payload }));
  log(`${name}: ${text}`);
  input.value = "";
}

document.getElementById("connect").addEventListener("click", connect);
document.getElementById("send").addEventListener("click", send);
document.getElementById("message").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    send();
  }
});
