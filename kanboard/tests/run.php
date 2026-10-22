<?php
/**
 * Test runner.
 *
 * Usage: php tests/run.php
 */

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    exit("This script must be run from the command line.\n");
}

$root = dirname(__DIR__);
$suites = [
    'kanban' => $root . '/tests/kanban.test.php',
    'http' => $root . '/tests/http.test.php',
];

$failed = 0;
foreach ($suites as $name => $path) {
    fwrite(STDOUT, "== {$name} ==\n");
    passthru(escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($path), $exitCode);
    if ($exitCode !== 0) $failed++;
    fwrite(STDOUT, "\n");
}

if ($failed === 0) {
    fwrite(STDOUT, "All test suites passed.\n");
    exit(0);
}

fwrite(STDOUT, sprintf("%d test suite(s) failed.\n", $failed));
exit(1);
