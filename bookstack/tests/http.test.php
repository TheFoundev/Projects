<?php
declare(strict_types=1);

/**
 * End to end tests against the PHP built in web server.
 *
 * These cover the library itself: the routes, the hierarchy rules, the
 * permissions and the search.
 */

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "http tests\n");

$root = dirname(__DIR__);
$php = PHP_BINARY;
$databasePath = sys_get_temp_dir() . '/wiki-http-' . bin2hex(random_bytes(6)) . '.sqlite';
$port = 8000 + random_int(100, 900);

$environment = [
    'APP_DSN' => 'sqlite:' . $databasePath,
    'PATH' => getenv('PATH') ?: '/usr/bin:/bin',
];

$descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
$server = proc_open(
    sprintf('%s -S 127.0.0.1:%d -t %s', escapeshellarg($php), $port, escapeshellarg($root . '/public')),
    $descriptors,
    $pipes,
    $root,
    $environment
);

if (!is_resource($server)) {
    fwrite(STDERR, "Could not start the test web server.\n");
    exit(1);
}

register_shutdown_function(static function () use ($server, $pipes, $databasePath) {
    foreach ($pipes as $pipe) if (is_resource($pipe)) fclose($pipe);
    if (is_resource($server)) { proc_terminate($server, 15); proc_close($server); }
    if (is_file($databasePath)) @unlink($databasePath);
});

$base = sprintf('http://127.0.0.1:%d', $port);
$ready = false;
for ($attempt = 0; $attempt < 100; $attempt++) {
    $socket = @fsockopen('127.0.0.1', $port, $errno, $errstr, 0.2);
    if ($socket !== false) { fclose($socket); $ready = true; break; }
    usleep(100000);
}
if (!$ready) { fwrite(STDERR, "The test web server did not start.\n"); exit(1); }

/** A client that keeps the session cookie and the CSRF token. */
final class Client {
    private string $base;
    private string $cookie = '';
    private string $csrf = '';

    public function __construct(string $base) { $this->base = $base; }

    public function get(string $path): array { return $this->send($path, null); }

    public function post(string $path, array $fields): array {
        if ($this->csrf === '') {
            $page = $this->get('/register');
            if (preg_match('/name="csrf" value="([a-f0-9]+)"/', $page[1], $m) === 1) $this->csrf = $m[1];
        }
        $fields['csrf'] = $this->csrf;
        return $this->send($path, $fields);
    }

