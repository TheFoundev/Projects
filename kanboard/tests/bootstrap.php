<?php
declare(strict_types=1);

/**
 * Test bootstrap.
 *
 * Points the application at a throwaway SQLite database so the test run never
 * touches a real one.
 */

define('APP_ROOT', dirname(__DIR__));

$databasePath = sys_get_temp_dir() . '/kanban-test-' . bin2hex(random_bytes(6)) . '.sqlite';
putenv('APP_DSN=sqlite:' . $databasePath);
putenv('APP_SQLITE_PATH=' . $databasePath);

register_shutdown_function(static function () use ($databasePath) {
    if (is_file($databasePath)) @unlink($databasePath);
});

require_once APP_ROOT . '/src/Database.php';
require_once APP_ROOT . '/src/helpers.php';
require_once APP_ROOT . '/src/kanban.php';

$GLOBALS['kanban_failures'] = 0;
$GLOBALS['kanban_assertions'] = 0;

/** Assert that a condition holds. */
function assert_true($condition, string $message): void {
    $GLOBALS['kanban_assertions']++;
    if ($condition) {
        fwrite(STDOUT, "  ok   {$message}\n");
        return;
    }
    $GLOBALS['kanban_failures']++;
    fwrite(STDOUT, "  FAIL {$message}\n");
}

/** Assert that two values are equal. */
function assert_same($expected, $actual, string $message): void {
    $same = $expected === $actual;
    if (!$same) {
        $message .= sprintf(' (expected %s, got %s)', var_export($expected, true), var_export($actual, true));
    }
    assert_true($same, $message);
}

/** Assert that a string contains a substring. */
function assert_contains(string $haystack, string $needle, string $message): void {
    assert_true(str_contains($haystack, $needle), $message);
}

/** A database with a project and a few cards. */
function test_db(): Database {
    static $db = null;
    if ($db instanceof Database) return $db;

    $config = require APP_ROOT . '/config.php';
    $db = new Database($config['dsn']);
    $db->migrate($config);
    $db->pdo()->exec("INSERT INTO projects (name, description, status, owner, created_at) VALUES ('Website', '', 'active', 'Ana', '2026-04-01T00:00:00Z')");
    return $db;
}
