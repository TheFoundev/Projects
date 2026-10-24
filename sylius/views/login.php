<div class="card" style="max-width:430px;margin:40px auto">
  <h1>Sign in</h1>
  <p class="muted">Use the account registered on this instance.</p>
  <form method="post" action="/login" style="margin-top:18px">
    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
    <div class="field"><label for="email">Email</label><input id="email" type="email" name="email" required autocomplete="email"></div>
    <div class="field"><label for="password">Password</label><input id="password" type="password" name="password" required autocomplete="current-password"></div>
    <button class="btn primary" type="submit">Sign in</button>
    <a href="/register" style="margin-left:10px">Create account</a>
  </form>
</div>
