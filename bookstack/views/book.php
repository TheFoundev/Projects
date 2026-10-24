<?php /** @var array $config */ ?>
<h1><?= e($tree['book']['title']) ?></h1>
<p class="muted"><?= e($tree['book']['description'] ?? '') ?> · <?= e($tree['book']['status'] ?? 'published') ?></p>

<?php if (!$tree['chapters']): ?>
  <p class="muted">This book has no chapters yet.</p>
<?php endif; ?>

<?php foreach ($tree['chapters'] as $entry): ?>
  <section class="column">
    <header><strong><?= e($entry['chapter']['title']) ?></strong>
      <span class="count"><?= e(count($entry['pages'])) ?> pages</span></header>
    <?php foreach ($entry['pages'] as $page): ?>
      <div class="card">
        <a href="/pages/<?= e($page['id']) ?>"><?= e($page['title']) ?></a>
        <div class="meta">
          <span class="pill">v<?= e($page['version'] ?? 1) ?></span>
          <?php if (!empty($page['tags'])): ?><span class="pill"><?= e($page['tags']) ?></span><?php endif; ?>
        </div>
      </div>
    <?php endforeach; ?>
    <?php if (!$entry['pages']): ?><p class="muted small">No pages in this chapter.</p><?php endif; ?>
  </section>
<?php endforeach; ?>
