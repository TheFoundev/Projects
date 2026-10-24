"use strict";

const canvas = document.getElementById("game");
const context = canvas.getContext("2d");
const leftElement = document.getElementById("left");
const flicksElement = document.getElementById("flicks");

const game = window.FlickGame.createGame({ width: canvas.width, height: canvas.height });

function draw() {
  context.clearRect(0, 0, canvas.width, canvas.height);

  context.fillStyle = "#4ade80";
  for (const block of game.blocks) {
    context.fillRect(block.x, block.y, block.width, block.height);
  }

  if (game.aiming) {
    context.strokeStyle = "#facc15";
    context.beginPath();
    context.moveTo(game.ball.x, game.ball.y);
    context.lineTo(game.aim.x, game.aim.y);
    context.stroke();
  }

  context.fillStyle = "#38bdf8";
  context.beginPath();
  context.arc(game.ball.x, game.ball.y, game.ball.radius, 0, Math.PI * 2);
  context.fill();

  if (game.won) {
    context.fillStyle = "rgba(15, 23, 32, 0.75)";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#e8eef6";
    context.font = "28px system-ui, sans-serif";
    context.fillText(`Cleared in ${game.flicks} flicks`, 170, 220);
  }

  leftElement.textContent = String(game.blockCount());
  flicksElement.textContent = String(game.flicks);
}

function position(event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((event.clientX - rect.left) / rect.width) * canvas.width,
    y: ((event.clientY - rect.top) / rect.height) * canvas.height,
  };
}

canvas.addEventListener("pointerdown", (event) => {
  const point = position(event);
  game.startAim(point.x, point.y);
});
canvas.addEventListener("pointermove", (event) => {
  const point = position(event);
  game.updateAim(point.x, point.y);
});
canvas.addEventListener("pointerup", () => {
  game.release();
});

let previous = 0;
function loop(timestamp) {
  const delta = Math.min(0.05, (timestamp - previous) / 1000 || 0);
  previous = timestamp;
  game.update(delta);
  draw();
  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);
