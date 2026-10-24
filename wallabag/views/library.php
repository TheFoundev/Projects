<h1>Reading library</h1>
<p class="muted">Saved articles, unread first. Open an article to annotate or archive it.</p>
<div class="grid" style="margin-top:16px">
<?php foreach ($articles as $a): ?>
  <a class="card stat" href="/read/<?= (int) $a['id'] ?>" style="color:inherit;text-decoration:none">
    <div class="row between"><span class="badge"><?= e($a['status'] ?: 'unread') ?></span><span class="badge"><?= e($a['tags'] ?: 'untagged') ?></span></div>
    <h3 style="margin:8px 0 2px"><?= e($a['title']) ?></h3>
    <p class="muted"><?= e(mb_strimwidth($a['excerpt'] ?: $a['content'] ?: '', 0, 180, '…')) ?></p>
    <span class="muted"><?= e($a['author'] ?: 'Unknown') ?> · <?= e($a['site'] ?: 'web') ?></span>
  </a>
<?php endforeach; ?>
<?php if (!$articles): ?><div class="card empty"><h2>Nothing saved yet</h2><p>Add an article from the Articles resource to start your library.</p></div><?php endif; ?>
</div>
