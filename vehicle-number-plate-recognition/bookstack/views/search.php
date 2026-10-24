<?php /** @var array $config */ ?>
<h1>Search</h1>
<form method="get" action="/search" class="inline">
  <input type="search" name="q" value="<?= e($query) ?>" placeholder="Search the library…">
  <button class="link">Search</button>
</form>

<p class="muted">
  <?= e($summary['books']) ?> books · <?= e($summary['chapters']) ?> chapters ·
  <?= e($summary['pages']) ?> pages · <?= e($summary['published']) ?> published
</p>

<?php if ($query === ''): ?>
  <p class="muted">Type something to search in the books, the chapters and the pages.</p>
<?php elseif ($results['total'] === 0): ?>
  <p class="muted">Nothing matches “<?= e($query) ?>”.</p>
<?php else: ?>
  <?php if ($results['books']): ?>
    <h2>Books</h2>
    <ul class="lane">
      <?php foreach ($results['books'] as $book): ?>
        <li><a href="/books/<?= e($book['id']) ?>"><?= e($book['title']) ?></a>
          <span class="muted">· <?= e($book['status']) ?></span></li>
      <?php endforeach; ?>
    </ul>
  <?php endif; ?>
  <?php if ($results['chapters']): ?>
    <h2>Chapters</h2>
    <ul class="lane">
      <?php foreach ($results['chapters'] as $chapter): ?>
        <li><?= e($chapter['title']) ?> <span class="muted">· book <?= e($chapter['book_id']) ?></span></li>
      <?php endforeach; ?>
    </ul>
  <?php endif; ?>
  <?php if ($results['pages']): ?>
    <h2>Pages</h2>
    <ul class="lane">
      <?php foreach ($results['pages'] as $page): ?>
        <li><a href="/pages/<?= e($page['id']) ?>"><?= e($page['title']) ?></a>
          <span class="muted">· v<?= e($page['version'] ?? 1) ?></span></li>
      <?php endforeach; ?>
    </ul>
  <?php endif; ?>
<?php endif; ?>
