<?php
declare(strict_types=1);

/**
 * End to end tests against the PHP built in web server.
 */

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "http tests\n");

$root = dirname(__DIR__);
$php = PHP_BINARY;
$databasePath = sys_get_temp_dir() . '/reader-http-' . bin2hex(random_bytes(6)) . '.sqlite';
$port = 8000 + random_int(100, 900);

$environment = ['APP_DSN' => 'sqlite:' . $databasePath, 'PATH' => getenv('PATH') ?: '/usr/bin:/bin'];
$descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
$server = proc_open(
    sprintf('%s -S 127.0.0.1:%d -t %s', escapeshellarg($php), $port, escapeshellarg($root . '/public')),
    $descriptors, $pipes, $root, $environment
);
if (!is_resource($server)) { fwrite(STDERR, "Could not start the test web server.\n"); exit(1); }

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
        if (preg_match('/Set-Cookie:\s*([^=]+)=([^;]*)/i', $rawHeaders, $m) === 1) $this->cookie = $m[1] . '=' . $m[2];
        if (preg_match('/name="csrf" value="([a-f0-9]+)"/', $body, $m) === 1) $this->csrf = $m[1];
        return [$status, $body, $rawHeaders];
    }
}

$client = new Client($base);
$client->post('/register', ['name' => 'Reader', 'email' => 'reader@example.test', 'password' => 'correct-horse']);

$db = new Database('sqlite:' . $databasePath);

// ---------------------------------------------------------------------------
// An article is saved.
// ---------------------------------------------------------------------------

[$status, $body] = $client->post('/r/articles/new', [
    'title' => 'A good article', 'url' => 'https://example.test/good', 'site' => '',
    'author' => 'Ann', 'excerpt' => 'A short summary', 'content' => 'The body of the article',
    'tags' => 'news, tech', 'status' => 'unread', 'added_at' => '',
]);
assert_true($status === 302, 'the article was created');
$articleId = (int) $db->pdo()->query("SELECT id FROM articles WHERE title = 'A good article'")->fetchColumn();
assert_true($articleId > 0, 'the article has an id');

$row = $db->pdo()->query("SELECT site, excerpt, added_at, status FROM articles WHERE id = {$articleId}")->fetch();
assert_same('example.test', $row['site'], 'the site was filled in from the url');
assert_same('A short summary', $row['excerpt'], 'the excerpt was kept');
assert_true(!empty($row['added_at']), 'the date the article was added was filled in');
assert_same('unread', $row['status'], 'a new article is unread');

// ---------------------------------------------------------------------------
// An article without a url is refused.
// ---------------------------------------------------------------------------

[$status, $body] = $client->post('/r/articles/new', [
    'title' => 'No url', 'url' => 'not a url', 'site' => 'x', 'author' => '', 'excerpt' => '', 'content' => '', 'tags' => '', 'status' => 'unread', 'added_at' => '',
]);
assert_same(200, $status, 'an article without a url is refused');
assert_contains($body, 'http://', 'the error says the url has to be an http one');

// ---------------------------------------------------------------------------
// The reading list.
// ---------------------------------------------------------------------------

[$status, $body] = $client->get('/reading');
assert_same(200, $status, 'the reading list renders');
assert_contains($body, 'A good article', 'the list shows the article');
assert_contains($body, 'unread', 'the list counts the unread articles');
assert_contains($body, '#news', 'the list shows the tags');

[$status, $body] = $client->get('/reading?status=read');
assert_not_contains($body, 'A good article', 'a filter by state works');

[$status, $body] = $client->get('/reading?q=good');
assert_contains($body, 'A good article', 'the search finds the article');

[$status, $body] = $client->get('/reading?q=zzzz');
assert_not_contains($body, 'A good article', 'a search that matches nothing finds nothing');

// ---------------------------------------------------------------------------
// The annotations of an article.
// ---------------------------------------------------------------------------

[$status, $body] = $client->post('/r/annotations/new', [
    'article_id' => $articleId, 'quote' => 'A quoted passage', 'note' => 'Why it matters', 'author' => 'Reader',
]);
assert_true($status === 302, 'the annotation was created');

[$status, $body] = $client->get("/articles/{$articleId}/annotations");
assert_same(200, $status, 'the annotations are served as json');
assert_contains($body, 'A quoted passage', 'the annotation is there');

[$status, $body] = $client->post('/r/annotations/new', [
    'article_id' => 9999, 'quote' => 'Orphan', 'note' => 'Orphan', 'author' => 'Reader',
]);
assert_same(200, $status, 'an annotation for an article that does not exist is refused');

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['wiki_assertions'], $GLOBALS['wiki_failures']));
exit($GLOBALS['wiki_failures'] === 0 ? 0 : 1);
