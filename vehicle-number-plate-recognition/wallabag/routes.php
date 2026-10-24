<?php
declare(strict_types=1);

require APP_ROOT . '/src/bootstrap.php';

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$path = rtrim($path, '/') ?: '/';
$segments = $path === '/' ? [] : explode('/', trim($path, '/'));

function find_resource(array $config, string $name): ?array {
    foreach ($config['resources'] as $resource) if ($resource['name'] === $name) return $resource;
    return null;
}

function list_rows(Database $db, array $resource, string $query = ''): array {
    $sql = 'SELECT * FROM "' . $resource['name'] . '"';
    $params = [];
    if ($query !== '') {
        $textFields = [];
        foreach ($resource['fields'] as $name => $field) if (($field['type'] ?? 'text') === 'text') $textFields[] = $name;
        if ($textFields) {
            $sql .= ' WHERE ' . implode(' OR ', array_map(fn($f) => '"' . $f . '" LIKE ?', $textFields));
            $params = array_fill(0, count($textFields), '%' . $query . '%');
        }
    }
    $sql .= ' ORDER BY id DESC LIMIT 200';
    $stmt = $db->pdo()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

/* ---------- auth ---------- */
if ($path === '/login') {
    if ($currentUser) redirect('/');
    if ($method === 'POST') {
        check_csrf();
        $stmt = $db->pdo()->prepare('SELECT * FROM users WHERE email = ?');
        $stmt->execute([strtolower(trim($_POST['email'] ?? ''))]);
        $user = $stmt->fetch();
        if ($user && password_verify($_POST['password'] ?? '', $user['password'])) {
            session_regenerate_id(true);
            $_SESSION['user_id'] = (int) $user['id'];
            flash('Welcome back, ' . $user['name']);
            redirect('/');
        }
        flash('Invalid email or password.', 'error');
        redirect('/login');
    }
    render('login', ['title' => 'Sign in', 'config' => $config, 'currentUser' => $currentUser]);
    exit;
}

if ($path === '/register') {
    if ($currentUser) redirect('/');
    if ($method === 'POST') {
        check_csrf();
        $name = trim($_POST['name'] ?? '');
        $email = strtolower(trim($_POST['email'] ?? ''));
        $password = $_POST['password'] ?? '';
        if ($name === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($password) < 8) {
            flash('Name, a valid email and an 8+ character password are required.', 'error');
            redirect('/register');
        }
        $count = (int) $db->pdo()->query('SELECT COUNT(*) FROM users')->fetchColumn();
        try {
            $stmt = $db->pdo()->prepare('INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)');
            $stmt->execute([$name, $email, password_hash($password, PASSWORD_DEFAULT), $count === 0 ? 'owner' : 'member', gmdate('c')]);
        } catch (PDOException $e) {
            flash('That email is already registered.', 'error');
            redirect('/register');
        }
        $_SESSION['user_id'] = (int) $db->pdo()->lastInsertId();
        flash('Account created.');
        redirect('/');
    }
    render('register', ['title' => 'Create account', 'config' => $config, 'currentUser' => $currentUser]);
    exit;
}

if ($path === '/logout' && $method === 'POST') {
    check_csrf();
    session_destroy();
    redirect('/');
}

/* ---------- commerce storefront ---------- */
if (($config['special'] ?? '') === 'commerce') {
    function cart_items(Database $db): array {
        $cart = $_SESSION['cart'] ?? [];
        $items = []; $total = 0;
        foreach ($cart as $pid => $qty) {
            $stmt = $db->pdo()->prepare('SELECT * FROM products WHERE id = ?');
            $stmt->execute([(int) $pid]);
            $product = $stmt->fetch();
            if (!$product) { unset($cart[$pid]); continue; }
            $qty = max(1, min((int) $qty, (int) $product['stock']));
            if ($qty < 1) { unset($cart[$pid]); continue; }
            $cart[$pid] = $qty;
            $line = (int) $product['price_cents'] * $qty;
            $total += $line;
            $items[] = ['product' => $product, 'quantity' => $qty, 'line_cents' => $line];
        }
        $_SESSION['cart'] = $cart;
        return [$items, $total];
    }

    if ($path === '/store' && $method === 'GET') {
        $products = $db->pdo()->query('SELECT * FROM products ORDER BY id')->fetchAll();
        render('store', ['title' => 'Store', 'config' => $config, 'currentUser' => $currentUser, 'products' => $products]);
        exit;
    }

    if (count($segments) === 3 && $segments[0] === 'cart' && $segments[1] === 'add' && $method === 'POST') {
        check_csrf();
        $pid = (int) $segments[2];
        $stmt = $db->pdo()->prepare('SELECT * FROM products WHERE id = ?');
        $stmt->execute([$pid]);
        $product = $stmt->fetch();
        if (!$product || (int) $product['stock'] < 1) { flash('That product is unavailable.', 'error'); redirect('/store'); }
        $cart = $_SESSION['cart'] ?? [];
        $cart[$pid] = min(($cart[$pid] ?? 0) + 1, (int) $product['stock']);
        $_SESSION['cart'] = $cart;
        flash($product['name'] . ' added to cart.');
        redirect('/store');
    }

    if ($path === '/cart' && $method === 'GET') {
        [$items, $total] = cart_items($db);
        render('cart', ['title' => 'Cart', 'config' => $config, 'currentUser' => $currentUser, 'items' => $items, 'total' => $total]);
        exit;
    }

    if (count($segments) === 3 && $segments[0] === 'cart' && $segments[1] === 'remove' && $method === 'POST') {
        check_csrf();
        $cart = $_SESSION['cart'] ?? [];
        unset($cart[(int) $segments[2]]);
        $_SESSION['cart'] = $cart;
        redirect('/cart');
    }

    if ($path === '/checkout' && $method === 'POST') {
        check_csrf();
        $email = trim($_POST['email'] ?? '');
        [$items, $total] = cart_items($db);
        if (!$items) { flash('Your cart is empty.', 'error'); redirect('/cart'); }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) { flash('A valid email is required.', 'error'); redirect('/cart'); }
        try {
            $db->pdo()->beginTransaction();
            foreach ($items as $item) {
                $stock = (int) $db->pdo()->query('SELECT stock FROM products WHERE id = ' . (int) $item['product']['id'])->fetchColumn();
                if ($stock < (int) $item['quantity']) throw new RuntimeException($item['product']['name'] . ' no longer has enough stock.');
            }
            $stmt = $db->pdo()->prepare('INSERT INTO orders (customer_email, total_cents, status, created_at) VALUES (?, ?, ?, ?)');
            $stmt->execute([$email, $total, 'paid', gmdate('c')]);
            $orderId = (int) $db->pdo()->lastInsertId();
            $lineStmt = $db->pdo()->prepare('INSERT INTO order_items (order_id, product_id, name, quantity, unit_cents) VALUES (?, ?, ?, ?, ?)');
            $stockStmt = $db->pdo()->prepare('UPDATE products SET stock = stock - ? WHERE id = ?');
            foreach ($items as $item) {
                $lineStmt->execute([$orderId, $item['product']['id'], $item['product']['name'], $item['quantity'], $item['product']['price_cents']]);
                $stockStmt->execute([$item['quantity'], $item['product']['id']]);
            }
            $db->pdo()->commit();
            $_SESSION['cart'] = [];
            flash('Order #' . $orderId . ' confirmed for $' . number_format($total / 100, 2) . '.');
            redirect('/');
        } catch (Throwable $e) {
            if ($db->pdo()->inTransaction()) $db->pdo()->rollBack();
            flash($e->getMessage(), 'error');
            redirect('/cart');
        }
    }
}

