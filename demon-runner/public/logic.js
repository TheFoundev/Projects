(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.DemonRunner = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const GROUND = 260;
  const PLAYER_SIZE = 28;
  const GRAVITY = 1900;
  const JUMP_SPEED = 620;
  // The layers of the background, the furthest one moves the slowest.
  const PARALLAX = [
    { factor: 0.15, height: 90, offset: 0 },
    { factor: 0.35, height: 130, offset: 40 },
    { factor: 0.6, height: 180, offset: 80 },
  ];

  function createGame(options) {
    const settings = Object.assign({ width: 800, speed: 260, spawnEvery: 1.1, seed: 1 }, options || {});
    let random = settings.seed >>> 0;
    const nextRandom = function () {
      random = (random * 1664525 + 1013904223) >>> 0;
      return random / 4294967296;
    };

    return {
      width: settings.width,
      ground: GROUND,
      player: { x: 90, y: GROUND - PLAYER_SIZE, size: PLAYER_SIZE, vy: 0, onGround: true },
      obstacles: [],
      // The layers of the background and the dust the runner makes.
      layers: PARALLAX.map((layer) => ({ ...layer, x: 0 })),
      dust: [],
      // The phase of the legs of the runner, so they move as it runs.
      stride: 0,
      speed: settings.speed,
      spawnEvery: settings.spawnEvery,
      spawnTimer: 0,
      elapsed: 0,
      score: 0,
      best: 0,
      over: false,
      nextRandom,

      jump() {
        if (this.over) {
          this.reset();
          return;
        }
        if (this.player.onGround) {
          this.player.vy = -JUMP_SPEED;
          this.player.onGround = false;
        }
      },

      /**
       * The legs of the runner.
       *
       * The phase goes with the distance, so the legs move faster when the
       * game is faster.
       */
      legPositions() {
        const swing = Math.sin(this.stride) * 0.7;
        return {
          front: { x: this.player.x + this.player.size * 0.75, y: this.player.y + this.player.size },
          back: { x: this.player.x + this.player.size * 0.25, y: this.player.y + this.player.size },
          swing,
        };
      },

      /** The dust the runner makes when it lands. */
      kickDust() {
        for (let index = 0; index < 6; index += 1) {
          this.dust.push({
            x: this.player.x + this.nextRandom() * this.player.size,
            y: GROUND - 2,
            vx: -40 - this.nextRandom() * 60,
            vy: -30 - this.nextRandom() * 50,
            life: 0.4 + this.nextRandom() * 0.3,
          });
        }
      },

      reset() {
        this.player.y = GROUND - this.player.size;
        this.player.vy = 0;
        this.player.onGround = true;
        this.obstacles = [];
        this.speed = settings.speed;
        this.spawnTimer = 0;
        this.elapsed = 0;
        this.score = 0;
        this.over = false;
      },

      spawn() {
        const height = 24 + Math.floor(this.nextRandom() * 30);
        this.obstacles.push({ x: this.width, y: GROUND - height, width: 22, height });
      },

      update(delta) {
        if (this.over) {
          return;
        }
        this.elapsed += delta;
        this.speed = settings.speed + this.elapsed * 12;
        this.score = Math.floor(this.elapsed * 10);
        this.best = Math.max(this.best, this.score);

        this.player.vy += GRAVITY * delta;
        this.player.y += this.player.vy * delta;
        const wasOnGround = this.player.onGround;
        if (this.player.y >= GROUND - this.player.size) {
          this.player.y = GROUND - this.player.size;
          this.player.vy = 0;
          this.player.onGround = true;
          if (!wasOnGround) {
            this.kickDust();
          }
        }

        // The legs move with the distance that is covered.
        this.stride += this.speed * delta * 0.05;

        // The background moves with the speed, the far layers the least.
        for (const layer of this.layers) {
          layer.x = (layer.x - this.speed * delta * layer.factor) % this.width;
        }

        // The dust falls and goes away.
        for (const particle of this.dust) {
          particle.x += particle.vx * delta;
          particle.y += particle.vy * delta;
          particle.vy += 260 * delta;
          particle.life -= delta;
        }
        this.dust = this.dust.filter((particle) => particle.life > 0);

        this.spawnTimer -= delta;
        if (this.spawnTimer <= 0) {
          this.spawn();
          this.spawnTimer = Math.max(0.4, this.spawnEvery - this.elapsed * 0.01);
        }

        for (const obstacle of this.obstacles) {
          obstacle.x -= this.speed * delta;
        }
        this.obstacles = this.obstacles.filter((obstacle) => obstacle.x + obstacle.width > 0);

        const player = this.player;
        for (const obstacle of this.obstacles) {
          if (
            player.x < obstacle.x + obstacle.width &&
            player.x + player.size > obstacle.x &&
            player.y < obstacle.y + obstacle.height &&
            player.y + player.size > obstacle.y
          ) {
            this.over = true;
          }
        }
      },
    };
  }

  return { createGame, GROUND, PLAYER_SIZE, GRAVITY, JUMP_SPEED, PARALLAX };
});
