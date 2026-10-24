(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.FlickGame = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const BALL_RADIUS = 9;
  const BLOCK_SIZE = 34;
  const MAX_SPEED = 640;
  // How much of the speed the ball keeps when it bounces.
  const RESTITUTION = 0.96;
  // How fast the ball loses speed over a second.
  const FRICTION = 0.12;
  // How much a block turns when the ball hits it.
  const SPIN = 4.2;

  function buildBlocks(width, rows, columns, seed) {
    let random = (seed >>> 0) || 1;
    const nextRandom = function () {
      random = (random * 1103515245 + 12345) >>> 0;
      return random / 4294967296;
    };
    const blocks = [];
    const margin = 40;
    const gap = 6;
    const used = columns * (BLOCK_SIZE + gap);
    const startX = Math.max(margin, (width - used) / 2);
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        if (nextRandom() < 0.15) {
          continue;
        }
        blocks.push({
          x: startX + column * (BLOCK_SIZE + gap),
          y: 50 + row * (BLOCK_SIZE + gap),
          width: BLOCK_SIZE,
          height: BLOCK_SIZE,
        });
      }
    }
    return blocks;
  }

  function createGame(options) {
    const settings = Object.assign({ width: 640, height: 480, rows: 5, columns: 9, seed: 7 }, options || {});
    return {
      width: settings.width,
      height: settings.height,
      ball: { x: settings.width / 2, y: settings.height - 40, vx: 0, vy: 0, radius: BALL_RADIUS },
      blocks: buildBlocks(settings.width, settings.rows, settings.columns, settings.seed),
      // The score of the run and the number of the blocks that are left.
      score: 0,
      rotations: 0,
      aiming: false,
      aim: { x: 0, y: 0 },
      speed: 0,
      moving: false,
      flicks: 0,
      won: false,

      blockCount() {
        return this.blocks.length;
      },

      startAim(x, y) {
        if (this.moving || this.won) {
          return;
        }
        this.aiming = true;
        this.aim = { x, y };
      },

      updateAim(x, y) {
        if (this.aiming) {
          this.aim = { x, y };
        }
      },

      release() {
        if (!this.aiming) {
          return false;
        }
        this.aiming = false;
        const dx = this.ball.x - this.aim.x;
        const dy = this.ball.y - this.aim.y;
        const distance = Math.hypot(dx, dy);
        if (distance < 5) {
          return false;
        }
        const power = Math.min(distance, 200) / 200;
        this.speed = MAX_SPEED * power;
        this.ball.vx = (dx / distance) * this.speed;
        this.ball.vy = (dy / distance) * this.speed;
        this.moving = true;
        this.flicks += 1;
        return true;
      },

      update(delta) {
        if (!this.moving) {
          return;
        }
        const ball = this.ball;
        ball.x += ball.vx * delta;
        ball.y += ball.vy * delta;

        if (ball.x - ball.radius < 0) {
          ball.x = ball.radius;
          ball.vx = Math.abs(ball.vx) * RESTITUTION;
          this.rotations += 1;
        }
        if (ball.x + ball.radius > this.width) {
          ball.x = this.width - ball.radius;
          ball.vx = -Math.abs(ball.vx) * RESTITUTION;
          this.rotations += 1;
        }
        if (ball.y - ball.radius < 0) {
          ball.y = ball.radius;
          ball.vy = Math.abs(ball.vy) * RESTITUTION;
          this.rotations += 1;
        }
        if (ball.y - ball.radius > this.height) {
          this.resetBall();
          return;
        }

        this.blocks = this.blocks.filter((block) => {
          const hit =
            ball.x + ball.radius > block.x &&
            ball.x - ball.radius < block.x + block.width &&
            ball.y + ball.radius > block.y &&
            ball.y - ball.radius < block.y + block.height;
          if (hit) {
            const overlapX = Math.min(ball.x + ball.radius - block.x, block.x + block.width - (ball.x - ball.radius));
            const overlapY = Math.min(ball.y + ball.radius - block.y, block.y + block.height - (ball.y - ball.radius));
            if (overlapX < overlapY) {
              ball.vx = -ball.vx * RESTITUTION;
              this.rotations += 1;
            } else {
              ball.vy = -ball.vy * RESTITUTION;
              this.rotations += 1;
            }
          }
          return !hit;
        });

        // The ball loses a little speed every second and keeps a part of
        // its speed when it bounces.
        const speed = Math.hypot(ball.vx, ball.vy);
        if (speed > 1) {
          const keep = Math.max(0, 1 - FRICTION * delta);
          ball.vx *= keep;
          ball.vy *= keep;
        }
        if (speed < 40) {
          this.resetBall();
          return;
        }
        // A block that is hit is worth a point, and the blocks that are
        // left are worth more.
        this.score = (this.score || 0) + 1;
        if (this.blocks.length === 0) {
          this.moving = false;
          this.won = true;
        }
      },

      resetBall() {
        this.ball.x = this.width / 2;
        this.ball.y = this.height - 40;
        this.ball.vx = 0;
        this.ball.vy = 0;
        this.moving = false;
      },
    };
  }

  return {
    createGame,
    buildBlocks,
    BALL_RADIUS,
    BLOCK_SIZE,
    MAX_SPEED,
    RESTITUTION,
    FRICTION,
    SPIN,
  };
});
