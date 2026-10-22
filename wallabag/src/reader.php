<?php
declare(strict_types=1);

/**
 * The reading list domain.
 *
 * The rules behind a reading list: an article is unread or read or
 * starred, an annotation belongs to a passage of an article, the tags are
 * a set, and the list can be searched and sorted.
 *
 * Pure functions, no database access, so the rules can be unit tested on
 * their own.
 */

/** The states an article can be in. */
const READER_STATUSES = ['unread', 'read', 'starred', 'archived'];

/** The kinds of annotation there are. */
const ANNOTATION_KINDS = ['highlight', 'note'];

/** True when the status is one the list knows. */
function reader_is_status(mixed $status): bool {
    return in_array((string) $status, READER_STATUSES, true);
}

/** True when the kind of annotation is one the list knows. */
function reader_is_kind(mixed $kind): bool {
    return in_array((string) $kind, ANNOTATION_KINDS, true);
}

/** True when the article is still to be read. */
function reader_is_unread(array $article): bool {
    return (string) ($article['status'] ?? 'unread') === 'unread';
}

/**
 * Check an article before it is saved.
 *
 * The article needs a title, a url and a site, and the url has to be a
 * real one. The status has to be one the list knows.
 */
function reader_check_article(array $values): ?string {
    if (trim((string) ($values['title'] ?? '')) === '') return 'The article needs a title.';
    if (trim((string) ($values['url'] ?? '')) === '') return 'The article needs a url.';

    $url = trim((string) ($values['url'] ?? ''));
    if (!preg_match('#^https?://#i', $url)) return 'The url has to start with http:// or https://.';
    if (filter_var($url, FILTER_VALIDATE_URL) === false) return 'The url is not a valid address.';

    if (trim((string) ($values['site'] ?? '')) === '') return 'The article needs a site.';

    $status = (string) ($values['status'] ?? 'unread');
    if (!reader_is_status($status)) return '"' . $status . '" is not a state the list knows.';

    return null;
}

/**
 * Check an annotation before it is saved.
 *
 * The annotation belongs to an article, and a highlight needs a quote.
 */
function reader_check_annotation(array $values, array $articles): ?string {
    $articleId = (int) ($values['article_id'] ?? 0);
    $found = false;
    foreach ($articles as $article) {
        if ((int) $article['id'] === $articleId) { $found = true; break; }
    }
    if (!$found) return 'The article does not exist.';

    // A highlight quotes the article, a note says something about it.
    $quote = trim((string) ($values['quote'] ?? ''));
    $note = trim((string) ($values['note'] ?? ''));
    if ($quote === '' && $note === '') return 'The annotation needs a quote or a note.';

    $kind = $quote !== '' ? 'highlight' : 'note';
    if (!reader_is_kind($kind)) return '"' . $kind . '" is not a kind of annotation.';

    return null;
}

/**
 * The tags of an article, as a list without the empty ones.
 */
function reader_tags(array $article): array {
    $raw = (string) ($article['tags'] ?? '');
    if (trim($raw) === '') return [];

    $tags = [];
    foreach (explode(',', $raw) as $tag) {
        $tag = trim($tag);
        if ($tag === '') continue;
        $tags[] = mb_strtolower($tag);
    }
    return array_values(array_unique($tags));
}

/**
 * The reading list.
 *
 * The articles can be filtered by state, by tag and by text, and they come
 * back in the order the list is sorted by.
 */
function reader_list(array $articles, array $filters = [], string $sort = 'added'): array {
    $status = $filters['status'] ?? null;
    $tag = isset($filters['tag']) ? mb_strtolower((string) $filters['tag']) : null;
    $query = isset($filters['q']) ? mb_strtolower(trim((string) $filters['q'])) : null;

    $items = [];
    foreach ($articles as $article) {
        if ($status !== null && $status !== '' && (string) ($article['status'] ?? 'unread') !== $status) continue;
        if ($tag !== null && $tag !== '' && !in_array($tag, reader_tags($article), true)) continue;
        if ($query !== null && $query !== '') {
            $haystack = mb_strtolower(($article['title'] ?? '') . ' ' . ($article['excerpt'] ?? '') . ' ' . ($article['content'] ?? '') . ' ' . ($article['author'] ?? ''));
            if (!str_contains($haystack, $query)) continue;
        }
        $items[] = $article;
    }

    usort($items, function (array $a, array $b) use ($sort): int {
        return match ($sort) {
            'title' => strcmp(mb_strtolower((string) $a['title']), mb_strtolower((string) $b['title'])),
            'site' => strcmp(mb_strtolower((string) $a['site']), mb_strtolower((string) $b['site'])),
            default => strcmp((string) ($b['added_at'] ?? ''), (string) ($a['added_at'] ?? '')),
        };
    });

    return $items;
}

/**
 * The counts of the list: how many articles are unread, read or starred.
 */
function reader_counts(array $articles): array {
    $counts = ['unread' => 0, 'read' => 0, 'starred' => 0, 'archived' => 0, 'total' => count($articles)];
    foreach ($articles as $article) {
        $status = (string) ($article['status'] ?? 'unread');
        if (isset($counts[$status])) $counts[$status]++;
    }
    return $counts;
}

/**
 * The tags of the whole list, with how many articles carry each of them.
 *
 * The most used tag comes first.
 */
function reader_tag_cloud(array $articles): array {
    $cloud = [];
    foreach ($articles as $article) {
        foreach (reader_tags($article) as $tag) {
            if (!isset($cloud[$tag])) $cloud[$tag] = 0;
            $cloud[$tag]++;
        }
    }
    arsort($cloud);
    return $cloud;
}

/**
 * The annotations of one article, in the order they were made.
 */
function reader_annotations_of(int $articleId, array $annotations): array {
    $own = array_values(array_filter(
        $annotations,
        fn(array $row) => (int) ($row['article_id'] ?? 0) === $articleId
    ));
    usort($own, fn($a, $b) => ((int) $a['id']) <=> ((int) $b['id']));
    return $own;
}

/**
 * The site of an article, taken from its url when it was not filled in.
 */
function reader_site_of(string $url): string {
    $host = parse_url($url, PHP_URL_HOST);
    if (!is_string($host) || $host === '') return '';
    return preg_replace('/^www\./', '', $host) ?? $host;
}

/**
 * A short excerpt of the article, when there is none.
 */
function reader_excerpt_of(string $content, int $length = 200): string {
    $text = trim(preg_replace('/\s+/u', ' ', strip_tags($content)) ?? '');
    if (mb_strlen($text) <= $length) return $text;
    return mb_substr($text, 0, $length) . '…';
}
