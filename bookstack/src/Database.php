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
            // The hierarchy is enforced by the database, not only by the
            // application: a chapter always belongs to a book and a page
            // always belongs to a chapter. A table constraint has to come
            // after the columns, so it is kept apart from them.
            $constraints = [];
            if ($resource['name'] === 'chapters') {
                $constraints[] = 'FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE';
            }
            if ($resource['name'] === 'pages') {
                $constraints[] = 'FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE';
            }

            $sql = 'CREATE TABLE IF NOT EXISTS "' . $resource['name'] . '" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ' . implode(",\n                ", $columns) . ',
                created_at TEXT NOT NULL'
                . ($constraints ? ",\n                " . implode(",\n                ", $constraints) : '') . '
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
        if (($config['special'] ?? '') === 'wiki') {
            $this->pdo->exec('CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER NOT NULL,
                title TEXT NOT NULL, body TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL
            )');
        }
    }
}