/* ---------- short links ---------- */
if (($config['special'] ?? '') === 'shortener' && count($segments) === 2 && $segments[0] === 'r' && $method === 'GET') {
    $stmt = $db->pdo()->prepare('SELECT * FROM links WHERE slug = ?');
    $stmt->execute([$segments[1]]);
    $link = $stmt->fetch();
    if ($link) {
        $db->pdo()->prepare('UPDATE links SET clicks = COALESCE(clicks,0) + 1 WHERE id = ?')->execute([$link['id']]);
        header('Location: ' . $link['target'], true, 302);
        exit;
    }
    http_response_code(404); echo 'Unknown short link'; exit;
}

/* ---------- pretty wiki page ---------- */
if (($config['special'] ?? '') === 'wiki' && count($segments) === 2 && $segments[0] === 'pages' && $method === 'GET') {
    $stmt = $db->pdo()->prepare('SELECT * FROM pages WHERE id = ?');
    $stmt->execute([(int) $segments[1]]);
    $page = $stmt->fetch();
    if (!$page) { http_response_code(404); exit('Page not found'); }
    $stmt = $db->pdo()->prepare('SELECT * FROM revisions WHERE page_id = ? ORDER BY id DESC');
    $stmt->execute([(int) $page['id']]);
    render('page', ['title' => $page['title'], 'config' => $config, 'currentUser' => $currentUser, 'page' => $page, 'revisions' => $stmt->fetchAll()]);
    exit;
}

