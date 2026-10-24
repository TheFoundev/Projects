<?php
declare(strict_types=1);

/**
 * End to end tests against the PHP built in web server.
 *
 * These cover the board itself: the route that renders it, the move
 * endpoint and the rules that run when a card is created.
 */

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "http tests\n");

$root = dirname(__DIR__);
$php = PHP_BINARY;
$databasePath = sys_get_temp_dir() . '/kanban-http-' . bin2hex(random_bytes(6)) . '.sqlite';
$port = 8000 + random_int(100, 900);

$environment = [
    'APP_DSN' => 'sqlite:' . $databasePath,
    'APP_SQLITE_PATH' => $databasePath,
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
    foreach ($pipes as $pipe) {
        if (is_resource($pipe)) fclose($pipe);
    }
    if (is_resource($server)) {
        proc_terminate($server, 15);
        proc_close($server);
    }
    if (is_file($databasePath)) @unlink($databasePath);
});

$base = sprintf('http://127.0.0.1:%d', $port);
$ready = false;
for ($attempt = 0; $attempt < 100; $attempt++) {
    $socket = @fsockopen('127.0.0.1', $port, $errno, $errstr, 0.2);
    if ($socket !== false) {
        fclose($socket);
        $ready = true;
        break;
    }
    usleep(100000);
}
if (!$ready) {
    fwrite(STDERR, "The test web server did not start.\n");
    exit(1);
}

/** A client that keeps the session cookie and the CSRF token. */
final class Client {
    private string $base;
    private string $cookie = '';
    private string $csrf = '';

    public function __construct(string $base) { $this->base = $base; }

    public function get(string $path): array {
        return $this->send($path, null);
    }

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

$client = new Client($base);

// ---------------------------------------------------------------------------
// Register and sign in.
// ---------------------------------------------------------------------------

[$status] = $client->post('/register', ['name' => 'Test Owner', 'email' => 'owner@example.test', 'password' => 'correct-horse']);
assert_true($status === 302 || $status === 200, 'the account was created');

// ---------------------------------------------------------------------------
// A project and a card.
// ---------------------------------------------------------------------------

[$status, $body] = $client->post('/r/projects/new', ['name' => 'Website', 'description' => 'The site', 'status' => 'active', 'owner' => 'Test Owner']);
assert_true($status === 200 || $status === 302, 'the project was created');

$db = new Database('sqlite:' . $databasePath);
$db->pdo()->exec("INSERT INTO tasks (project_id, title, description, status, assignee, priority, due_date, position, created_at) VALUES (1, 'Write the board', '', 'backlog', 'Ana', 'high', '', 1, '2026-04-01T00:00:00Z')");
$db->pdo()->exec("INSERT INTO tasks (project_id, title, description, status, assignee, priority, due_date, position, created_at) VALUES (1, 'Second card', '', 'todo', '', 'medium', '2026-04-01', 1, '2026-04-01T00:00:00Z')");

// ---------------------------------------------------------------------------
// The board itself.
// ---------------------------------------------------------------------------

[$status, $body] = $client->get('/board');
assert_same(200, $status, 'the board renders');
assert_contains($body, 'Write the board', 'the board shows the cards');
assert_contains($body, 'Backlog', 'the board shows the columns');
assert_contains($body, 'In progress', 'the board shows every column');
assert_contains($body, 'overdue', 'the board reports the overdue cards');

// ---------------------------------------------------------------------------
// Moving a card.
// ---------------------------------------------------------------------------

[$status, $body] = $client->post('/r/tasks/1/move', ['status' => 'in_progress', 'position' => 1]);
assert_true($status === 302, 'the card was moved');

$moved = $db->pdo()->query("SELECT status FROM tasks WHERE id = 1")->fetchColumn();
assert_same('in_progress', $moved, 'the card changed column');

// The column has a limit of three cards, so a fourth one is refused.
for ($i = 0; $i < 3; $i++) {
    $db->pdo()->exec("INSERT INTO tasks (project_id, title, description, status, assignee, priority, due_date, position, created_at) VALUES (1, 'Filler $i', '', 'in_progress', '', 'medium', '', 1, '2026-04-01T00:00:00Z')");
}
[$status, $body] = $client->post('/r/tasks/2/move', ['status' => 'in_progress', 'position' => 1]);
assert_true($status === 302, 'the move was answered');
$moved = $db->pdo()->query("SELECT status FROM tasks WHERE id = 2")->fetchColumn();
assert_same('todo', $moved, 'the card was not moved into a full column');

// ---------------------------------------------------------------------------
// The rules that run when a card is created.
// ---------------------------------------------------------------------------

[$status, $body] = $client->post('/r/tasks/new', [
    'project_id' => 99, 'title' => 'No project', 'status' => 'todo', 'priority' => 'medium',
]);
assert_same(200, $status, 'the form is shown again');
assert_contains($body, 'does not exist', 'a card needs a real project');

[$status, $body] = $client->post('/r/tasks/new', [
    'project_id' => 1, 'title' => 'Wrong status', 'status' => 'nope', 'priority' => 'medium',
]);
assert_contains($body, 'not a column', 'the status has to be a column of the board');

[$status, $body] = $client->post('/r/tasks/new', [
    'project_id' => 1, 'title' => 'Good card', 'status' => 'todo', 'priority' => 'medium',
]);
assert_true($status === 302, 'a good card is created');
$count = (int) $db->pdo()->query("SELECT COUNT(*) FROM tasks WHERE title = 'Good card'")->fetchColumn();
assert_same(1, $count, 'the card was stored');

// The default of the status is used when the field is not sent.
[$status, $body] = $client->post('/r/tasks/new', ['project_id' => 1, 'title' => 'Default card']);
assert_same(302, $status, 'a card without a status is created');
$status_column = $db->pdo()->query("SELECT status FROM tasks WHERE title = 'Default card'")->fetchColumn();
assert_same('backlog', $status_column, 'a new card starts in the backlog');

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['kanban_failures'] === 0 ? $GLOBALS['kanban_assertions'] : $GLOBALS['kanban_assertions'], $GLOBALS['kanban_failures']));
exit($GLOBALS['kanban_failures'] === 0 ? 0 : 1);
