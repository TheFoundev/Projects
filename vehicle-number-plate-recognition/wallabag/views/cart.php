<h1>Cart</h1>
<?php if (!$items): ?>
  <div class="card empty"><h2>Your cart is empty</h2><p>Browse the store and add something.</p><a class="btn primary" href="/store">Browse products</a></div>
<?php else: ?>
  <div class="card">
    <?php foreach ($items as $item): ?>
      <div class="row between" style="padding:8px 0;border-bottom:1px solid var(--line)">
        <div><strong><?= e($item['product']['name']) ?></strong><div class="muted"><?= (int) $item['quantity'] ?> × $<?= number_format($item['product']['price_cents'] / 100, 2) ?></div></div>
        <div class="row gap"><span>$<?= number_format($item['line_cents'] / 100, 2) ?></span>
          <form method="post" action="/cart/remove/<?= (int) $item['product']['id'] ?>"><input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>"><button class="btn danger">Remove</button></form>
        </div>
      </div>
    <?php endforeach; ?>
    <div class="row between" style="margin-top:14px"><strong>Total</strong><strong>$<?= number_format($total / 100, 2) ?></strong></div>
    <form method="post" action="/checkout" class="row gap" style="margin-top:14px">
      <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
      <input type="email" name="email" placeholder="Email for receipt" required>
      <button class="btn primary">Checkout</button>
    </form>
  </div>
<?php endif; ?>
