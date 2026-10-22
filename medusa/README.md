# Medusa

Composable commerce, small enough to read

> Composable headless commerce platform with products, carts, orders, inventory, promotions, regions and payment or shipping modules.

## Overview

An original, self-contained implementation of the **Medusa** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Product catalogue with integer-cent pricing
- Stock-aware cart and checkout
- Orders with line items and totals
- Categories and inventory in one place
- Dependency-free storefront UI

## Stack

`Node.js`
The app intentionally keeps a dependency-free Node stack; SQLite is provided by Node's built-in `node:sqlite` module (Node 22.5+).

## Run

```bash
npm start
# open http://localhost:3000
npm test
```

## Structure

```text
medusa/
├── server.js          HTTP API, auth and SQLite schema
├── config.json        domain model and seed data
├── public/            dependency-free single-page client
├── test/smoke.test.js API smoke test
└── data/app.db        local database (gitignored)
```

## Testing

```bash
npm test
```

5 domain tests (`npm test`), on top of the smoke test: the products, the checkout and the stock.


## Notes and limitations

- Payments are simulated: checkout marks an order paid and decrements stock atomically, but no card processor is contacted.
- Prices are stored as integer cents to avoid floating-point money bugs.
- The upstream Medusa is a Node/Postgres commerce platform; this MVP keeps the catalogue/cart/order core and uses SQLite for zero setup.

## License

MIT. See `LICENSE`.
