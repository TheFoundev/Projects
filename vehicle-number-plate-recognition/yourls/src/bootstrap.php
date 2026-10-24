<?php
declare(strict_types=1);

if (!defined('APP_ROOT')) define('APP_ROOT', __DIR__ . '/..');
require APP_ROOT . '/src/Database.php';
require APP_ROOT . '/src/helpers.php';

$config = require APP_ROOT . '/config.php';
$db = new Database($config['dsn'], $config['db_user'] ?? null, $config['db_pass'] ?? null);
$db->migrate($config);
$currentUser = current_user($db);

function current_user(Database $db): ?array {
    if (empty($_SESSION['user_id'])) return null;
    $stmt = $db->pdo()->prepare('SELECT id, name, email, role FROM users WHERE id = ?');
    $stmt->execute([$_SESSION['user_id']]);
    $user = $stmt->fetch();
    return $user ?: null;
}

function require_user(): array {
    global $currentUser;
    if (!$currentUser) {
        header('Location: /login');
        exit;
    }
    return $currentUser;
}

function csrf_token(): string {
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(24));
    return $_SESSION['csrf'];
}

function check_csrf(): void {
    $token = $_POST['csrf'] ?? '';
    if (!is_string($token) || !hash_equals($_SESSION['csrf'] ?? '', $token)) {
        http_response_code(419);
        exit('Invalid CSRF token. Go back and try again.');
    }
}
