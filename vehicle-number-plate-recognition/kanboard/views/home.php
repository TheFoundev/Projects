<h1><?= e($config['name']) ?></h1>
<p class="muted"><?= e($config['description']) ?></p>
<div class="grid" style="margin-top:20px">
<?php foreach ($counts as $name => $count): ?>
  <a class="card stat" href="/r/<?= e($name) ?>" style="color:inherit;text-decoration:none">
    <span class="muted"><?= e($labels[$name]) ?></span><b><?= (int) $count ?></b>
    <span class="muted">records</span>
  </a>
<?php endforeach; ?>
</div>
<div class="card" style="margin-top:18px">
  <h2>Getting started</h2>
  <p class="muted"><?= $currentUser ? 'You are signed in. Use the navigation above to browse and create records.' : 'Browse freely, then sign in or create the first account to edit.' ?></p>
  <?php if (!$currentUser): ?><a class="btn primary" href="/register">Create an account</a><?php endif; ?>
</div>
