"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createGame, GROUND, PLAYER_SIZE } = require("../public/logic.js");

test("the player starts on the ground", () => {
  const game = createGame();
  assert.equal(game.player.y, GROUND - PLAYER_SIZE);
  assert.equal(game.player.onGround, true);
});

test("jumping leaves the ground and gravity brings it back", () => {
  const game = createGame();
  game.jump();
  assert.equal(game.player.onGround, false);
  assert.equal(game.player.vy < 0, true);
  for (let step = 0; step < 120; step++) {
    game.update(1 / 60);
  }
  assert.equal(game.player.onGround, true);
  assert.equal(game.player.y, GROUND - PLAYER_SIZE);
});

test("the score grows and speed increases over time", () => {
  const game = createGame({ spawnEvery: 100 });
  for (let step = 0; step < 60; step++) {
    game.update(1 / 60);
  }
  assert.equal(game.score > 0, true);
  assert.equal(game.speed > 260, true);
});

test("an obstacle hit ends the run", () => {
  const game = createGame({ speed: 260 });
  game.spawn();
  game.obstacles[0].x = game.player.x;
  game.update(1 / 60);
  assert.equal(game.over, true);
});

test("the run can be reset", () => {
  const game = createGame();
  game.spawn();
  game.obstacles[0].x = game.player.x;
  game.update(1 / 60);
  assert.equal(game.over, true);
  game.jump();
  assert.equal(game.over, false);
  assert.equal(game.obstacles.length, 0);
  assert.equal(game.score, 0);
});

test("the background moves with the game and the far layers the least", () => {
  const { createGame } = require("../public/logic");
  const game = createGame({ width: 800, seed: 3 });
  const before = game.layers.map((layer) => layer.x);

  game.update(0.5);

  const moved = game.layers.map((layer, index) => Math.abs(layer.x - before[index]));
  assert.ok(moved[0] > 0, "the background has to move");
  assert.ok(moved[0] < moved[2], "the far layer moves the least");
});

test("the legs of the runner move while it runs", () => {
  const { createGame } = require("../public/logic");
  const game = createGame({ width: 800, seed: 3 });

  const first = game.legPositions();
  game.update(0.2);
  const second = game.legPositions();

  assert.notEqual(first.swing, second.swing, "the legs have to move");
});

test("the runner makes dust when it lands", () => {
  const { createGame } = require("../public/logic");
  const game = createGame({ width: 800, seed: 3 });
  game.player.onGround = false;
  game.player.y = 0;
  game.player.vy = 900;

  game.update(0.2);

  assert.ok(game.dust.length > 0, "the runner has to make dust");
});

test("the dust goes away", () => {
  const { createGame } = require("../public/logic");
  const game = createGame({ width: 800, seed: 3 });
  game.player.onGround = false;
  game.player.y = 0;
  game.player.vy = 900;
  game.update(0.2);
  const count = game.dust.length;

  game.update(2);

  assert.ok(game.dust.length < count, "the dust has to go away");
});
