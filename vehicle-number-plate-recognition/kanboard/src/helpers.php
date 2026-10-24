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
