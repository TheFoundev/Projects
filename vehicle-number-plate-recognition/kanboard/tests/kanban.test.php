<?php
declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

fwrite(STDOUT, "kanban tests\n");

// ---------------------------------------------------------------------------
// The rules
// ---------------------------------------------------------------------------

assert_true(kanban_is_column('backlog'), 'backlog is a column of the board');
assert_true(kanban_is_column('done'), 'done is a column of the board');
assert_true(!kanban_is_column('archive'), 'archive is not a column of the board');
assert_true(kanban_is_priority('urgent'), 'urgent is a priority');
assert_true(kanban_is_priority('normal'), 'normal is a priority');
assert_true(!kanban_is_priority('critical'), 'critical is not a priority');
assert_same('In progress', kanban_column_label('in_progress'), 'the column has a label');

// ---------------------------------------------------------------------------
// The board
// ---------------------------------------------------------------------------

$tasks = [
    ['id' => 3, 'title' => 'Third', 'status' => 'todo', 'position' => 1],
    ['id' => 1, 'title' => 'First', 'status' => 'todo', 'position' => 2],
    ['id' => 2, 'title' => 'Second', 'status' => 'backlog', 'position' => 1],
    ['id' => 4, 'title' => 'Fourth', 'status' => 'done', 'position' => 1],
];

$board = kanban_board($tasks);
assert_same(5, count($board), 'the board has every column');
assert_same(2, count($board['todo']), 'the todo column holds two cards');
assert_same('Third', $board['todo'][0]['title'], 'the cards are in the order they were placed');
assert_same('First', $board['todo'][1]['title'], 'the second card follows');
assert_same(1, count($board['done']), 'the done column holds one card');
assert_same(0, count($board['review']), 'the review column is empty');

$next = kanban_next_position($tasks, 'todo');
assert_same(3, $next, 'a new card goes to the end of the column');
assert_same(1, kanban_next_position($tasks, 'review'), 'a new card in an empty column starts at one');

// ---------------------------------------------------------------------------
// The work in progress limit
// ---------------------------------------------------------------------------

$full = [
    ['id' => 1, 'status' => 'in_progress'],
    ['id' => 2, 'status' => 'in_progress'],
    ['id' => 3, 'status' => 'in_progress'],
];
assert_true(kanban_check_wip('in_progress', $full) !== null, 'a full column is reported');
assert_true(kanban_check_wip('backlog', $full) === null, 'a column without a limit is always fine');
assert_true(kanban_check_wip('in_progress', $full, 1) === null, 'the card being moved is not counted against the limit');
assert_true(kanban_check_wip('in_progress', [['id' => 1, 'status' => 'in_progress']]) === null, 'a column with room is fine');

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

$projects = [['id' => 1, 'name' => 'Website']];
assert_true(kanban_validate_task(['project_id' => 1, 'status' => 'todo'], $projects) === null, 'a good card is accepted');
assert_contains((string) kanban_validate_task(['project_id' => 99, 'status' => 'todo'], $projects), 'does not exist', 'a card needs a real project');
assert_contains((string) kanban_validate_task(['project_id' => 1, 'status' => 'nope'], $projects), 'not a column', 'the status has to be a column');
assert_contains((string) kanban_validate_task(['project_id' => 1, 'status' => 'todo', 'priority' => 'critical'], $projects), 'not a priority', 'the priority has to be one the board knows');
assert_contains((string) kanban_validate_task(['project_id' => 1, 'status' => 'todo', 'due_date' => '23-04-2026'], $projects), 'YYYY-MM-DD', 'the due date has to be a date');
assert_true(kanban_validate_task(['project_id' => 1, 'status' => 'todo', 'due_date' => '2026-04-23'], $projects) === null, 'a good due date is accepted');

assert_contains((string) kanban_validate_move(null, 'todo', []), 'does not exist', 'a move needs a card');
assert_contains((string) kanban_validate_move(['id' => 1], 'nope', []), 'not a column', 'a move needs a real column');

// ---------------------------------------------------------------------------
// Reordering
// ---------------------------------------------------------------------------

