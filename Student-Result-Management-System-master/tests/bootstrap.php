<?php
/**
 * Test bootstrap.
 *
 * Points the application at a throwaway SQLite database so the test run never
 * touches a real one.
 */

declare(strict_types=1);

$databasePath = sys_get_temp_dir() . '/srms-test-' . bin2hex(random_bytes(6)) . '.sqlite';
putenv('SRMS_SQLITE_PATH=' . $databasePath);
putenv('SRMS_DSN');

register_shutdown_function(static function () use ($databasePath) {
    if (is_file($databasePath)) {
        @unlink($databasePath);
    }
});

require_once dirname(__DIR__) . '/init.php';

$GLOBALS['srms_test_failures'] = 0;
$GLOBALS['srms_test_assertions'] = 0;
$GLOBALS['srms_test_database'] = $databasePath;

/** Assert that a condition holds. */
function assert_true($condition, string $message): void
{
    $GLOBALS['srms_test_assertions']++;
    if ($condition) {
        fwrite(STDOUT, "  ok   {$message}\n");

        return;
    }
    $GLOBALS['srms_test_failures']++;
    fwrite(STDOUT, "  FAIL {$message}\n");
}

/** Assert that two values are equal. */
function assert_same($expected, $actual, string $message): void
{
    $same = $expected === $actual;
    if (!$same) {
        $message .= sprintf(' (expected %s, got %s)', var_export($expected, true), var_export($actual, true));
    }
    assert_true($same, $message);
}

/** Assert that a string contains a substring. */
function assert_contains(string $haystack, string $needle, string $message): void
{
    assert_true(str_contains($haystack, $needle), $message);
}

/** Assert that a string does not contain a substring. */
function assert_not_contains(string $haystack, string $needle, string $message): void
{
    assert_true(!str_contains($haystack, $needle), $message);
}

/** Create an administrator with a known password. */
function make_admin(string $userid = 'admin', string $password = 'correct-horse'): string
{
    $hash = password_hash($password, PASSWORD_DEFAULT);
    db_query(
        'INSERT INTO admin_login (userid, password, password_hash) VALUES (:userid, NULL, :hash)',
        [':userid' => $userid, ':hash' => $hash]
    );

    return $password;
}

/** Reset the request-scoped state between unit tests. */
function reset_session_state(): void
{
    $_SESSION = [];
    $_POST = [];
    $_SERVER['REQUEST_METHOD'] = 'GET';
}
