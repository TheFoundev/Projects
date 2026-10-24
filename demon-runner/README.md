# Demon-Runner

An endless runner where you dodge incoming demons.

> Endless runner game built with the Phaser framework playable in any browser; no hardware needed.

## Overview

An original, self-contained implementation of the **Demon-Runner** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Fixed-step game loop with jump physics and gravity
- Spawner that scales obstacle speed with distance
- Collision detection and score tracking
- HTML5 canvas rendering with a UMD logic module that tests can require

## Stack

`Node.js`
The CSV stack is Node.js. Phaser is not installed, so the game is drawn with the canvas 2D API directly, and the simulation lives in a UMD module that node:test can load.

## Run

```bash
npm start
npm test
```

## Structure

```text
demon-runner/
├── public/index.html        game page
├── public/game.js           canvas rendering and input
├── public/logic.js          UMD simulation module
├── src/server.js            static file server
├── test/logic.test.js       simulation tests
├── test/server.test.js      server tests
└── package.json
```

## Testing

```bash
npm test
```

10 tests (`npm test`), up from 6: the parallax layers, the legs of the runner and the dust.


## Notes and limitations

- Graphics are coloured rectangles, there are no sprites or audio.
- High scores only live in memory for the current tab.
- Only keyboard and pointer input are supported.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project. It targets Node's built-in modules and has no third-party runtime dependencies, so a few upstream conveniences are missing.
