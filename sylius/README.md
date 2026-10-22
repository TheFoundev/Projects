# Sylius

An ecommerce core with a clear data model

> Ecommerce framework on Symfony with product variants, promotions, taxes, shipping, inventory and multi-channel sales.

## Overview

An original, self-contained implementation of the **Sylius** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Product catalogue with integer-cent prices and stock
- Session cart and transactional checkout
- Orders with line-item snapshots
- Promotions and sales channels as first-class records
- Owner/member accounts and a responsive storefront

## Stack

`PHP`
The application follows a small MVC structure (front controller, PDO models, PHP views) and uses PDO so the same code runs on SQLite locally and MySQL in production.

## Run

```bash
php -S localhost:8000 -t public
# open http://localhost:8000
```

## Structure

```text
sylius/
├── public/index.php     front controller (PHP built-in server router)
├── routes.php           HTTP routes and controllers
├── src/                 PDO database layer, helpers, bootstrap
├── views/               server-rendered templates
├── config.php           resources, seed data and DSN
└── data/app.sqlite      local database (gitignored)
```

## Testing

```bash
composer test      # or: php tests/run.php
```

The suite has no external dependency: the tests run against a SQLite database
of their own.


## Notes and limitations

- Promotions and channels are modelled and administered, but the checkout does not yet apply coupon codes or multi-currency conversion.
- Tax and shipping calculations are intentionally out of scope; totals are the sum of line items.
- The upstream Sylius is Symfony; this Foundev MVP follows the same PHP/PDO MVC shape with SQLite locally.

## License

MIT. See `LICENSE`.
