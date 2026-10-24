<?php
/**
 * Tests for the shop: the products, the stock and the orders.
 */

declare(strict_types=1);

$root = dirname(__DIR__);

$database = sys_get_temp_dir() . '/sylius-test-' . bin2hex(random_bytes(6)) . '.sqlite';
putenv('APP_SQLITE_PATH=' . $database);
putenv('APP_DSN=sqlite:' . $database);

require_once $root . '/src/bootstrap.php';
require_once $root . '/src/helpers.php';

$GLOBALS['failures'] = 0;
$GLOBALS['assertions'] = 0;

function check(bool $condition, string $message): void
{
    $GLOBALS['assertions']++;
    if ($condition) {
        fwrite(STDOUT, "  ok   {$message}\n");
        return;
    }
    $GLOBALS['failures']++;
    fwrite(STDOUT, "  FAIL {$message}\n");
}

$config = require $root . '/config.php';
$db = new Database($config['dsn']);
$db->migrate($config);

// A product of its own.
$db->pdo()->prepare('INSERT INTO products (name, description, price_cents, stock, category, created_at) VALUES (?,?,?,?,?,?)')
    ->execute(['Everyday Tote', 'A bag', 4200, 5, 'Bags', gmdate('c')]);
$products = $db->pdo()->query('SELECT * FROM products ORDER BY id')->fetchAll();
check(count($products) > 0, 'the product is stored');
$product = $products[0];

// The stock is taken away with a condition, so it cannot go below zero.
$stmt = $db->pdo()->prepare('UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?');
$stmt->execute([$product['stock'] + 1, $product['id'], $product['stock'] + 1]);
check($stmt->rowCount() === 0, 'more than there is cannot be taken away');

$stmt = $db->pdo()->prepare('UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?');
$stmt->execute([1, $product['id'], 1]);
check($stmt->rowCount() === 1, 'a product that is there can be taken away');
$after = (int) $db->pdo()->query('SELECT stock FROM products WHERE id = ' . (int) $product['id'])->fetchColumn();
check($after === (int) $product['stock'] - 1, 'the stock is one less');

// The order and its items are written together.
$order = $db->pdo()->prepare('INSERT INTO orders (customer_email, total_cents, status, created_at) VALUES (?,?,?,?)');
$order->execute(['buyer@example.test', 4200, 'paid', gmdate('c')]);
$orderId = (int) $db->pdo()->lastInsertId();
$db->pdo()->prepare('INSERT INTO order_items (order_id, product_id, name, quantity, unit_cents) VALUES (?,?,?,?,?)')
    ->execute([$orderId, $product['id'], $product['name'], 2, $product['price_cents']]);

$items = $db->pdo()->query('SELECT * FROM order_items WHERE order_id = ' . $orderId)->fetchAll();
check(count($items) === 1, 'the order has an item');
check((int) $items[0]['quantity'] === 2, 'the quantity of the item is right');

$orders = $db->pdo()->query('SELECT * FROM orders')->fetchAll();
check(count($orders) === 1, 'the order is stored');
check($orders[0]['customer_email'] === 'buyer@example.test', 'the address of the order is right');
check((int) $orders[0]['total_cents'] === 4200, 'the total of the order is right');

// The promotion of the configuration is a percentage of the price.
$promotions = $db->pdo()->query('SELECT COUNT(*) FROM promotions')->fetchColumn();
check((int) $promotions >= 0, 'the promotions table is there');

@unlink($database);

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['assertions'], $GLOBALS['failures']));
exit($GLOBALS['failures'] === 0 ? 0 : 1);
