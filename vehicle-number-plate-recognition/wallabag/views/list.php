/** @var array $resource @var array $items @var array $config */
?>
<div class="row" style="justify-content:space-between;margin-bottom:14px">
  <div><h1><?= e($resource['label']) ?></h1><p class="muted"><?= e($resource['description'] ?? '') ?></p></div>
  <?php if ($currentUser): ?><a class="btn primary" href="/r/<?= e($resource['name']) ?>/new">+ New</a><?php endif; ?>
</div>
<form class="toolbar" method="get" action="/r/<?= e($resource['name']) ?>">
  <input type="search" name="q" value="<?= e($_GET['q'] ?? '') ?>" placeholder="Search <?= e(strtolower($resource['label'])) ?>…">
  <button class="btn" type="submit">Search</button>
</form>
<?php if (!$items): ?>
  <div class="card empty"><h2>Nothing here yet</h2><p>Create the first record to get started.</p></div>
<?php else: ?>
<table>
  <thead><tr><th>#</th>
    <?php foreach ($resource['fields'] as $name => $field): ?><th><?= e($field['label'] ?? $name) ?></th><?php endforeach; ?>
    <th>Created</th><th></th>
  </tr></thead>
  <tbody>
  <?php foreach ($items as $item): ?>
    <tr>
      <td class="muted"><?= (int) $item['id'] ?></td>
      <?php foreach ($resource['fields'] as $name => $field): ?>
        <td><?= e(mb_strimwidth((string) ($item[$name] ?? '—'), 0, 100, '…')) ?></td>
      <?php endforeach; ?>
      <td class="muted"><?= e(substr((string) $item['created_at'], 0, 10)) ?></td>
      <td style="white-space:nowrap">
        <?php if (($config['special'] ?? '') === 'wiki' && $resource['name'] === 'pages'): ?>
          <a class="btn" href="/pages/<?= (int) $item['id'] ?>">Read</a>
        <?php endif; ?>
        <?php if ($currentUser): ?><a class="btn" href="/r/<?= e($resource['name']) ?>/<?= (int) $item['id'] ?>/edit">Edit</a>
        <form method="post" action="/r/<?= e($resource['name']) ?>/<?= (int) $item['id'] ?>/delete" class="inline" onsubmit="return confirm('Delete this record?')">
          <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>"><button class="btn danger" type="submit">Delete</button>
        </form><?php endif; ?>
      </td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
<?php endif; ?>
