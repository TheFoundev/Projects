<?php /** @var array $config */ ?>
<h1>Reading list</h1>

<p class="muted">
  <?= e($counts['total']) ?> articles · <?= e($counts['unread']) ?> unread ·
  <?= e($counts['read']) ?> read · <?= e($counts['starred']) ?> starred
</p>

<form method="get" action="/reading" class="inline">
  <input type="search" name="q" value="<?= e((string) ($filters['q'] ?? '')) ?>" placeholder="Search the list…">
  <select name="status">
    <option value="">Any state</option>
    <?php foreach (['unread', 'read', 'starred', 'archived'] as $state): ?>
      <option value="<?= e($state) ?>" <?= (($filters['status'] ?? '') === $state) ? 'selected' : '' ?>><?= e($state) ?></option>
    <?php endforeach; ?>
  </select>
  <select name="sort">
    <option value="added" <?= $sort === 'added' ? 'selected' : '' ?>>Newest first</option>
    <option value="title" <?= $sort === 'title' ? 'selected' : '' ?>>By title</option>
    <option value="site" <?= $sort === 'site' ? 'selected' : '' ?>>By site</option>
  </select>
  <button class="link">Apply</button>
</form>

<?php if ($cloud): ?>
  <p class="muted">
    <?php foreach ($cloud as $tag => $count): ?>
      <a href="/reading?tag=<?= e($tag) ?>">#<?= e($tag) ?> (<?= e($count) ?>)</a>
    <?php endforeach; ?>
  </p>
<?php endif; ?>

<?php if (!$items): ?>
  <p class="muted">Nothing in the list matches.</p>
<?php endif; ?>

<?php foreach ($items as $article): ?>
  <article class="card">
    <div class="row between wrap gap">
      <div>
        <a href="/r/articles/<?= e($article['id']) ?>"><strong><?= e($article['title']) ?></strong></a>
        <div class="muted small"><?= e($article['site']) ?><?= !empty($article['author']) ? ' · ' . e($article['author']) : '' ?></div>
      </div>
      <span class="pill"><?= e($article['status'] ?? 'unread') ?></span>
    </div>
    <?php if (!empty($article['excerpt'])): ?>
      <p class="muted"><?= e($article['excerpt']) ?></p>
    <?php endif; ?>
    <?php if ($article['tags'] ?? ''): ?>
      <div class="meta"><?php foreach (reader_tags($article) as $tag): ?>
        <span class="pill">#<?= e($tag) ?></span>
      <?php endforeach; ?></div>
    <?php endif; ?>
  </article>
<?php endforeach; ?>