    private function send(string $path, ?array $fields): array {
        $handle = curl_init($this->base . $path);
        curl_setopt($handle, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($handle, CURLOPT_HEADER, true);
        curl_setopt($handle, CURLOPT_FOLLOWLOCATION, false);
        $headers = [];
        if ($this->cookie !== '') $headers[] = 'Cookie: ' . $this->cookie;
        if ($fields !== null) {
            curl_setopt($handle, CURLOPT_POST, true);
            curl_setopt($handle, CURLOPT_POSTFIELDS, http_build_query($fields));
        }
        if ($headers !== []) curl_setopt($handle, CURLOPT_HTTPHEADER, $headers);

        $response = curl_exec($handle);
        $status = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
        $headerSize = (int) curl_getinfo($handle, CURLINFO_HEADER_SIZE);
        curl_close($handle);
        if ($response === false) return [0, '', ''];

        $rawHeaders = substr($response, 0, $headerSize);
        $body = substr($response, $headerSize);

        if (preg_match('/Set-Cookie:\s*([^=]+)=([^;]*)/i', $rawHeaders, $m) === 1) {
            $this->cookie = $m[1] . '=' . $m[2];
        }
        if (preg_match('/name="csrf" value="([a-f0-9]+)"/', $body, $m) === 1) {
            $this->csrf = $m[1];
        }

        return [$status, $body, $rawHeaders];
    }
}

$owner = new Client($base);
$owner->post('/register', ['name' => 'Owner', 'email' => 'owner@example.test', 'password' => 'correct-horse']);

$db = new Database('sqlite:' . $databasePath);

// ---------------------------------------------------------------------------
// The library is created.
// ---------------------------------------------------------------------------

[$status] = $owner->post('/r/books/new', ['title' => 'Handbook', 'description' => 'How we work', 'owner' => 'Owner', 'status' => 'published']);
assert_true($status === 302, 'the book was created');
$bookId = (int) $db->pdo()->query("SELECT id FROM books WHERE title = 'Handbook'")->fetchColumn();
assert_true($bookId > 0, 'the book has an id');

[$status, $body] = $owner->post('/r/chapters/new', ['title' => 'Getting started', 'book_id' => $bookId, 'description' => '', 'position' => 1]);
assert_true($status === 302, 'the chapter was created');
$chapterId = (int) $db->pdo()->query("SELECT id FROM chapters WHERE title = 'Getting started' AND book_id = {$bookId}")->fetchColumn();
assert_true($chapterId > 0, 'the chapter has an id');

[$status, $body] = $owner->post('/r/pages/new', ['title' => 'Install', 'chapter_id' => $chapterId, 'body' => 'How to install', 'tags' => 'setup', 'version' => 1]);
assert_true($status === 302, 'the page was created');
$pageId = (int) $db->pdo()->query("SELECT id FROM pages WHERE title = 'Install'")->fetchColumn();
assert_true($pageId > 0, 'the page has an id');

// ---------------------------------------------------------------------------
// The hierarchy is enforced.
// ---------------------------------------------------------------------------

[$status, $body] = $owner->post('/r/chapters/new', ['title' => 'Orphan', 'book_id' => 999, 'description' => '', 'position' => 1]);
assert_same(200, $status, 'a chapter without a book is refused');
assert_contains($body, 'does not exist', 'the error says the book does not exist');

[$status, $body] = $owner->post('/r/pages/new', ['title' => 'Orphan', 'chapter_id' => 999, 'body' => '', 'tags' => '', 'version' => 1]);
assert_same(200, $status, 'a page without a chapter is refused');
assert_contains($body, 'does not exist', 'the error says the chapter does not exist');

// ---------------------------------------------------------------------------
// The search.
// ---------------------------------------------------------------------------

[$status, $body] = $owner->get('/search?q=Install');
assert_same(200, $status, 'the search page renders');
assert_contains($body, 'Install', 'the search finds the page');

[$status, $body] = $owner->get('/search?q=Handbook');
assert_contains($body, 'Handbook', 'the search finds the book');

[$status, $body] = $owner->get('/search?q=zzzz');
assert_not_contains($body, 'Install', 'a search that matches nothing finds nothing');

// ---------------------------------------------------------------------------
// The book tree.
// ---------------------------------------------------------------------------

[$status, $body] = $owner->get('/books/' . $bookId);
assert_same(200, $status, 'the book renders');
assert_contains($body, 'Getting started', 'the book shows its chapters');
assert_contains($body, 'Install', 'the chapter shows its pages');

// ---------------------------------------------------------------------------
// The permissions: a member may edit a page but not a book.
// ---------------------------------------------------------------------------

$member = new Client($base);
$member->post('/register', ['name' => 'Member', 'email' => 'member@example.test', 'password' => 'correct-horse']);

[$status] = $member->post('/r/pages/' . $pageId, ['title' => 'Install', 'chapter_id' => $chapterId, 'body' => 'Edited by a member', 'tags' => 'setup', 'version' => 2]);
assert_true($status === 302, 'a member may edit a page');
$body = $db->pdo()->query("SELECT body FROM pages WHERE id = {$pageId}")->fetchColumn();
assert_same('Edited by a member', $body, 'the change was saved');

[$status, $body] = $member->post('/r/books/' . $bookId, ['title' => 'Hijacked', 'description' => '', 'owner' => 'Member', 'status' => 'published']);
assert_true($status === 302, 'the member was sent away from the book');
$title = $db->pdo()->query("SELECT title FROM books WHERE id = {$bookId}")->fetchColumn();
assert_same('Handbook', $title, 'the book was not changed');

// ---------------------------------------------------------------------------
// The revisions.
// ---------------------------------------------------------------------------

$revisions = (int) $db->pdo()->query("SELECT COUNT(*) FROM revisions WHERE page_id = {$pageId}")->fetchColumn();
assert_true($revisions >= 1, 'the edit made a revision');

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['wiki_assertions'], $GLOBALS['wiki_failures']));
exit($GLOBALS['wiki_failures'] === 0 ? 0 : 1);
