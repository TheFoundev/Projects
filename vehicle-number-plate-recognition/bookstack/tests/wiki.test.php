<?php
declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "wiki tests\n");

// ---------------------------------------------------------------------------
// The rules
// ---------------------------------------------------------------------------

assert_true(wiki_is_book_status('published'), 'published is a book status');
assert_true(wiki_is_book_status('draft'), 'draft is a book status');
assert_true(!wiki_is_book_status('hidden'), 'hidden is not a book status');
assert_true(wiki_is_role('owner'), 'owner is a role');
assert_true(!wiki_is_role('admin'), 'admin is not a role');

// ---------------------------------------------------------------------------
// The hierarchy
// ---------------------------------------------------------------------------

$books = [['id' => 1, 'title' => 'Handbook', 'status' => 'published', 'owner' => 'Ana']];
$chapters = [['id' => 1, 'title' => 'Getting started', 'book_id' => 1, 'position' => 1]];

assert_true(wiki_check_hierarchy('chapters', ['book_id' => 1, 'position' => 1], $books, $chapters) === null, 'a chapter in a real book is fine');
assert_contains((string) wiki_check_hierarchy('chapters', ['book_id' => 99, 'position' => 1], $books, $chapters), 'does not exist', 'a chapter needs a real book');
assert_contains((string) wiki_check_hierarchy('chapters', ['book_id' => 1, 'position' => 0], $books, $chapters), 'one or more', 'the position has to be one or more');
assert_contains((string) wiki_check_hierarchy('pages', ['chapter_id' => 99], $books, $chapters), 'does not exist', 'a page needs a real chapter');
assert_true(wiki_check_hierarchy('pages', ['chapter_id' => 1], $books, $chapters) === null, 'a page in a real chapter is fine');
assert_contains((string) wiki_check_hierarchy('books', ['status' => 'nope'], $books, $chapters), 'not a book status', 'the book status has to be one the library knows');

// ---------------------------------------------------------------------------
// The book of a page and the tree of a book
// ---------------------------------------------------------------------------

$pages = [['id' => 1, 'title' => 'Install', 'chapter_id' => 1, 'version' => 1]];

$book = wiki_book_of_page(1, $pages, $chapters);
assert_same(1, $book['id'] ?? null, 'the book of a page is the book of its chapter');
assert_same(null, wiki_book_of_page(99, $pages, $chapters), 'an unknown page has no book');

$tree = wiki_book_tree(1, $books, $chapters, $pages);
assert_same('Handbook', $tree['book']['title'], 'the tree has the book');
assert_same(1, count($tree['chapters']), 'the tree has the chapters');
assert_same(1, count($tree['chapters'][0]['pages']), 'the chapter holds its pages');
assert_same(null, wiki_book_tree(99, $books, $chapters, $pages), 'an unknown book has no tree');

$ordered = wiki_book_tree(1, $books, [
    ['id' => 2, 'title' => 'Second', 'book_id' => 1, 'position' => 2],
    ['id' => 1, 'title' => 'First', 'book_id' => 1, 'position' => 1],
], $pages);
assert_same('First', $ordered['chapters'][0]['chapter']['title'], 'the chapters are in the order of their position');

// ---------------------------------------------------------------------------
// The search
// ---------------------------------------------------------------------------

$found = wiki_search($books, $chapters, $pages, 'install');
assert_same(1, count($found['pages']), 'the search looks in the pages');
assert_same(0, $found['total'] - 1, 'the total counts every hit');

$found = wiki_search($books, $chapters, $pages, 'handbook');
assert_same(1, count($found['books']), 'the search looks in the books');

$found = wiki_search($books, $chapters, $pages, 'started');
assert_same(1, count($found['chapters']), 'the search looks in the chapters');

$found = wiki_search($books, $chapters, $pages, '');
assert_same(0, $found['total'], 'an empty query finds nothing');
assert_same(0, count(wiki_search($books, $chapters, $pages, 'zzzz')['pages']), 'a query that matches nothing finds nothing');

// ---------------------------------------------------------------------------
// The versions and the revisions
// ---------------------------------------------------------------------------