/* ---------- home ---------- */
if ($path === '/') {
    $counts = []; $labels = [];
    foreach ($config['resources'] as $resource) {
        $counts[$resource['name']] = (int) $db->pdo()->query('SELECT COUNT(*) FROM "' . $resource['name'] . '"')->fetchColumn();
        $labels[$resource['name']] = $resource['label'];
    }
    render('home', ['title' => 'Dashboard', 'config' => $config, 'currentUser' => $currentUser, 'counts' => $counts, 'labels' => $labels]);
    exit;
}

/* ---------- the reading list ---------- */
if (($config['special'] ?? '') === 'readlater' && $path === '/reading') {
    $user = require_user();
    $articles = $db->pdo()->query('SELECT * FROM articles')->fetchAll();
    $filters = [
        'status' => $_GET['status'] ?? null,
        'tag' => $_GET['tag'] ?? null,
        'q' => $_GET['q'] ?? null,
    ];
    $sort = (string) ($_GET['sort'] ?? 'added');
    $items = reader_list($articles, $filters, $sort);
    render('reading', ['title' => 'Reading list', 'config' => $config, 'currentUser' => $user,
        'items' => $items, 'counts' => reader_counts($articles), 'cloud' => reader_tag_cloud($articles),
        'filters' => $filters, 'sort' => $sort]);
    exit;
}

if (($config['special'] ?? '') === 'readlater' && count($segments) === 3 && $segments[0] === 'articles'
    && $segments[2] === 'annotations' && $method === 'GET') {
    $article = $db->pdo()->prepare('SELECT * FROM articles WHERE id = ?');
    $article->execute([(int) $segments[1]]);
    $row = $article->fetch();
    if (!$row) { http_response_code(404); exit('Article not found'); }
    $annotations = $db->pdo()->query('SELECT * FROM annotations')->fetchAll();
    return json_response(['annotations' => reader_annotations_of((int) $row['id'], $annotations)]);
}

if (($config['special'] ?? '') === 'readlater' && count($segments) === 3 && $segments[0] === 'articles'
    && $segments[2] === 'extract' && $method === 'POST') {
    $user = require_user();
    check_csrf();
    $url = trim((string) ($_POST['url'] ?? ''));
    if (!preg_match('#^https?://#i', $url)) { flash('The url has to start with http:// or https://.', 'error'); redirect('/reading'); }
    $extracted = ['title' => '', 'author' => '', 'excerpt' => '', 'content' => ''];
    try {
        $html = fetch_url($url);
        if (preg_match('/<title[^>]*>(.*?)<\/title>/is', $html, $m) === 1) {
            $extracted['title'] = trim(html_entity_decode($m[1], ENT_QUOTES, 'UTF-8'));
        }
        if (preg_match('/<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)/i', $html, $m) === 1) {
            $extracted['author'] = trim($m[1]);
        }
        if (preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)/i', $html, $m) === 1) {
            $extracted['excerpt'] = trim($m[1]);
        }
        if (preg_match('/<article[^>]*>(.*?)<\/article>/is', $html, $m) === 1) {
            $extracted['content'] = trim($m[1]);
        } elseif (preg_match('/<body[^>]*>(.*?)<\/body>/is', $html, $m) === 1) {
            $extracted['content'] = trim($m[1]);
        }
    } catch (Throwable $e) {
        flash('Could not fetch the page: ' . $e->getMessage(), 'error');
        redirect('/reading');
    }
    $extracted['site'] = reader_site_of($url);
    if ($extracted['excerpt'] === '') $extracted['excerpt'] = reader_excerpt_of($extracted['content']);
    render('form', ['title' => 'Save the article', 'config' => $config, 'currentUser' => $user,
        'resource' => find_resource($config, 'articles'), 'item' => $extracted + ['url' => $url],
        'errors' => []]);
    exit;
}

