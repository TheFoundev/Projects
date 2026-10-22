<?php
/**
 * Application bootstrap: configuration, database connection and shared helpers.
 *
 * Every include of this file must happen before any output is sent, because it
 * starts the session and sets the security headers.
 */

declare(strict_types=1);

/** Idle timeout for an authenticated session, in seconds. */
const SESSION_IDLE_TIMEOUT = 1800;
/** Length of the generated CSRF token, in bytes. */
const CSRF_TOKEN_BYTES = 32;

if (session_status() !== PHP_SESSION_ACTIVE) {
    // Hardened cookie/session defaults. Secure cookies are only sent over
    // HTTPS, which is why this is toggled on the actual request scheme.
    $isHttps = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.cookie_httponly', '1');
    ini_set('session.cookie_samesite', 'Lax');
    ini_set('session.cookie_secure', $isHttps ? '1' : '0');
    ini_set('session.gc_maxlifetime', (string) SESSION_IDLE_TIMEOUT);
    session_name('SRMSSESSID');
    session_start();
}

header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('Referrer-Policy: no-referrer');

/**
 * Build the PDO connection.
 *
 * MySQL/MariaDB is used when SRMS_DSN is set (the production path). When it is
 * not set the application falls back to a local SQLite file so the project can
 * be run and tested without provisioning a database server.
 */
function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $dsn = getenv('SRMS_DSN');
    if ($dsn === false || $dsn === '') {
        $path = getenv('SRMS_SQLITE_PATH');
        if ($path === false || $path === '') {
            $path = dirname(__DIR__) . '/data/srms.sqlite';
        }
        $directory = dirname($path);
        if (!is_dir($directory)) {
            mkdir($directory, 0770, true);
        }
        $dsn = 'sqlite:' . $path;
        $pdo = new PDO($dsn, null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        $pdo->exec('PRAGMA foreign_keys = ON');
    } else {
        $pdo = new PDO(
            $dsn,
            (string) (getenv('SRMS_DB_USER') ?: ''),
            (string) (getenv('SRMS_DB_PASSWORD') ?: ''),
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]
        );
    }

    ensure_schema($pdo);

    return $pdo;
}

/** True when the application is running against SQLite. */
function db_is_sqlite(PDO $pdo): bool
{
    return (string) $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'sqlite';
}

/**
 * Create the tables when they are missing.
 *
 * The DDL is written so that it runs unchanged on MySQL/MariaDB and SQLite.
 */
function ensure_schema(PDO $pdo): void
{
    $statements = schema_statements($pdo);
    foreach ($statements as $statement) {
        $pdo->exec($statement);
    }
}

/** Return the portable CREATE TABLE statements for the active driver. */
function schema_statements(PDO $pdo): array
{
    if (db_is_sqlite($pdo)) {
        return [
            'CREATE TABLE IF NOT EXISTS admin_login (
                userid VARCHAR(64) NOT NULL PRIMARY KEY,
                password VARCHAR(255) NULL,
                password_hash VARCHAR(255) NULL
            )',
            'CREATE TABLE IF NOT EXISTS class (
                name VARCHAR(64) NOT NULL,
                id INTEGER NOT NULL PRIMARY KEY
            )',
            'CREATE TABLE IF NOT EXISTS students (
                name VARCHAR(128) NOT NULL,
                rno INTEGER NOT NULL,
                class_name VARCHAR(64) NOT NULL,
                PRIMARY KEY (rno, class_name)
            )',
            'CREATE TABLE IF NOT EXISTS login_attempts (
                userid VARCHAR(64) NOT NULL PRIMARY KEY,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_attempt INTEGER NOT NULL DEFAULT 0
            )',
            'CREATE TABLE IF NOT EXISTS result (
                name VARCHAR(128) NOT NULL,
                rno INTEGER NOT NULL,
                class_name VARCHAR(64) NOT NULL,
                p1 INTEGER NOT NULL,
                p2 INTEGER NOT NULL,
                p3 INTEGER NOT NULL,
                p4 INTEGER NOT NULL,
                p5 INTEGER NOT NULL,
                marks INTEGER NOT NULL,
                percentage REAL NOT NULL,
                PRIMARY KEY (rno, class_name)
            )',
        ];
    }

    return [
        'CREATE TABLE IF NOT EXISTS admin_login (
            userid VARCHAR(64) NOT NULL,
            password VARCHAR(255) NULL,
            password_hash VARCHAR(255) NULL,
            PRIMARY KEY (userid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS class (
            name VARCHAR(64) NOT NULL,
            id INTEGER NOT NULL,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS students (
            name VARCHAR(128) NOT NULL,
            rno INTEGER NOT NULL,
            class_name VARCHAR(64) NOT NULL,
            PRIMARY KEY (rno, class_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS result (
            name VARCHAR(128) NOT NULL,
            rno INTEGER NOT NULL,
            class_name VARCHAR(64) NOT NULL,
            p1 INTEGER NOT NULL,
            p2 INTEGER NOT NULL,
            p3 INTEGER NOT NULL,
            p4 INTEGER NOT NULL,
            p5 INTEGER NOT NULL,
            marks INTEGER NOT NULL,
            percentage DOUBLE NOT NULL,
            PRIMARY KEY (rno, class_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS login_attempts (
            userid VARCHAR(64) NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_attempt INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (userid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    ];
}

/** Run a prepared statement and return the statement. */
function db_query(string $sql, array $params = []): PDOStatement
{
    $statement = db()->prepare($sql);
    $statement->execute($params);

    return $statement;
}

/** Fetch a single row, or null. */
function db_one(string $sql, array $params = []): ?array
{
    $row = db_query($sql, $params)->fetch();

    return $row === false ? null : $row;
}

/** Fetch every row. */
function db_all(string $sql, array $params = []): array
{
    return db_query($sql, $params)->fetchAll();
}

/** Escape a value for safe output in HTML. */
function e($value): string
{
    return htmlspecialchars((string) $value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Return the CSRF token for the current session, creating one if needed. */
function csrf_token(): string
{
    if (empty($_SESSION['csrf_token']) || !is_string($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(CSRF_TOKEN_BYTES));
    }

    return $_SESSION['csrf_token'];
}

/** Render a hidden CSRF input field. */
function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . e(csrf_token()) . '">';
}

/**
 * Check the submitted CSRF token against the session token.
 *
 * Uses hash_equals so the comparison does not leak timing information.
 */
function csrf_valid(?string $submitted): bool
{
    $expected = $_SESSION['csrf_token'] ?? null;
    if (!is_string($expected) || !is_string($submitted) || $submitted === '') {
        return false;
    }

    return hash_equals($expected, $submitted);
}

/** Abort the current request unless the CSRF token is valid. */
function require_csrf(): void
{
    if (!csrf_valid($_POST['csrf_token'] ?? null)) {
        http_response_code(400);
        header('Content-Type: text/html; charset=utf-8');
        echo '<p class="error">Invalid or missing CSRF token. Please reload the page and try again.</p>';
        exit;
    }
}

/** Store a one-shot message for the next request. */
function flash(string $message, string $kind = 'success'): void
{
    $_SESSION['flash'] = ['message' => $message, 'kind' => $kind];
}

/** Read and clear the pending flash message. */
function take_flash(): ?array
{
    $flash = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);

    return is_array($flash) ? $flash : null;
}

/** Render the pending flash message as HTML. */
function render_flash(): string
{
    $flash = take_flash();
    if ($flash === null) {
        return '';
    }

    return '<p class="' . e($flash['kind']) . '">' . e($flash['message']) . '</p>';
}
