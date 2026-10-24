<?php
/**
 * Create or update an administrator account.
 *
 * Usage:
 *   php scripts/create_admin.php <userid> [password]
 *
 * When the password is omitted it is read from the SRMS_ADMIN_PASSWORD
 * environment variable. If neither is given the script prompts for it.
 */

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit("This script must be run from the command line.\n");
}

require_once dirname(__DIR__) . '/init.php';

$userid = $argv[1] ?? '';
$password = $argv[2] ?? (getenv('SRMS_ADMIN_PASSWORD') ?: '');

if ($userid === '') {
    fwrite(STDERR, "Usage: php scripts/create_admin.php <userid> [password]\n");
    exit(1);
}

if ($password === '') {
    fwrite(STDERR, "Set SRMS_ADMIN_PASSWORD or pass the password as the second argument.\n");
    exit(1);
}

if (strlen($password) < 8) {
    fwrite(STDERR, "The password must be at least 8 characters long.\n");
    exit(1);
}

$hash = password_hash($password, PASSWORD_DEFAULT);

$existing = db_one('SELECT userid FROM admin_login WHERE userid = :userid', [':userid' => $userid]);
if ($existing === null) {
    db_query(
        'INSERT INTO admin_login (userid, password, password_hash) VALUES (:userid, NULL, :hash)',
        [':userid' => $userid, ':hash' => $hash]
    );
    fwrite(STDOUT, "Created administrator '{$userid}'.\n");
} else {
    db_query(
        'UPDATE admin_login SET password = NULL, password_hash = :hash WHERE userid = :userid',
        [':hash' => $hash, ':userid' => $userid]
    );
    fwrite(STDOUT, "Updated administrator '{$userid}'.\n");
}
