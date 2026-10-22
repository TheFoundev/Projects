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

/* ---------- the board ---------- */
if (($config['special'] ?? '') === 'kanban' && $path === '/board') {
    $user = require_user();
    $projects = $db->pdo()->query('SELECT * FROM projects ORDER BY name COLLATE NOCASE ASC')->fetchAll();
    $visible = array_values(array_filter($projects, fn($p) => kanban_can_view($p, $user)));
    $projectId = (int) ($_GET['project'] ?? ($visible[0]['id'] ?? 0));
    $current = null;
    foreach ($visible as $project) {
        if ((int) $project['id'] === $projectId) { $current = $project; break; }
    }
    $tasks = [];
    if ($current) {
        $stmt = $db->pdo()->prepare('SELECT * FROM tasks WHERE project_id = ?');
        $stmt->execute([$projectId]);
        $tasks = $stmt->fetchAll();
    }
    render('board', ['title' => 'Board', 'config' => $config, 'currentUser' => $user,
        'projects' => $visible, 'project' => $current, 'board' => kanban_board($tasks),
        'summary' => kanban_summary($tasks), 'lanes' => kanban_swimlanes($tasks)]);
    exit;
}

if (($config['special'] ?? '') === 'kanban' && $segments[0] === 'r' && ($segments[1] ?? '') === 'tasks'
    && isset($segments[3]) && $segments[3] === 'move' && $method === 'POST') {
    $user = require_user();
    check_csrf();
    $id = (int) $segments[2];
    $stmt = $db->pdo()->prepare('SELECT * FROM tasks WHERE id = ?');
    $stmt->execute([$id]);
    $task = $stmt->fetch();
    if (!$task) { http_response_code(404); exit('Card not found'); }

    $status = (string) ($_POST['status'] ?? '');
    $position = max(1, (int) ($_POST['position'] ?? 1));

    // The up and down buttons move the card one place inside its column.
    $action = (string) ($_POST['action'] ?? '');
    if ($action === 'up') $position = max(1, $position - 1);
    if ($action === 'down') $position = $position + 1;

    $stmt = $db->pdo()->prepare('SELECT * FROM tasks WHERE project_id = ?');
    $stmt->execute([(int) $task['project_id']]);
    $siblings = $stmt->fetchAll();

    $problem = kanban_validate_move($task, $status, $siblings);
    if ($problem) { flash($problem, 'error'); redirect('/board?project=' . (int) $task['project_id']); }

    $db->pdo()->beginTransaction();
    try {
        $cards = [];
        foreach ($siblings as $card) {
            if ((string) ($card['status'] ?? '') === $status) $cards[] = $card;
        }
        $moved = ['id' => $id, 'status' => $status, 'position' => $position];
        $cards[] = $moved;
        foreach (kanban_reorder($cards, $id, $position - 1) as $placement) {
            $db->pdo()->prepare('UPDATE tasks SET status = ?, position = ? WHERE id = ?')
                ->execute([$status, $placement['position'], $placement['id']]);
        }
        $db->pdo()->commit();
    } catch (Throwable $e) {
        $db->pdo()->rollBack();
        flash('The card could not be moved: ' . $e->getMessage(), 'error');
    }
    flash('Card moved.');
    redirect('/board?project=' . (int) $task['project_id']);
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
            if (($config['special'] ?? '') === 'kanban' && $resource['name'] === 'tasks') {
                $projects = $db->pdo()->query('SELECT * FROM projects')->fetchAll();
                $problem = kanban_validate_task($values, $projects);
                if ($problem) $errors[] = $problem;
                $values['position'] = kanban_next_position(
                    $db->pdo()->query('SELECT * FROM tasks WHERE project_id = ' . (int) ($values['project_id'] ?? 0))->fetchAll(),
                    (string) ($values['status'] ?? 'backlog')
                );
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
        if (($config['special'] ?? '') === 'kanban' && $resource['name'] === 'tasks') {
            $projects = $db->pdo()->query('SELECT * FROM projects')->fetchAll();
            $problem = kanban_validate_task($values + ['project_id' => $item['project_id']], $projects);
            if ($problem) $errors[] = $problem;
        }
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
