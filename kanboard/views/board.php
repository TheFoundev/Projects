<?php /** @var array $config */ ?>
<?php
$currentProjectId = (int) ($project['id'] ?? 0);
?>
<div class="board-head">
  <div>
    <h1>Board</h1>
    <?php if ($project): ?>
      <p class="muted">
        <?= e($project['name']) ?>
        · <?= e($summary['total']) ?> cards
        · <?= e($summary['overdue']) ?> overdue
      </p>
    <?php else: ?>
      <p class="muted">No project to show.</p>
    <?php endif; ?>
  </div>
  <?php if (count($projects) > 1): ?>
    <form method="get" action="/board" class="inline">
      <select name="project" onchange="this.form.submit()">
        <?php foreach ($projects as $option): ?>
          <option value="<?= e($option['id']) ?>" <?= (int) $option['id'] === $currentProjectId ? 'selected' : '' ?>>
            <?= e($option['name']) ?>
          </option>
        <?php endforeach; ?>
      </select>
    </form>
  <?php endif; ?>
</div>

<?php if ($project): ?>
  <?php if ($summary['overdue'] > 0): ?>
    <p class="flash warn"><?= e($summary['overdue']) ?> card<?= $summary['overdue'] === 1 ? ' is' : 's are' ?> past the due date.</p>
  <?php endif; ?>

  <div class="board">
    <?php foreach (KANBAN_COLUMNS as $column): ?>
      <?php $cards = $board[$column] ?? []; ?>
      <?php $limit = KANBAN_WIP_LIMITS[$column] ?? 0; ?>
      <section class="column">
        <header>
          <strong><?= e(kanban_column_label($column)) ?></strong>
          <span class="count"><?= e(count($cards)) ?><?= $limit ? '/' . e($limit) : '' ?></span>
        </header>
        <?php if ($limit && count($cards) >= $limit): ?>
          <p class="muted small">This column is full.</p>
        <?php endif; ?>
        <?php foreach ($cards as $card): ?>
          <article class="card<?= kanban_is_overdue($card) ? ' overdue' : '' ?>">
            <a href="/r/tasks/<?= e($card['id']) ?>"><?= e($card['title']) ?></a>
            <div class="meta">
              <?php if (!empty($card['priority'])): ?>
                <span class="pill prio-<?= e($card['priority']) ?>"><?= e($card['priority']) ?></span>
              <?php endif; ?>
              <?php if (!empty($card['assignee'])): ?>
                <span class="pill"><?= e($card['assignee']) ?></span>
              <?php endif; ?>
              <?php if (!empty($card['due_date'])): ?>
                <span class="pill">due <?= e($card['due_date']) ?></span>
              <?php endif; ?>
            </div>
            <?php if ($currentUser): ?>
              <form method="post" action="/r/tasks/<?= e($card['id']) ?>/move" class="inline move">
                <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
                <input type="hidden" name="status" value="<?= e($column) ?>">
                <input type="hidden" name="position" value="<?= e((int) ($card['position'] ?? 1)) ?>">
                <button class="link" name="action" value="up">↑</button>
                <button class="link" name="action" value="down">↓</button>
              </form>
            <?php endif; ?>
          </article>
        <?php endforeach; ?>
        <?php if (!$cards): ?>
          <p class="muted small">Empty.</p>
        <?php endif; ?>
      </section>
    <?php endforeach; ?>
  </div>

  <h2>Swimlanes</h2>
  <?php foreach ($lanes as $lane => $cards): ?>
    <h3><?= e($lane) ?> <span class="muted">(<?= e(count($cards)) ?>)</span></h3>
    <ul class="lane">
      <?php foreach ($cards as $card): ?>
        <li><?= e($card['title']) ?> <span class="muted">· <?= e(kanban_column_label((string) ($card['status'] ?? 'backlog'))) ?></span></li>
      <?php endforeach; ?>
    </ul>
  <?php endforeach; ?>
<?php endif; ?>