$cards = [
    ['id' => 1, 'position' => 1],
    ['id' => 2, 'position' => 2],
    ['id' => 3, 'position' => 3],
];
$reordered = kanban_reorder($cards, 3, 0);
assert_same(3, $reordered[0]['id'], 'the moved card takes the first place');
assert_same(1, $reordered[1]['id'], 'the other cards move one place');
assert_same(1, $reordered[0]['position'], 'the positions are numbered from one');
assert_same(3, count($reordered), 'every card is placed');

// The place is a zero based index into the column.
$reordered = kanban_reorder($cards, 1, 1);
assert_same(2, $reordered[0]['id'], 'the card before it stays first');
assert_same(1, $reordered[1]['id'], 'the moved card takes the place it was dropped at');

// ---------------------------------------------------------------------------
// Overdue cards
// ---------------------------------------------------------------------------

assert_true(kanban_is_overdue(['due_date' => '2026-04-01', 'status' => 'todo'], '2026-04-23'), 'a card past its due date is overdue');
assert_true(!kanban_is_overdue(['due_date' => '2026-04-30', 'status' => 'todo'], '2026-04-23'), 'a card before its due date is not overdue');
assert_true(!kanban_is_overdue(['due_date' => '2026-04-01', 'status' => 'done'], '2026-04-23'), 'a finished card is not overdue');
assert_true(!kanban_is_overdue(['status' => 'todo'], '2026-04-23'), 'a card without a due date is not overdue');

// ---------------------------------------------------------------------------
// Swimlanes and access
// ---------------------------------------------------------------------------

$lanes = kanban_swimlanes([
    ['id' => 1, 'title' => 'A', 'assignee' => 'Ana'],
    ['id' => 2, 'title' => 'B', 'assignee' => ''],
    ['id' => 3, 'title' => 'C', 'assignee' => 'Ana'],
]);
assert_same(2, count($lanes), 'there are two lanes');
assert_same(2, count($lanes['Ana']), 'the lane holds the cards of that person');
assert_same(1, count($lanes['unassigned']), 'the cards nobody has taken are in their own lane');

assert_true(kanban_can_view(['owner' => 'Ana', 'status' => 'active'], ['name' => 'Ana', 'role' => 'member']), 'the owner can see the project');
assert_true(kanban_can_view(['owner' => 'Ana', 'status' => 'active'], ['name' => 'Bo', 'role' => 'owner']), 'an owner can see every project');
assert_true(kanban_can_view(['owner' => 'Ana', 'status' => 'active'], ['name' => 'Bo', 'role' => 'member']), 'a member can see an open project');
assert_true(!kanban_can_view(['owner' => 'Ana', 'status' => 'private'], ['name' => 'Bo', 'role' => 'member']), 'a member cannot see a private project');
assert_true(!kanban_can_view(['owner' => 'Ana', 'status' => 'active'], null), 'an anonymous visitor cannot see a project');

// ---------------------------------------------------------------------------
// The summary
// ---------------------------------------------------------------------------

$summary = kanban_summary([
    ['id' => 1, 'status' => 'todo', 'due_date' => '2026-04-01'],
    ['id' => 2, 'status' => 'todo'],
    ['id' => 3, 'status' => 'done'],
], '2026-04-23');
assert_same(2, $summary['counts']['todo'], 'the summary counts the cards per column');
assert_same(1, $summary['counts']['done'], 'the summary counts the finished cards');
assert_same(3, $summary['total'], 'the summary counts every card');
assert_same(1, $summary['overdue'], 'the summary counts the overdue cards');

// ---------------------------------------------------------------------------
// The database
// ---------------------------------------------------------------------------

$db = test_db();
$count = (int) $db->pdo()->query('SELECT COUNT(*) FROM projects')->fetchColumn();
assert_true($count >= 1, 'the project was stored');

fwrite(STDOUT, sprintf("%d assertions, %d failures\n", $GLOBALS['kanban_assertions'], $GLOBALS['kanban_failures']));
exit($GLOBALS['kanban_failures'] === 0 ? 0 : 1);
