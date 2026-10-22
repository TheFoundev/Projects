<?php
/**
 * End to end tests against the PHP built in web server.
 *
 * These cover the behaviour that unit tests cannot: the login flow, the SQL
 * injection attempt on the login form, the CSRF enforcement on the admin
 * forms and the escaping of stored data in the student page.
 */

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "http tests\n");

$root = dirname(__DIR__);
$php = PHP_BINARY;
$databasePath = sys_get_temp_dir() . '/srms-http-' . bin2hex(random_bytes(6)) . '.sqlite';
$port = 8000 + random_int(100, 900);

$environment = [
    'SRMS_SQLITE_PATH' => $databasePath,
    'SRMS_DSN' => '',
    'PATH' => getenv('PATH') ?: '/usr/bin:/bin',
];

$descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
$server = proc_open(
    sprintf('%s -S 127.0.0.1:%d -t %s', escapeshellarg($php), $port, escapeshellarg($root)),
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
        if (is_resource($pipe)) {
            fclose($pipe);
        }
    }
    if (is_resource($server)) {
        proc_terminate($server, 15);
        proc_close($server);
    }
    if (is_file($databasePath)) {
        @unlink($databasePath);
    }
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

/**
 * A tiny HTTP client that keeps the session cookie explicitly.
 *
 * The cookie is tracked by hand rather than through curl's cookie jar so the
 * test does not depend on how curl decides to persist a session cookie.
 */
final class Client
{
    /** @var array<string, string> */
    private array $cookies = [];

    private string $base;

    public function __construct(string $base)
    {
        $this->base = $base;
    }

    public function get(string $path): array
    {
        return $this->send($path, null);
    }

    public function post(string $path, array $fields): array
    {
        return $this->send($path, $fields);
    }

    public function cookieHeader(): string
    {
        $parts = [];
        foreach ($this->cookies as $name => $value) {
            $parts[] = $name . '=' . $value;
        }

        return implode('; ', $parts);
    }

    public function clearCookies(): void
    {
        $this->cookies = [];
    }

