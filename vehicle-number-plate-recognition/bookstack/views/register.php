<div class="card" style="max-width:430px;margin:40px auto">
  <h1>Create account</h1>
  <p class="muted">The first account becomes the workspace owner.</p>
  <form method="post" action="/register" style="margin-top:18px">
    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
    <div class="field"><label for="name">Name</label><input id="name" name="name" required autocomplete="name"></div>
    <div class="field"><label for="email">Email</label><input id="email" type="email" name="email" required autocomplete="email"></div>
    <div class="field"><label for="password">Password (8+ characters)</label><input id="password" type="password" name="password" minlength="8" required autocomplete="new-password"></div>
    <button class="btn primary" type="submit">Create account</button>
  </form>
</div>
