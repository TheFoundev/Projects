# Saleor

GraphQL-first commerce for growing catalogues

> GraphQL-first e-commerce platform with catalogue, checkout, order management, discounts, warehouses and an admin dashboard.

## Overview

An original, self-contained implementation of the **Saleor** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Product catalogue with stock and integer-cent pricing
- Session cart, stock validation and atomic checkout
- Orders with line-item snapshots
- Minimal GraphQL endpoint for products, orders and channels
- Server-rendered storefront and admin resource views

## Stack

`Python; Flask`
Flask + SQLite + Jinja. The CSV stack is Python + Flask.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://localhost:5000
pytest -q
```

## Structure

```text
saleor/
├── app.py               Flask routes, auth, JSON API and domain logic
├── config.json          resource schema and seed data
├── templates/           server-rendered Jinja views
├── static/style.css     responsive styling
├── tests/               pytest smoke test
└── data/app.db          local database (gitignored)
```

## Testing

```bash
pytest -q
```

12 tests: the storefront, the cart, the checkout (with an address, without one
and with the stock of the product) and the GraphQL endpoint (the fields that
are asked for, the variables and a broken query).

## Notes and limitations

- Payments are simulated; checkout validates and decrements stock in a transaction.
- The /graphql endpoint is deliberately small: it answers product, order and channel selections over the same schema, without a GraphQL runtime dependency.
- The upstream Saleor is Django + GraphQL + PostgreSQL; this Foundev MVP keeps the catalogue/checkout core runnable with Flask and SQLite.

## License

BSD-3-Clause. See `LICENSE`.
