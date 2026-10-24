<?php
/**
 * Tests for the short links.
 */

declare(strict_types=1);

$root = dirname(__DIR__);

// The database of the test is a file of its own.
$database = sys_get_temp_dir() . '/yourls-test-' . bin2hex(random_bytes(6)) . '.sqlite';
putenv('APP_SQLITE_PATH=' . $database);
putenv('APP_DSN=sqlite:' . $database);

require_once $root . '/src/bootstrap.php';
require_once $root . '/src/helpers.php';

$GLOBALS['failures'] = 0;
$GLOBALS['assertions'] = 0;

function check(bool $condition, string $message): void
{
    $GLOBALS['assertions']++;
    if ($condition) {
        fwrite(STDOUT, "  ok   {$message}\n");
        return;
    }
    $GLOBALS['failures']++;
    fwrite(STDOUT, "  FAIL {$message}\n");
}

$config = require $root . '/config.php';
$db = new Database($config['dsn']);
$db->migrate($config);

function slug_of(Database $db, string $slug): bool
{
    $stmt = $db->pdo()->prepare('SELECT COUNT(*) FROM links WHERE LOWER(slug) = ?');
    $stmt->execute([strtolower($slug)]);
    return (int) $stmt->fetchColumn() > 0;
}

$insert = $db->pdo()->prepare('INSERT INTO links (slug, target, title, tags, clicks, status, created_at) VALUES (?,?,?,?,?,?,?)');
$insert->execute(['demo', 'https://example.test', 'Demo', '', 0, 'active', gmdate('c')]);
check(slug_of($db, 'demo'), 'a link is stored');

// A slug may not be there twice.
try {
    $insert->execute(['demo', 'https://example.test', 'Demo', '', 0, 'active', gmdate('c')]);
    check(false, 'a slug that is taken is refused');
} catch (PDOException $exception) {
    check(true, 'a slug that is taken is refused');
}

// A slug of its own is fine.
$insert->execute(['other', 'https://example.test/other', 'Other', '', 0, 'active', gmdate('c')]);
check(slug_of($db, 'other'), 'a new slug is stored');

// The click counter of a link goes up when it is followed.
$link = $db->pdo()->query("SELECT * FROM links WHERE slug = 'demo'")->fetch();
$before = (int) $link['clicks'];
$db->pdo()->prepare('UPDATE links SET clicks = COALESCE(clicks,0) + 1 WHERE id = ?')->execute([$link['id']]);
$after = (int) $db->pdo()->query('SELECT clicks FROM links WHERE id = ' . (int) $link['id'])->fetchColumn();
check($after === $before + 1, 'the click counter goes up');

// The slug of a link is stored as it was given.
$stored = $db->pdo()->query("SELECT slug FROM links WHERE slug = 'other'")->fetchColumn();
check($stored === 'other', 'the slug is stored');

// The unique index is really there.
$indexes = $db->pdo()->query("PRAGMA index_list('links')")->fetchAll();
$unique = false;
foreach ($indexes as $index) {
    if (($index['name'] ?? '') === 'links_slug_unique' && (int) $index['unique'] === 1) {
        $unique = true;
    }
}
check($unique, 'the slug has a unique index');

@unlink($database);

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['assertions'], $GLOBALS['failures']));
exit($GLOBALS['failures'] === 0 ? 0 : 1);
