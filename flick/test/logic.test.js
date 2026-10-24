"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createGame, buildBlocks } = require("../public/logic.js");

test("a board is generated deterministically from a seed", () => {
  const first = buildBlocks(640, 5, 9, 7);
  const second = buildBlocks(640, 5, 9, 7);
  const different = buildBlocks(640, 5, 9, 8);
  assert.equal(first.length, second.length);
  assert.deepEqual(first[0], second[0]);
  assert.notDeepEqual(first.map((block) => block.x), different.map((block) => block.x));
  assert.equal(first.length > 0, true);
});

test("releasing a drag flicks the ball", () => {
  const game = createGame();
  assert.equal(game.moving, false);
  game.startAim(game.ball.x, game.ball.y + 100);
  assert.equal(game.release(), true);
  assert.equal(game.moving, true);
  assert.equal(game.flicks, 1);
  assert.equal(game.ball.vy < 0, true);
});

test("a tiny drag does not count as a flick", () => {
  const game = createGame();
  game.startAim(game.ball.x, game.ball.y);
  assert.equal(game.release(), false);
  assert.equal(game.flicks, 0);
});

test("hitting a block removes it", () => {
  const game = createGame({ rows: 1, columns: 1, seed: 1 });
  assert.equal(game.blockCount(), 1);
  const block = game.blocks[0];
  game.ball.x = block.x + block.width / 2;
  game.ball.y = block.y + block.height / 2;
  game.ball.vx = 200;
  game.ball.vy = 0;
  game.moving = true;
  game.update(1 / 60);
  assert.equal(game.blockCount(), 0);
  assert.equal(game.won, true);
});

test("the ball bounces off the walls", () => {
  const game = createGame();
  game.ball.x = 10;
  game.ball.vx = -300;
  game.ball.vy = -100;
  game.moving = true;
  game.update(1 / 60);
  assert.equal(game.ball.vx > 0, true);
});

test("a ball that leaves the bottom resets", () => {
  const game = createGame();
  game.ball.y = game.height + 50;
  game.ball.vx = 0;
  game.ball.vy = 100;
  game.moving = true;
  game.update(1 / 60);
  assert.equal(game.moving, false);
  assert.equal(game.ball.y, game.height - 40);
});

test("the ball keeps only a part of its speed when it bounces", () => {
  const { createGame, RESTITUTION } = require("../public/logic");
  const game = createGame({ width: 640, height: 480 });
  game.ball.x = 2;
  game.ball.y = 240;
  game.ball.vx = -300;
  game.ball.vy = 0;
  game.moving = true;

  game.update(0.016);

  assert.ok(game.ball.vx > 0, "the ball bounces off the wall");
  assert.ok(game.ball.vx < 300, "the ball loses speed");
  assert.ok(Math.abs(game.ball.vx - 300 * RESTITUTION) < 1);
});

test("the ball loses speed over the time", () => {
  const { createGame } = require("../public/logic");
  const game = createGame({ width: 640, height: 480 });
  game.ball.x = 320;
  game.ball.y = 240;
  game.ball.vx = 200;
  game.ball.vy = 0;
  game.moving = true;

  const before = Math.hypot(game.ball.vx, game.ball.vy);
  game.update(0.5);
  const after = Math.hypot(game.ball.vx, game.ball.vy);

  assert.ok(after < before, "the ball has to lose speed");
});

test("the blocks that are hit are worth a point", () => {
  const { createGame } = require("../public/logic");
  const game = createGame({ width: 640, height: 480 });
  const block = game.blocks[0];
  game.ball.x = block.x + block.width / 2;
  game.ball.y = block.y + block.height / 2;
  game.ball.vx = 0;
  game.ball.vy = -200;
  game.moving = true;

  game.update(0.016);

  assert.ok(game.score > 0, "a block that is hit is worth a point");
});
