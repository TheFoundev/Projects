<?php
declare(strict_types=1);
if (PHP_SAPI === 'cli-server') {
    $file = __DIR__ . parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    if (is_file($file)) return false;
}
// The application root has to be known before the routes are loaded, because
// the routes use it to find the bootstrap file.
define('APP_ROOT', dirname(__DIR__));

session_start([
    'cookie_httponly' => true,
    'cookie_samesite' => 'Lax',
    'use_strict_mode' => true,
]);
require __DIR__ . '/../routes.php';
