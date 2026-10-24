"use strict";

const canvas = document.getElementById("game");
const context = canvas.getContext("2d");
const scoreElement = document.getElementById("score");
const bestElement = document.getElementById("best");

const game = window.DemonRunner.createGame({ width: canvas.width });

function draw() {
  context.clearRect(0, 0, canvas.width, canvas.height);

  context.fillStyle = "#242c44";
  context.fillRect(0, game.ground, canvas.width, canvas.height - game.ground);

  context.fillStyle = game.over ? "#e5484d" : "#f5d90a";
  context.fillRect(game.player.x, game.player.y, game.player.size, game.player.size);

  context.fillStyle = "#8b5cf6";
  for (const obstacle of game.obstacles) {
    context.fillRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);
  }

  if (game.over) {
    context.fillStyle = "rgba(16, 19, 26, 0.7)";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#e6e6e6";
    context.font = "28px system-ui, sans-serif";
    context.fillText("Game over - press space to retry", 150, 150);
  }

  scoreElement.textContent = String(game.score);
  bestElement.textContent = String(game.best);
}

let previous = 0;
function loop(timestamp) {
  const delta = Math.min(0.05, (timestamp - previous) / 1000 || 0);
  previous = timestamp;
  game.update(delta);
  draw();
  requestAnimationFrame(loop);
}

function jump() {
  game.jump();
}

window.addEventListener("keydown", (event) => {
  if (event.code === "Space" || event.code === "ArrowUp") {
    event.preventDefault();
    jump();
  }
});
canvas.addEventListener("pointerdown", jump);

requestAnimationFrame(loop);
