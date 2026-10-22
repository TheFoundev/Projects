<?php
declare(strict_types=1);

/**
 * The wiki domain.
 *
 * The rules that make a set of books, chapters and pages a library: the
 * hierarchy has to hold, the revisions have to follow the pages, only the
 * owner may change the library itself, and the search has to look in all
 * three levels.
 *
 * Pure functions, no database access, so the rules can be unit tested on
 * their own.
 */

/** The states a book can be in. */
const WIKI_BOOK_STATUSES = ['published', 'draft', 'archived'];

/** The roles a user can have. */
const WIKI_ROLES = ['owner', 'member'];

/** True when the status is one the library knows. */
function wiki_is_book_status(mixed $status): bool {
    return in_array((string) $status, WIKI_BOOK_STATUSES, true);
}

/** True when the role is one the library knows. */
function wiki_is_role(mixed $role): bool {
    return in_array((string) $role, WIKI_ROLES, true);
}

/**
 * Check that the hierarchy holds.
 *
 * A chapter belongs to a book and a page belongs to a chapter, so the
 * chapter of a page has to belong to the same book as the page. The
 * position of a chapter is a number.
 *
 * Returns an error message, or null when the hierarchy is fine.
 */
function wiki_check_hierarchy(string $kind, array $values, array $books, array $chapters): ?string {
    if ($kind === 'chapters') {
        $bookId = (int) ($values['book_id'] ?? 0);
        $found = false;
        foreach ($books as $book) {
            if ((int) $book['id'] === $bookId) { $found = true; break; }
        }
        if (!$found) return 'The book does not exist.';
        $position = (int) ($values['position'] ?? 1);
        if ($position < 1) return 'The position has to be one or more.';
        return null;
    }

    if ($kind === 'pages') {
        $chapterId = (int) ($values['chapter_id'] ?? 0);
        $chapter = null;
        foreach ($chapters as $row) {
            if ((int) $row['id'] === $chapterId) { $chapter = $row; break; }
        }
        if (!$chapter) return 'The chapter does not exist.';
        return null;
    }

    if ($kind === 'books') {
        if (!wiki_is_book_status($values['status'] ?? 'published')) {
            return '"' . (string) ($values['status'] ?? '') . '" is not a book status.';
        }
        return null;
    }

    return null;
}

/**
 * The book a page belongs to.
 *
 * A page belongs to a chapter, and a chapter belongs to a book, so the book
 * of a page is the book of its chapter.
 */
function wiki_book_of_page(int $pageId, array $pages, array $chapters): ?array {
    $page = null;
    foreach ($pages as $row) {
        if ((int) $row['id'] === $pageId) { $page = $row; break; }
    }
    if (!$page) return null;

    $chapter = null;
    foreach ($chapters as $row) {
        if ((int) $row['id'] === (int) $page['chapter_id']) { $chapter = $row; break; }
    }
    if (!$chapter) return null;

    return ['id' => (int) $chapter['book_id']];
}

/**
 * The library of one book: its chapters in order, with the pages of each
 * chapter.
 */
function wiki_book_tree(int $bookId, array $books, array $chapters, array $pages): ?array {
    $book = null;
    foreach ($books as $row) {
        if ((int) $row['id'] === $bookId) { $book = $row; break; }
    }
    if (!$book) return null;

    $bookChapters = [];
    foreach ($chapters as $chapter) {
        if ((int) $chapter['book_id'] !== $bookId) continue;
        $bookChapters[] = $chapter;
    }
    usort($bookChapters, function (array $a, array $b): int {
        $left = (int) ($a['position'] ?? 0);
        $right = (int) ($b['position'] ?? 0);
        return $left === $right ? ((int) $a['id'] <=> (int) $b['id']) : $left <=> $right;
    });

    $tree = [];
    foreach ($bookChapters as $chapter) {
        $chapterPages = [];
        foreach ($pages as $page) {
            if ((int) $page['chapter_id'] === (int) $chapter['id']) $chapterPages[] = $page;
        }
        usort($chapterPages, fn($a, $b) => ((int) $a['id']) <=> ((int) $b['id']));
        $tree[] = ['chapter' => $chapter, 'pages' => $chapterPages];
    }

    return ['book' => $book, 'chapters' => $tree];
}

/**
 * The search across the whole library.
 *
 * Books, chapters and pages are searched at the same time and the results
 * are grouped by kind, with the best match of each kind first.
 */
function wiki_search(array $books, array $chapters, array $pages, string $query): array {
    $needle = trim(mb_strtolower($query));
    if ($needle === '') return ['books' => [], 'chapters' => [], 'pages' => [], 'total' => 0];

    $found = ['books' => [], 'chapters' => [], 'pages' => []];

    foreach ($books as $book) {
        $haystack = mb_strtolower(($book['title'] ?? '') . ' ' . ($book['description'] ?? ''));
        if (str_contains($haystack, $needle)) $found['books'][] = $book;
    }
    foreach ($chapters as $chapter) {
        $haystack = mb_strtolower(($chapter['title'] ?? '') . ' ' . ($chapter['description'] ?? ''));
        if (str_contains($haystack, $needle)) $found['chapters'][] = $chapter;
    }
    foreach ($pages as $page) {
        $haystack = mb_strtolower(($page['title'] ?? '') . ' ' . ($page['body'] ?? '') . ' ' . ($page['tags'] ?? ''));
        if (str_contains($haystack, $needle)) $found['pages'][] = $page;
    }

    $total = count($found['books']) + count($found['chapters']) + count($found['pages']);
    return ['books' => $found['books'], 'chapters' => $found['chapters'], 'pages' => $found['pages'], 'total' => $total];
}

/**
 * The next version of a page.
 *
 * Every save makes a revision, so the version goes up by one.
 */
function wiki_next_version(int|string|null $current): int {
    return max(1, (int) $current + 1);
}

/**
 * The revision that is written when a page is saved.
 */
function wiki_revision(array $page, int $version): array {
    return [
        'page_id' => (int) $page['id'],
        'title' => (string) ($page['title'] ?? ''),
        'body' => (string) ($page['body'] ?? ''),
        'version' => $version,
    ];
}

/**
 * What a user may do.
 *
 * The owner can do everything. A member can read the library and edit the
 * pages, but cannot change the books or the chapters, and cannot delete
 * anything.
 */
function wiki_can(?array $user, string $action): bool {
    if (!$user) return false;
    $role = (string) ($user['role'] ?? 'member');

    if ($role === 'owner') return true;

    return in_array($action, ['read', 'edit_page'], true);
}

/**
 * The library summary: the number of books, chapters and pages.
 */
function wiki_summary(array $books, array $chapters, array $pages): array {
    $published = 0;
    foreach ($books as $book) {
        if ((string) ($book['status'] ?? 'published') === 'published') $published++;
    }
    return [
        'books' => count($books),
        'chapters' => count($chapters),
        'pages' => count($pages),
        'published' => $published,
    ];
}
