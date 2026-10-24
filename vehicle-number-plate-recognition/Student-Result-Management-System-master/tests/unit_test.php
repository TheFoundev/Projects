<?php
/**
 * Unit tests for the helpers in init.php and the security behaviour that does
 * not need a web server.
 */

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "unit tests\n");

// ---------------------------------------------------------------------------
// Escaping
// ---------------------------------------------------------------------------
assert_same(
    '&lt;script&gt;alert(1)&lt;/script&gt;',
    e('<script>alert(1)</script>'),
    'e() escapes angle brackets'
);
assert_same('&quot;x&quot; &amp; &#039;y&#039;', e('"x" & \'y\''), 'e() escapes quotes and ampersands');
assert_not_contains(e("' OR '1'='1"), "'", 'e() escapes single quotes');
assert_same('plain text', e('plain text'), 'e() leaves plain text alone');

// ---------------------------------------------------------------------------
// CSRF
// ---------------------------------------------------------------------------
reset_session_state();
$token = csrf_token();
assert_true(is_string($token) && strlen($token) === 64, 'csrf_token() returns a 32 byte hex token');
assert_same($token, csrf_token(), 'csrf_token() is stable within a session');
assert_true(csrf_valid($token), 'csrf_valid() accepts the session token');
assert_true(!csrf_valid('wrong-token'), 'csrf_valid() rejects a wrong token');
assert_true(!csrf_valid(null), 'csrf_valid() rejects a missing token');
assert_true(!csrf_valid(''), 'csrf_valid() rejects an empty token');
assert_not_contains(csrf_field(), 'value=""', 'csrf_field() renders a value');
assert_contains(csrf_field(), $token, 'csrf_field() embeds the token');

// A token from another session must not be accepted.
$other = bin2hex(random_bytes(32));
assert_true(!csrf_valid($other), 'csrf_valid() rejects a token from another session');

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------
$tables = array_map(
    static fn (array $row) => (string) $row['name'],
    db_all("SELECT name FROM sqlite_master WHERE type = 'table'")
);
foreach (['admin_login', 'class', 'students', 'result', 'login_attempts'] as $table) {
    assert_true(in_array($table, $tables, true), "schema creates the {$table} table");
}

// ---------------------------------------------------------------------------
// Prepared statements are not affected by injection attempts
// ---------------------------------------------------------------------------
db_query('INSERT INTO class (name, id) VALUES (:name, :id)', [':name' => "Robert'); DROP TABLE class;--", ':id' => 1]);
$classRow = db_one('SELECT name FROM class WHERE id = :id', [':id' => 1]);
assert_same("Robert'); DROP TABLE class;--", $classRow['name'] ?? null, 'a quote in a value is stored literally');
assert_true(in_array('class', array_map(
    static fn (array $row) => (string) $row['name'],
    db_all("SELECT name FROM sqlite_master WHERE type = 'table'")
), true), 'the class table still exists after an injection attempt');

$injected = db_one('SELECT name FROM class WHERE name = :name', [':name' => "' OR '1'='1"]);
assert_same(null, $injected, 'a classic injection payload matches no row');

// ---------------------------------------------------------------------------
// Password handling
// ---------------------------------------------------------------------------
$plain = 'correct-horse-battery';
$hash = password_hash($plain, PASSWORD_DEFAULT);
assert_true(password_verify($plain, $hash), 'password_verify accepts the right password');
assert_true(!password_verify('wrong', $hash), 'password_verify rejects a wrong password');
assert_not_contains($hash, $plain, 'the stored hash does not contain the plaintext');

make_admin('tester', $plain);
$account = db_one('SELECT password, password_hash FROM admin_login WHERE userid = :u', [':u' => 'tester']);
assert_same(null, $account['password'], 'a new account has no plaintext column value');
assert_true(!empty($account['password_hash']), 'a new account stores a password hash');
assert_true(str_starts_with((string) $account['password_hash'], '$2y$'), 'the hash is bcrypt');

// ---------------------------------------------------------------------------
// Session helpers
// ---------------------------------------------------------------------------
reset_session_state();
$_SESSION['flash'] = ['message' => 'saved', 'kind' => 'success'];
$flash = take_flash();
assert_same('saved', $flash['message'] ?? null, 'take_flash() returns the pending message');
assert_same(null, take_flash(), 'take_flash() clears the message');
assert_same('', render_flash(), 'render_flash() is empty without a message');

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
fwrite(STDOUT, sprintf(
    "%d assertions, %d failures\n",
    $GLOBALS['srms_test_assertions'],
    $GLOBALS['srms_test_failures']
));

exit($GLOBALS['srms_test_failures'] === 0 ? 0 : 1);
