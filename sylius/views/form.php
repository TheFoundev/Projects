/** @var array $resource @var array $item @var array $errors */
?>
<div class="card" style="max-width:640px;margin:0 auto">
  <h1><?= $item ? 'Edit' : 'New' ?> <?= e($resource['label']) ?></h1>
  <?php foreach ($errors as $error): ?><div class="flash error"><?= e($error) ?></div><?php endforeach; ?>
  <form method="post" action="<?= $item ? '/r/' . e($resource['name']) . '/' . (int) $item['id'] : '/r/' . e($resource['name']) ?>">
    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
    <?php foreach ($resource['fields'] as $name => $field): ?>
      <div class="field">
        <label for="f_<?= e($name) ?>"><?= e($field['label'] ?? $name) ?><?= !empty($field['required']) ? ' *' : '' ?></label>
        <?php $value = field_value($resource['fields'], $item ?: [], $name); ?>
        <?php if (($field['type'] ?? 'text') === 'text' && !empty($field['multiline'])): ?>
          <textarea id="f_<?= e($name) ?>" name="<?= e($name) ?>" rows="6"><?= e($value) ?></textarea>
        <?php elseif (($field['type'] ?? 'text') === 'bool'): ?>
          <input type="checkbox" id="f_<?= e($name) ?>" name="<?= e($name) ?>" value="1" <?= $value ? 'checked' : '' ?>>
        <?php else: ?>
          <input id="f_<?= e($name) ?>" name="<?= e($name) ?>" type="<?= ($field['type'] ?? 'text') === 'int' ? 'number' : (($field['type'] ?? 'text') === 'real' ? 'number' : 'text') ?>" step="<?= ($field['type'] ?? '') === 'real' ? 'any' : '' ?>" value="<?= e($value) ?>">
        <?php endif; ?>
      </div>
    <?php endforeach; ?>
    <button class="btn primary" type="submit">Save</button>
    <a class="btn" href="/r/<?= e($resource['name']) ?>">Cancel</a>
  </form>
</div>
