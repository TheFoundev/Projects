# flick

A canvas flick-and-aim game about clearing blocks in one shot.

> Physics-based HTML5 mobile game where players flick objects at targets; browser only.

## Overview

An original, self-contained implementation of the **flick** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Aim and flick with a power value like a slingshot
- Bouncing projectile with wall reflection
- Blocks that are removed on contact
- HTML5 canvas rendering with a UMD logic module under test

## Stack

`Node.js`
The CSV stack is Node.js. Phaser is not installed, so the game uses the raw canvas 2D API and a UMD logic module that node:test can require.

## Run

```bash
npm start
npm test
```

## Structure

```text
flick/
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

10 tests (`npm test`), up from 7: the bounce, the friction and the score.


## Notes and limitations

- Physics are simplified: no rotation, spin or friction simulation.
- Levels are generated from a seeded pattern rather than a level editor.
- Sound and mobile game stores are out of scope.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project. It targets Node's built-in modules and has no third-party runtime dependencies, so a few upstream conveniences are missing.