/* ---------- resources ---------- */
if ($segments[0] === 'r' && isset($segments[1])) {
    $resource = find_resource($config, $segments[1]);
    if (!$resource) { http_response_code(404); exit('Unknown resource'); }
    $table = '"' . $resource['name'] . '"';

    if (!isset($segments[2])) {
        $items = list_rows($db, $resource, trim($_GET['q'] ?? ''));
        render('list', ['title' => $resource['label'], 'config' => $config, 'currentUser' => $currentUser,
            'resource' => $resource, 'items' => $items]);
        exit;
    }

    if ($segments[2] === 'new') {
        $user = require_user();
        if ($method === 'POST') {
            check_csrf();
            [$values, $errors] = validate_resource($resource, $_POST);
            if (($config['special'] ?? '') === 'readlater') {
                if ($resource['name'] === 'articles') {
                    // The site, the excerpt and the date are filled in before
                    // the article is checked, so a saved link only needs a
                    // title and an url.
                    if (($values['site'] ?? '') === '' && !empty($values['url'])) {
                        $values['site'] = reader_site_of((string) $values['url']);
                    }
                    if (($values['excerpt'] ?? '') === '' && !empty($values['content'])) {
                        $values['excerpt'] = reader_excerpt_of((string) $values['content']);
                    }
                    if (($values['added_at'] ?? '') === '') $values['added_at'] = gmdate('c');
                    $problem = reader_check_article($values);
                    if ($problem) $errors[] = $problem;
                }
                if ($resource['name'] === 'annotations') {
                    $problem = reader_check_annotation($values, $db->pdo()->query('SELECT * FROM articles')->fetchAll());
                    if ($problem) $errors[] = $problem;
                }
            }
            if ($errors) {
                render('form', ['title' => 'New ' . $resource['label'], 'config' => $config, 'currentUser' => $user,
                    'resource' => $resource, 'item' => $_POST, 'errors' => $errors]);
                exit;
            }
            $keys = array_keys($values);
            $cols = implode(',', array_map(fn($k) => '"' . $k . '"', $keys));
            $marks = implode(',', array_fill(0, count($keys), '?'));
            $stmt = $db->pdo()->prepare('INSERT INTO ' . $table . ' (' . $cols . ', created_at) VALUES (' . $marks . ', ?)');
            $stmt->execute([...array_values($values), gmdate('c')]);
            $id = (int) $db->pdo()->lastInsertId();
            flash($resource['label'] . ' created.');
            if (($config['special'] ?? '') === 'wiki' && $resource['name'] === 'pages') redirect('/pages/' . $id);
            redirect('/r/' . $resource['name']);
        }
        render('form', ['title' => 'New ' . $resource['label'], 'config' => $config, 'currentUser' => $user,
            'resource' => $resource, 'item' => [], 'errors' => []]);
        exit;
    }

    $id = (int) $segments[2];
    if (isset($segments[3]) && $segments[3] === 'delete' && $method === 'POST') {
        $user = require_user();
        check_csrf();
        $db->pdo()->prepare('DELETE FROM ' . $table . ' WHERE id = ?')->execute([$id]);
        flash('Record deleted.');
        redirect('/r/' . $resource['name']);
    }

    $stmt = $db->pdo()->prepare('SELECT * FROM ' . $table . ' WHERE id = ?');
    $stmt->execute([$id]);
    $item = $stmt->fetch();
    if (!$item) { http_response_code(404); exit('Record not found'); }

    $user = require_user();
    if ($method === 'POST') {
        check_csrf();
        [$values, $errors] = validate_resource($resource, $_POST);
        if ($errors) {
            render('form', ['title' => 'Edit ' . $resource['label'], 'config' => $config, 'currentUser' => $user,
                'resource' => $resource, 'item' => array_merge($item, $_POST), 'errors' => $errors]);
            exit;
        }
        if (($config['special'] ?? '') === 'wiki' && $resource['name'] === 'pages') {
            $version = (int) ($item['version'] ?? 1);
            $db->pdo()->prepare('INSERT INTO revisions (page_id, title, body, version, created_at) VALUES (?, ?, ?, ?, ?)')
                ->execute([$id, $item['title'], $item['body'], $version, gmdate('c')]);
            $values['version'] = $version + 1;
        }
        $keys = array_keys($values);
        $set = implode(',', array_map(fn($k) => '"' . $k . '" = ?', $keys));
        $stmt = $db->pdo()->prepare('UPDATE ' . $table . ' SET ' . $set . ' WHERE id = ?');
        $stmt->execute([...array_values($values), $id]);
        flash('Changes saved.');
        if (($config['special'] ?? '') === 'wiki' && $resource['name'] === 'pages') redirect('/pages/' . $id);
        redirect('/r/' . $resource['name']);
    }

    render('form', ['title' => 'Edit ' . $resource['label'], 'config' => $config, 'currentUser' => $user,
        'resource' => $resource, 'item' => $item, 'errors' => []]);
    exit;
}

http_response_code(404);
echo 'Not found';