    private function send(string $path, ?array $fields): array
    {
        $handle = curl_init($this->base . $path);
        curl_setopt($handle, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($handle, CURLOPT_HEADER, true);
        curl_setopt($handle, CURLOPT_FOLLOWLOCATION, false);
        $headers = [];
        if ($this->cookieHeader() !== '') {
            $headers[] = 'Cookie: ' . $this->cookieHeader();
        }
        if ($fields !== null) {
            curl_setopt($handle, CURLOPT_POST, true);
            curl_setopt($handle, CURLOPT_POSTFIELDS, http_build_query($fields));
        }
        if ($headers !== []) {
            curl_setopt($handle, CURLOPT_HTTPHEADER, $headers);
        }
        $response = curl_exec($handle);
        $status = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
        $headerSize = (int) curl_getinfo($handle, CURLINFO_HEADER_SIZE);
        curl_close($handle);

        if ($response === false) {
            return [0, '', ''];
        }

        $rawHeaders = substr($response, 0, $headerSize);
        $body = substr($response, $headerSize);

        // Collect the session cookies the server hands out.
        if (preg_match_all('/^Set-Cookie:\s*([^=]+)=([^;]*)/mi', $rawHeaders, $matches, PREG_SET_ORDER) > 0) {
            foreach ($matches as $match) {
                $name = trim($match[1]);
                $value = trim($match[2]);
                if ($value === '' || str_contains($match[0], 'expires=Thu, 19 Nov 1981')) {
                    unset($this->cookies[$name]);
                    continue;
                }
                $this->cookies[$name] = $value;
            }
        }

        return [$status, $body, $rawHeaders];
    }
}

/** Pull the CSRF token out of a rendered page. */
function csrf_from(string $html): ?string
{
    if (preg_match('/name="csrf_token" value="([a-f0-9]{64})"/', $html, $matches) === 1) {
        return $matches[1];
    }

    return null;
}

$client = new Client($base);

// ---------------------------------------------------------------------------
// The login page is reachable and carries a CSRF token.
// ---------------------------------------------------------------------------
[$status, $body] = $client->get('/login.php');
assert_same(200, $status, 'GET /login.php returns 200');
assert_true(csrf_from($body) !== null, 'the login form carries a CSRF token');
$token = (string) csrf_from($body);

// ---------------------------------------------------------------------------
// SQL injection through the login form must not authenticate anyone.
// ---------------------------------------------------------------------------
[$status, $body] = $client->post('/login.php', [
    'userid' => "' OR '1'='1",
    'password' => "' OR '1'='1",
    'csrf_token' => $token,
]);
assert_true($status !== 302, 'a SQL injection attempt does not redirect to the dashboard');
assert_contains($body, 'Invalid username or password', 'a SQL injection attempt is rejected');

// The classic payload against the password field alone.
[$status, $body] = $client->post('/login.php', [
    'userid' => 'admin',
    'password' => "' OR '1'='1",
    'csrf_token' => $token,
]);
assert_true($status !== 302, 'a password field injection attempt does not authenticate');

// ---------------------------------------------------------------------------
// A missing CSRF token is rejected.
// ---------------------------------------------------------------------------
[$status, $body] = $client->post('/login.php', [
    'userid' => 'admin',
    'password' => 'anything',
]);
assert_same(400, $status, 'a login without a CSRF token is rejected with 400');
assert_contains($body, 'CSRF', 'the CSRF error explains itself');

// ---------------------------------------------------------------------------
// Create an administrator and sign in with it.
// ---------------------------------------------------------------------------
exec(sprintf(
    'SRMS_SQLITE_PATH=%s %s %s %s %s 2>&1',
    escapeshellarg($databasePath),
    escapeshellarg($php),
    escapeshellarg($root . '/scripts/create_admin.php'),
    escapeshellarg('admin'),
    escapeshellarg('correct-horse')
), $output, $exitCode);
assert_same(0, $exitCode, 'create_admin.php creates an administrator');

[$status, $body, $headers] = $client->post('/login.php', [
    'userid' => 'admin',
    'password' => 'correct-horse',
    'csrf_token' => $token,
]);
assert_same(302, $status, 'a correct password redirects to the dashboard');
assert_contains($headers, 'Location: dashboard.php', 'the redirect points at the dashboard');

// ---------------------------------------------------------------------------
// The admin area is reachable with the session cookie.
// ---------------------------------------------------------------------------
[$status, $body] = $client->get('/dashboard.php');
assert_same(200, $status, 'the dashboard is reachable when signed in');
assert_contains($body, 'Number of classes', 'the dashboard renders the counters');

// ---------------------------------------------------------------------------
// Adding a class requires a CSRF token.
// ---------------------------------------------------------------------------
[$status, $body] = $client->post('/add_classes.php', [
    'class_name' => 'First Year',
    'class_id' => '1',
]);
assert_same(400, $status, 'adding a class without a CSRF token is rejected');

[$status, $body] = $client->get('/add_classes.php');
$classToken = (string) csrf_from($body);
assert_true($classToken !== null, 'the add class form carries a CSRF token');

[$status, $body] = $client->post('/add_classes.php', [
    'class_name' => 'First Year',
    'class_id' => '1',
    'csrf_token' => $classToken,
]);
assert_same(200, $status, 'adding a class with a CSRF token succeeds');
assert_contains($body, 'First Year', 'the new class is listed');

// ---------------------------------------------------------------------------
// A class name with an injection payload is stored literally and escaped.
// ---------------------------------------------------------------------------
[$status, $body] = $client->get('/add_classes.php');
$classToken = (string) csrf_from($body);
$payload = "<script>alert('xss')</script>";
$client->post('/add_classes.php', [
    'class_name' => $payload,
    'class_id' => '2',
    'csrf_token' => $classToken,
]);

[$status, $body] = $client->get('/manage_classes.php');
assert_contains($body, '&lt;script&gt;', 'the stored payload is HTML escaped in the admin list');
assert_not_contains($body, "<script>alert('xss')</script>", 'the raw payload is never rendered');

// The class table must still be there.
[$status, $body] = $client->get('/dashboard.php');
assert_contains($body, 'Number of classes', 'the dashboard still works after the injection attempt');

// ---------------------------------------------------------------------------
// The student page escapes everything it prints.
// ---------------------------------------------------------------------------
[$status, $body] = $client->get('/add_students.php');
$studentToken = (string) csrf_from($body);
$client->post('/add_students.php', [
    'student_name' => "<img src=x onerror=alert(1)>",
    'roll_no' => '1011',
    'class_name' => 'First Year',
    'csrf_token' => $studentToken,
]);

// Add a result for that student so the result page renders it.
[$status, $body] = $client->get('/add_results.php');
$resultToken = (string) csrf_from($body);
[$status, $body] = $client->post('/add_results.php', [
    'class_name' => 'First Year',
    'rno' => '1011',
    'p1' => '80', 'p2' => '90', 'p3' => '70', 'p4' => '60', 'p5' => '95',
    'csrf_token' => $resultToken,
]);
assert_same(200, $status, 'a result can be saved');

$studentClient = new Client($base);
[$status, $body] = $studentClient->get('/student.php?class=First+Year&rn=1011');
assert_same(200, $status, 'the student result page is reachable');
assert_contains($body, '&lt;img src=x onerror=alert(1)&gt;', 'the student name is escaped');
assert_not_contains($body, '<img src=x onerror=alert(1)>', 'the raw student name is never rendered');

// A non numeric roll number is rejected rather than interpolated.
[$status, $body] = $studentClient->get('/student.php?class=First+Year&rn=1%27+OR+%271%27%3D%271');
assert_contains($body, 'valid roll number', 'a non numeric roll number is rejected');

// ---------------------------------------------------------------------------
// The admin area redirects to the login page without a session.
// ---------------------------------------------------------------------------
$anonymous = new Client($base);
[$status, $body, $headers] = $anonymous->get('/dashboard.php');
assert_same(302, $status, 'the dashboard redirects an anonymous visitor');
assert_contains($headers, 'Location: login.php', 'the redirect points at the login page');

// ---------------------------------------------------------------------------
// Repeated failures lock the account out.
// ---------------------------------------------------------------------------
$attacker = new Client($base);
[$status, $body] = $attacker->get('/login.php');
$attackerToken = (string) csrf_from($body);
$locked = false;
for ($try = 0; $try < 8; $try++) {
    [$status, $body] = $attacker->post('/login.php', [
        'userid' => 'admin',
        'password' => 'wrong-password',
        'csrf_token' => $attackerToken,
    ]);
    if (str_contains($body, 'Too many failed attempts')) {
        $locked = true;
        break;
    }
}
assert_true($locked, 'repeated failed sign in attempts lock the account out');

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
fwrite(STDOUT, sprintf(
    "%d assertions, %d failures\n",
    $GLOBALS['srms_test_assertions'],
    $GLOBALS['srms_test_failures']
));

exit($GLOBALS['srms_test_failures'] === 0 ? 0 : 1);
