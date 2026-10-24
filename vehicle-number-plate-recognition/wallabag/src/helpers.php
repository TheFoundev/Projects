<?php
declare(strict_types=1);

function e(mixed $value): string {
    return htmlspecialchars((string) $value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function redirect(string $path): never {
    header('Location: ' . $path);
    exit;
}

function flash(string $message, string $type = 'ok'): void {
    $_SESSION['flash'] = ['message' => $message, 'type' => $type];
}

function take_flash(): ?array {
    $flash = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $flash;
}

function render(string $view, array $data = []): void {
    extract($data, EXTR_SKIP);
    require APP_ROOT . '/views/layout.php';
}

function field_value(array $fields, array $row, string $name): mixed {
    return $row[$name] ?? ($fields[$name]['default'] ?? '');
}

function validate_resource(array $resource, array $input): array {
    $values = [];
    $errors = [];
    foreach ($resource['fields'] as $name => $field) {
        $raw = $input[$name] ?? null;
        $type = $field['type'] ?? 'text';
        if (!empty($field['required']) && ($raw === null || $raw === '')) {
            $errors[] = ($field['label'] ?? $name) . ' is required.';
            continue;
        }
        if ($raw === null || $raw === '') {
            // A field that was not sent keeps the default from the
            // configuration, so a new record is never half empty.
            $values[$name] = array_key_exists('default', $field) ? $field['default'] : null;
            continue;
        }
        if ($type === 'int') $values[$name] = (int) $raw;
        elseif ($type === 'real') $values[$name] = (float) $raw;
        elseif ($type === 'bool') $values[$name] = !empty($raw) ? 1 : 0;
        else $values[$name] = trim((string) $raw);
    }
    return [$values, $errors];
}

/**
 * Send a JSON answer.
 */
function json_response(mixed $data, int $status = 200): never {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

/**
 * Fetch a page.
 *
 * The URL has to be an http one, and the answer is limited so a huge page
 * cannot use all the memory.
 */
function fetch_url(string $url, int $timeout = 10, int $maxBytes = 2000000): string {
    if (!preg_match('#^https?://#i', $url)) {
        throw new RuntimeException('Only http and https urls can be fetched.');
    }

    $context = stream_context_create([
        'http' => [
            'timeout' => $timeout,
            'user_agent' => 'Wallabag Foundev build (reading list)',
            'follow_location' => 1,
            'max_redirects' => 3,
        ],
    ]);

    $body = @file_get_contents($url, false, $context);
    if ($body === false) {
        throw new RuntimeException('The page could not be fetched.');
    }

    return substr($body, 0, $maxBytes);
}
