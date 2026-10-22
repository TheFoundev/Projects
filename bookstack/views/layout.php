<?php /** @var array $config */ ?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><?= e($title ?? $config['name']) ?> · <?= e($config['name']) ?></title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="topbar">
  <a class="brand" href="/"><span class="mark"><?= e(strtoupper(substr($config['name'], 0, 1))) ?></span>
    <span><strong><?= e($config['name']) ?></strong><small><?= e($config['tagline']) ?></small></span></a>
  <nav>
    <?php if (($config['special'] ?? '') === 'wiki'): ?>
      <a href="/search">Search</a>
    <?php endif; ?>
    <?php foreach ($config['resources'] as $r): ?>
      <a href="/r/<?= e($r['name']) ?>"><?= e($r['label']) ?></a>
    <?php endforeach; ?>
    <?php if ($currentUser): ?>
      <span class="who"><?= e($currentUser['name']) ?></span>
      <form method="post" action="/logout" class="inline"><input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>"><button class="link">Sign out</button></form>
    <?php else: ?>
      <a href="/login">Sign in</a>
    <?php endif; ?>
  </nav>
</header>
<main>
  <?php if ($flash = take_flash()): ?>
    <div class="flash <?= e($flash['type']) ?>"><?= e($flash['message']) ?></div>
  <?php endif; ?>
  <?php require APP_ROOT . '/views/' . $view . '.php'; ?>
</main>
<footer><?= e($config['name']) ?> · an original Foundev implementation</footer>
</body>
</html>
