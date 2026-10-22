<?php
declare(strict_types=1);

/**
 * The kanban domain.
 *
 * The rules of a board: the columns a card can be in, the order the cards
 * are in, how many cards a column may hold, when a card is overdue and who
 * may look at which project.
 *
 * Pure functions, no database access, so the rules can be unit tested on
 * their own.
 */

/** The columns of the board, in the order they are shown. */
const KANBAN_COLUMNS = ['backlog', 'todo', 'in_progress', 'review', 'done'];

/** The priorities a card can have, from calmest to loudest. */
const KANBAN_PRIORITIES = ['low', 'normal', 'medium', 'high', 'urgent'];

/** How many cards a column may hold. Zero means no limit. */
const KANBAN_WIP_LIMITS = [
    'in_progress' => 3,
    'review' => 2,
];

/** True when the status is a column of the board. */
function kanban_is_column(mixed $status): bool {
    return in_array((string) $status, KANBAN_COLUMNS, true);
}

/** True when the priority is one the board knows. */
function kanban_is_priority(mixed $priority): bool {
    return in_array((string) $priority, KANBAN_PRIORITIES, true);
}

/** The label of a column, for the board. */
function kanban_column_label(string $status): string {
    return match ($status) {
        'backlog' => 'Backlog',
        'todo' => 'To do',
        'in_progress' => 'In progress',
        'review' => 'Review',
        'done' => 'Done',
        default => ucfirst(str_replace('_', ' ', $status)),
    };
}

/**
 * The cards of one project, grouped by column.
 *
 * Each column holds the cards in the order they were placed, and the cards
 * that were never given a position keep their order by id.
 */
function kanban_board(array $tasks): array {
    $board = [];
    foreach (KANBAN_COLUMNS as $column) $board[$column] = [];

    foreach ($tasks as $task) {
        $status = (string) ($task['status'] ?? 'backlog');
        if (!kanban_is_column($status)) continue;
        $board[$status][] = $task;
    }

    foreach ($board as $column => $cards) {
        usort($cards, function (array $a, array $b): int {
            $left = (int) ($a['position'] ?? 0);
            $right = (int) ($b['position'] ?? 0);
            return $left === $right ? ((int) $a['id'] <=> (int) $b['id']) : $left <=> $right;
        });
        $board[$column] = $cards;
    }

    return $board;
}

/**
 * The position a new card gets at the end of a column.
 */
function kanban_next_position(array $tasks, string $status): int {
    $positions = [];
    foreach ($tasks as $task) {
        if ((string) ($task['status'] ?? '') === $status) {
            $positions[] = (int) ($task['position'] ?? 0);
        }
    }
    return $positions ? max($positions) + 1 : 1;
}

/**
 * Check that a column is not over its limit.
 *
 * Returns an error message, or null when there is room. The card that is
 * being moved is not counted, so a card can always be moved inside its own
 * column.
 */
function kanban_check_wip(string $status, array $tasks, ?int $movingId = null): ?string {
    $limit = KANBAN_WIP_LIMITS[$status] ?? 0;
    if ($limit <= 0) return null;

    $count = 0;
    foreach ($tasks as $task) {
        if ((string) ($task['status'] ?? '') !== $status) continue;
        if ($movingId !== null && (int) $task['id'] === $movingId) continue;
        $count++;
    }

    if ($count >= $limit) {
        return kanban_column_label($status) . " is limited to {$limit} card" . ($limit === 1 ? '' : 's') . '.';
    }
    return null;
}

/**
 * Check a card before it is saved.
 *
 * The project has to exist, the status has to be a column, the priority has
 * to be one the board knows and the due date has to be a date.
 */
function kanban_validate_task(array $values, array $projects): ?string {
    $projectId = (int) ($values['project_id'] ?? 0);
    $known = false;
    foreach ($projects as $project) {
        if ((int) $project['id'] === $projectId) { $known = true; break; }
    }
    if (!$known) return 'The project does not exist.';

    $status = (string) ($values['status'] ?? 'backlog');
    if (!kanban_is_column($status)) return '"' . $status . '" is not a column of the board.';

    $priority = (string) ($values['priority'] ?? 'medium');
    if ($priority !== '' && !kanban_is_priority($priority)) {
        return '"' . $priority . '" is not a priority.';
    }

    $due = (string) ($values['due_date'] ?? '');
    if ($due !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $due)) {
        return 'The due date has to be written as YYYY-MM-DD.';
    }

    return null;
}

/**
 * Check a move.
 *
 * The card has to exist, the column has to be one of the board and the
 * column must not be over its limit.
 */
function kanban_validate_move(?array $task, string $status, array $tasks): ?string {
    if (!$task) return 'The card does not exist.';
    if (!kanban_is_column($status)) return '"' . $status . '" is not a column of the board.';
    return kanban_check_wip($status, $tasks, (int) $task['id']);
}

/**
 * The new positions of the cards of a column after a move.
 *
 * The moved card takes the place it was dropped at and the cards that were
 * in between move one place.
 */
function kanban_reorder(array $cards, int $movingId, int $position): array {
    $others = [];
    $moving = null;
    foreach ($cards as $card) {
        if ((int) $card['id'] === $movingId) { $moving = $card; continue; }
        $others[] = $card;
    }
    if ($moving === null) return [];

    $index = max(0, min($position, count($others)));
    array_splice($others, $index, 0, [$moving]);

    $result = [];
    $place = 1;
    foreach ($others as $card) {
        $result[] = ['id' => (int) $card['id'], 'position' => $place++];
    }
    return $result;
}

/** True when a card is past its due date and not finished yet. */
function kanban_is_overdue(array $task, ?string $today = null): bool {
    $due = (string) ($task['due_date'] ?? '');
    if ($due === '') return false;
    if ((string) ($task['status'] ?? '') === 'done') return false;
    $today = $today ?? gmdate('Y-m-d');
    return $due < $today;
}

/**
 * The swimlanes of a board.
 *
 * A swimlane is the assignee of a card; the cards nobody has taken are in
 * the "unassigned" lane.
 */
function kanban_swimlanes(array $tasks): array {
    $lanes = [];
    foreach ($tasks as $task) {
        $assignee = trim((string) ($task['assignee'] ?? ''));
        $lane = $assignee === '' ? 'unassigned' : $assignee;
        $lanes[$lane][] = $task;
    }
    ksort($lanes);
    return $lanes;
}

/**
 * True when the user may look at the project.
 *
 * The owner can, and so can a member when the project is not private.
 */
function kanban_can_view(?array $project, ?array $user): bool {
    if (!$user) return false;
    if (!$project) return false;
    if ((string) ($project['owner'] ?? '') === (string) $user['name']) return true;
    if (($user['role'] ?? '') === 'owner') return true;
    return (string) ($project['status'] ?? 'active') !== 'private';
}

/**
 * The summary of a board: the cards per column and the overdue ones.
 */
function kanban_summary(array $tasks, ?string $today = null): array {
    $counts = [];
    foreach (KANBAN_COLUMNS as $column) $counts[$column] = 0;
    $overdue = 0;

    foreach ($tasks as $task) {
        $status = (string) ($task['status'] ?? '');
        if (isset($counts[$status])) $counts[$status]++;
        if (kanban_is_overdue($task, $today)) $overdue++;
    }

    return ['counts' => $counts, 'total' => count($tasks), 'overdue' => $overdue];
}
