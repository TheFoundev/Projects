<?php
/**
 * Sign out.
 *
 * The session id is regenerated and the session data is cleared, so a
 * captured session cookie cannot be reused.
 */

declare(strict_types=1);

require_once __DIR__ . '/init.php';

$_SESSION = [];
if (ini_get('session.use_cookies')) {
    $params = session_get_cookie_params();
    setcookie(session_name(), '', [
        'expires' => time() - 42000,
        'path' => $params['path'],
        'domain' => $params['domain'],
        'secure' => $params['secure'],
        'httponly' => $params['httponly'],
        'samesite' => $params['samesite'] ?? 'Lax',
    ]);
}
session_destroy();

session_start();
flash('Logout successful.');
header('Location: login.php');
exit;
