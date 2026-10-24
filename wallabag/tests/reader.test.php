<?php
declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "reading list tests\n");

// ---------------------------------------------------------------------------
// The states
// ---------------------------------------------------------------------------

assert_true(reader_is_status('unread'), 'unread is a state of the list');
assert_true(reader_is_status('starred'), 'starred is a state of the list');
assert_true(!reader_is_status('deleted'), 'deleted is not a state of the list');
assert_true(reader_is_unread(['status' => 'unread']), 'an unread article is unread');
assert_true(!reader_is_unread(['status' => 'read']), 'a read article is not unread');

// ---------------------------------------------------------------------------
// The article rules
// ---------------------------------------------------------------------------

assert_true(reader_check_article(['title' => 'A', 'url' => 'https://example.test/a', 'site' => 'example.test']) === null, 'a good article is accepted');
assert_contains((string) reader_check_article(['url' => 'https://example.test/a', 'site' => 'example.test']), 'title', 'an article needs a title');
assert_contains((string) reader_check_article(['title' => 'A', 'site' => 'example.test']), 'url', 'an article needs a url');
assert_contains((string) reader_check_article(['title' => 'A', 'url' => 'example.test', 'site' => 'example.test']), 'http', 'the url has to be an http one');
assert_contains((string) reader_check_article(['title' => 'A', 'url' => 'https://example.test/a']), 'site', 'an article needs a site');
assert_contains((string) reader_check_article(['title' => 'A', 'url' => 'https://example.test/a', 'site' => 'x', 'status' => 'nope']), 'state the list knows', 'the status has to be one the list knows');

// ---------------------------------------------------------------------------
// The annotations
// ---------------------------------------------------------------------------

$articles = [['id' => 1, 'title' => 'A']];
assert_true(reader_check_annotation(['article_id' => 1, 'quote' => 'A quote'], $articles) === null, 'a highlight is accepted');
assert_true(reader_check_annotation(['article_id' => 1, 'note' => 'A note'], $articles) === null, 'a note is accepted');
assert_contains((string) reader_check_annotation(['article_id' => 99, 'quote' => 'x'], $articles), 'does not exist', 'an annotation needs a real article');
assert_contains((string) reader_check_annotation(['article_id' => 1], $articles), 'quote or a note', 'an annotation needs something to say');

// ---------------------------------------------------------------------------
// The tags
// ---------------------------------------------------------------------------

assert_same(['news', 'tech'], reader_tags(['tags' => 'News, Tech']), 'the tags are lowercased');
assert_same(['news'], reader_tags(['tags' => 'news, news']), 'a tag is only counted once');
assert_same([], reader_tags(['tags' => '']), 'an article without tags has none');
assert_same([], reader_tags([]), 'an article without the field has no tags');

// ---------------------------------------------------------------------------
// The list
// ---------------------------------------------------------------------------

$list = [
    ['id' => 1, 'title' => 'Alpha', 'site' => 'a.test', 'excerpt' => '', 'content' => '', 'status' => 'unread', 'tags' => 'news', 'added_at' => '2026-04-01T00:00:00Z'],
    ['id' => 2, 'title' => 'Beta', 'site' => 'b.test', 'excerpt' => '', 'content' => '', 'status' => 'read', 'tags' => 'news, tech', 'added_at' => '2026-04-02T00:00:00Z'],
    ['id' => 3, 'title' => 'Gamma', 'site' => 'c.test', 'excerpt' => '', 'content' => '', 'status' => 'unread', 'tags' => '', 'added_at' => '2026-04-03T00:00:00Z'],
];

assert_same(2, count(reader_list($list, ['status' => 'unread'])), 'the list filters by state');
assert_same(1, count(reader_list($list, ['tag' => 'tech'])), 'the list filters by tag');
assert_same(1, count(reader_list($list, ['q' => 'alpha'])), 'the list searches the title');
assert_same(0, count(reader_list($list, ['q' => 'nothing here'])), 'a search that matches nothing finds nothing');
assert_same(3, count(reader_list($list)), 'without a filter the list has everything');

$byDate = reader_list($list, [], 'added');
assert_same(3, $byDate[0]['id'], 'the newest article comes first');
$byTitle = reader_list($list, [], 'title');
assert_same(1, $byTitle[0]['id'], 'the list can be sorted by title');
$bySite = reader_list($list, [], 'site');
assert_same(1, $bySite[0]['id'], 'the list can be sorted by site');

// ---------------------------------------------------------------------------
// The counters and the tag cloud
// ---------------------------------------------------------------------------

$counts = reader_counts($list);
assert_same(2, $counts['unread'], 'the counters count the unread articles');
assert_same(1, $counts['read'], 'the counters count the read articles');
assert_same(3, $counts['total'], 'the counters count every article');

$cloud = reader_tag_cloud($list);
assert_same(2, $cloud['news'], 'the tag cloud counts the articles of a tag');
assert_same(1, $cloud['tech'], 'the tag cloud counts every tag');
assert_same('news', array_key_first($cloud), 'the most used tag comes first');

// ---------------------------------------------------------------------------
// The annotations of an article
// ---------------------------------------------------------------------------

$annotations = [
    ['id' => 2, 'article_id' => 1, 'quote' => 'second'],
    ['id' => 1, 'article_id' => 1, 'quote' => 'first'],
    ['id' => 3, 'article_id' => 2, 'quote' => 'other'],
];
$own = reader_annotations_of(1, $annotations);
assert_same(2, count($own), 'the annotations of an article are only its own');
assert_same(1, $own[0]['id'], 'the annotations are in the order they were made');

// ---------------------------------------------------------------------------
// The site and the excerpt
// ---------------------------------------------------------------------------

assert_same('example.test', reader_site_of('https://example.test/a/b'), 'the site is the host of the url');
assert_same('example.test', reader_site_of('https://www.example.test/a'), 'the www is not part of the site');
assert_same('', reader_site_of('not a url'), 'a url without a host has no site');

assert_same('Hello there', reader_excerpt_of("Hello   there"), 'the excerpt collapses the spaces');
assert_same('Hello…', reader_excerpt_of('Hello world', 5), 'a long text is cut short');

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['wiki_assertions'], $GLOBALS['wiki_failures']));
exit($GLOBALS['wiki_failures'] === 0 ? 0 : 1);
