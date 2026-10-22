<h1>Store</h1>
<p class="muted">A small catalogue backed by the same products table used by the admin views.</p>
<div class="grid" style="margin-top:16px">
<?php foreach ($products as $p): ?>
  <div class="card stat" style="justify-content:space-between">
    <div class="row between"><span class="badge"><?= e($p['category'] ?: 'Product') ?></span><span class="badge"><?= (int) $p['stock'] ?> in stock</span></div>
    <h3 style="margin:8px 0 2px"><?= e($p['name']) ?></h3>
    <p class="muted"><?= e($p['description'] ?? '') ?></p>
    <div class="row between" style="margin-top:10px">
      <strong>$<?= number_format(((int) $p['price_cents']) / 100, 2) ?></strong>
      <form method="post" action="/cart/add/<?= (int) $p['id'] ?>" class="inline">
        <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
        <button class="btn primary" <?= (int) $p['stock'] < 1 ? 'disabled' : '' ?>>Add to cart</button>
      </form>
    </div>
  </div>
<?php endforeach; ?>
</div>