assert_same(2, wiki_next_version(1), 'a saved page goes up one version');
assert_same(1, wiki_next_version(null), 'a page without a version starts at one');
assert_same(1, wiki_next_version(0), 'a page with version zero starts at one');

$revision = wiki_revision(['id' => 3, 'title' => 'Install', 'body' => 'Text'], 2);
assert_same(3, $revision['page_id'], 'the revision belongs to the page');
assert_same(2, $revision['version'], 'the revision keeps the version');

// ---------------------------------------------------------------------------
// The permissions
// ---------------------------------------------------------------------------

$owner = ['name' => 'Ana', 'role' => 'owner'];
$member = ['name' => 'Bo', 'role' => 'member'];

assert_true(wiki_can($owner, 'read'), 'the owner can read');
assert_true(wiki_can($owner, 'edit_page'), 'the owner can edit a page');
assert_true(wiki_can($owner, 'edit_book'), 'the owner can edit a book');
assert_true(wiki_can($owner, 'delete'), 'the owner can delete');
assert_true(wiki_can($member, 'read'), 'a member can read');
assert_true(wiki_can($member, 'edit_page'), 'a member can edit a page');
assert_true(!wiki_can($member, 'edit_book'), 'a member cannot edit a book');
assert_true(!wiki_can($member, 'delete'), 'a member cannot delete');
assert_true(!wiki_can(null, 'read'), 'an anonymous visitor cannot read');

// ---------------------------------------------------------------------------
// The summary
// ---------------------------------------------------------------------------

$summary = wiki_summary($books, $chapters, $pages);
assert_same(1, $summary['books'], 'the summary counts the books');
assert_same(1, $summary['chapters'], 'the summary counts the chapters');
assert_same(1, $summary['pages'], 'the summary counts the pages');
assert_same(1, $summary['published'], 'the summary counts the published books');

// ---------------------------------------------------------------------------
// The database
// ---------------------------------------------------------------------------

$db = test_db();
$ids = seed_library($db);

$booksInDb = $db->pdo()->query('SELECT * FROM books')->fetchAll();
$chaptersInDb = $db->pdo()->query('SELECT * FROM chapters')->fetchAll();
$pagesInDb = $db->pdo()->query('SELECT * FROM pages')->fetchAll();
assert_true(count($booksInDb) >= 1, 'the book was stored');
assert_true(count($chaptersInDb) >= 1, 'the chapter was stored');
assert_true(count($pagesInDb) >= 1, 'the page was stored');
assert_true(in_array($ids['book'], array_map(fn($row) => (int) $row['id'], $booksInDb), true), 'the book has the id it was given');
assert_true(in_array($ids['chapter'], array_map(fn($row) => (int) $row['id'], $chaptersInDb), true), 'the chapter has the id it was given');
assert_true(in_array($ids['page'], array_map(fn($row) => (int) $row['id'], $pagesInDb), true), 'the page has the id it was given');

// The database refuses a chapter whose book does not exist.
$failed = false;
try {
    $db->pdo()->exec("INSERT INTO chapters (title, book_id, description, position, created_at) VALUES ('Orphan', 999, '', 1, '2026-04-01T00:00:00Z')");
} catch (PDOException $e) {
    $failed = true;
}
assert_true($failed, 'the database refuses a chapter without a book');

// The same for a page without a chapter.
$failed = false;
try {
    $db->pdo()->exec("INSERT INTO pages (title, chapter_id, body, tags, version, created_at) VALUES ('Orphan', 999, 'x', '', 1, '2026-04-01T00:00:00Z')");
} catch (PDOException $e) {
    $failed = true;
}
assert_true($failed, 'the database refuses a page without a chapter');

// The defaults of the configuration are used when a field is not sent.
$config = require APP_ROOT . '/config.php';
$booksResource = null;
foreach ($config['resources'] as $resource) {
    if ($resource['name'] === 'books') $booksResource = $resource;
}
[$values, $errors] = validate_resource($booksResource, ['title' => 'Defaults']);
assert_same(0, count($errors), 'a book without a status is valid');
assert_same('published', $values['status'], 'a new book is published by default');

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['wiki_assertions'], $GLOBALS['wiki_failures']));
exit($GLOBALS['wiki_failures'] === 0 ? 0 : 1);
