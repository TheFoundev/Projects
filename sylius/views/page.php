<div class="card">
  <p class="muted">Revision <?= (int) ($page['version'] ?? 1) ?></p>
  <h1><?= e($page['title']) ?></h1>
  <pre class="body"><?= e($page['body']) ?></pre>
  <div class="row" style="margin-top:18px">
    <?php if ($currentUser): ?><a class="btn primary" href="/r/pages/<?= (int) $page['id'] ?>/edit">Edit page</a><?php endif; ?>
    <a class="btn" href="/r/pages">All pages</a>
  </div>
</div>
<?php if ($revisions): ?>
<div class="card" style="margin-top:16px"><h2>Revision history</h2>
  <?php foreach ($revisions as $rev): ?><div class="muted" style="padding:6px 0">v<?= (int) $rev['version'] ?> · <?= e($rev['created_at']) ?> · <?= e($rev['title']) ?></div><?php endforeach; ?>
</div>
<?php endif; ?>
