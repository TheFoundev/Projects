<?php
/**
 * Test runner.
 *
 * Usage: php tests/run.php
 *
 * Runs the unit tests and the end to end tests in separate processes so the
 * database of one does not leak into the other.
 */

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    exit("This script must be run from the command line.\n");
}

$root = dirname(__DIR__);
$suites = [
    'unit' => $root . '/tests/unit_test.php',
    'http' => $root . '/tests/http_test.php',
];

$failed = 0;
foreach ($suites as $name => $path) {
    fwrite(STDOUT, "== {$name} ==\n");
    $command = escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($path);
    passthru($command, $exitCode);
    if ($exitCode !== 0) {
        $failed++;
    }
    fwrite(STDOUT, "\n");
}

if ($failed === 0) {
    fwrite(STDOUT, "All test suites passed.\n");
    exit(0);
}

fwrite(STDOUT, sprintf("%d test suite(s) failed.\n", $failed));
exit(1);
