<article class="card">
  <div class="row between"><span class="badge"><?= e($article['status'] ?: 'unread') ?></span><span class="muted"><?= e($article['added_at'] ?: '') ?></span></div>
  <h1 style="margin-top:10px"><?= e($article['title']) ?></h1>
  <p class="muted"><?= e($article['author'] ?: 'Unknown author') ?> · <a href="<?= e($article['url']) ?>" rel="noopener noreferrer" target="_blank">original</a></p>
  <div style="white-space:pre-wrap;line-height:1.75;margin-top:18px"><?= e($article['content']) ?></div>
  <?php if ($currentUser): ?>
  <form method="post" action="/read/<?= (int) $article['id'] ?>/archive" class="inline" style="margin-top:18px">
    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
    <button class="btn">Archive article</button>
  </form>
  <?php endif; ?>
</article>
<div class="card" style="margin-top:16px">
  <h2>Annotations</h2>
  <?php foreach ($annotations as $note): ?>
    <div style="border-left:3px solid var(--brand);padding:6px 12px;margin:10px 0">
      <?php if ($note['quote']): ?><blockquote class="muted" style="margin:0 0 5px">“<?= e($note['quote']) ?>”</blockquote><?php endif; ?>
      <p><?= e($note['note']) ?></p><span class="muted"><?= e($note['author']) ?> · <?= e($note['created_at']) ?></span>
    </div>
  <?php endforeach; ?>
  <?php if (!$annotations): ?><p class="muted">No annotations yet.</p><?php endif; ?>
  <?php if ($currentUser): ?>
  <form method="post" action="/read/<?= (int) $article['id'] ?>/annotations" style="margin-top:12px">
    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
    <div class="field"><label>Quote (optional)</label><input name="quote"></div>
    <div class="field"><label>Your note</label><textarea name="note" rows="3" required></textarea></div>
    <button class="btn primary">Save annotation</button>
  </form>
  <?php else: ?><p class="muted">Sign in to annotate.</p><?php endif; ?>
</div>
