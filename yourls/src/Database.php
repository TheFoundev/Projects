<?php
declare(strict_types=1);

final class Database {
    private PDO $pdo;
    public function __construct(string $dsn, ?string $user = null, ?string $pass = null) {
        $dir = dirname(__DIR__) . '/data';
        if (!is_dir($dir)) mkdir($dir, 0775, true);
        $this->pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        if (str_starts_with($dsn, 'sqlite:')) {
            $this->pdo->exec('PRAGMA foreign_keys = ON');
            $this->pdo->exec('PRAGMA journal_mode = WAL');
        }
    }
    public function pdo(): PDO { return $this->pdo; }

    public function migrate(array $config): void {
        $this->pdo->exec('CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT "member",
            created_at TEXT NOT NULL
        )');
        foreach ($config['resources'] as $resource) {
            $columns = [];
            foreach ($resource['fields'] as $name => $field) {
                $type = match ($field['type'] ?? 'text') {
                    'int' => 'INTEGER', 'real' => 'REAL', 'bool' => 'INTEGER', default => 'TEXT'
                };
                $columns[] = '"' . $name . '" ' . $type;
            }
            $sql = 'CREATE TABLE IF NOT EXISTS "' . $resource['name'] . '" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ' . implode(",\n                ", $columns) . ',
                created_at TEXT NOT NULL
            )';
            $this->pdo->exec($sql);
            $count = (int) $this->pdo->query('SELECT COUNT(*) FROM "' . $resource['name'] . '"')->fetchColumn();
            if ($count === 0 && !empty($config['seed'][$resource['name']])) {
                foreach ($config['seed'][$resource['name']] as $row) {
                    $keys = array_keys($row);
                    $cols = implode(',', array_map(fn($k) => '"' . $k . '"', $keys));
                    $marks = implode(',', array_fill(0, count($keys), '?'));
                    $stmt = $this->pdo->prepare('INSERT INTO "' . $resource['name'] . '" (' . $cols . ', created_at) VALUES (' . $marks . ', ?)');
                    $stmt->execute([...array_values($row), gmdate('c')]);
                }
            }
        }
        if (($config['special'] ?? '') === 'shortener') {
            // A slug may only be there once, so a short link always points
            // at the target it was made for.
            $this->pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS links_slug_unique ON links (slug)');
        }
        if (($config['special'] ?? '') === 'wiki') {
            $this->pdo->exec('CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER NOT NULL,
                title TEXT NOT NULL, body TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL
            )');
        }
        if (($config['special'] ?? '') === 'commerce') {
            $this->pdo->exec('CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
                name TEXT NOT NULL, quantity INTEGER NOT NULL, unit_cents INTEGER NOT NULL
            )');
        }
    }
}
