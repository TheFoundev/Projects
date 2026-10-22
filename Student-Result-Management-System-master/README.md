# Student Result Management System

A small PHP/MySQL application for entering examination results and letting
students look them up by class and roll number.

Administrators sign in, manage classes and students, and record the five paper
marks for each student. Students read their result on a public page without an
account.

## Technology

- Back end: PHP 8.1+ with PDO (MySQL/MariaDB in production, SQLite for local
  development and tests)
- Front end: server rendered HTML with a small amount of CSS
- No framework and no Composer dependencies

## Setup

1. Point the application at a database. For a quick local run it falls back to
   a SQLite file under `data/`:

   ```bash
   export SRMS_SQLITE_PATH="$PWD/data/srms.sqlite"
   ```

   For MySQL or MariaDB use a DSN plus credentials:

   ```bash
   export SRMS_DSN="mysql:host=localhost;dbname=srms;charset=utf8mb4"
   export SRMS_DB_USER="srms"
   export SRMS_DB_PASSWORD="a-real-password"
   ```

   The tables are created automatically on first use. To provision the schema
   by hand, run `database/schema.sql`.

2. Create the first administrator. The password is hashed with bcrypt before
   it is stored:

   ```bash
   php scripts/create_admin.php admin
   ```

   The password is read from the `SRMS_ADMIN_PASSWORD` environment variable or
   from the second argument.

3. Serve the application over HTTPS with a real web server:

   ```bash
   php -S localhost:8000
   ```

   The built in server is for development only.

## Running the tests

The test suite has no external dependencies:

```bash
php tests/run.php
```

It covers the escaping helpers, the CSRF implementation, the schema and the
password handling (unit tests), and the login flow, the SQL injection attempt
on the login form, the CSRF enforcement on every form, the account lockout and
the escaping of stored data in the admin and student pages (end to end tests
against the PHP built in server).

## Security notes

- Every query uses a prepared statement. Values are never concatenated into
  SQL, so the login form is not injectable.
- Passwords are stored as bcrypt hashes. An account that still holds a
  legacy plaintext password is upgraded to a hash the first time it signs in
  successfully.
- Every state changing form carries a CSRF token that is checked with
  `hash_equals`.
- All output is escaped with `htmlspecialchars`, so stored values cannot
  inject markup.
- The session id is regenerated on sign in, the cookie is HttpOnly and
  SameSite, and an idle session expires after 30 minutes.
- Repeated failed sign in attempts lock an account for five minutes.

## Project layout

```
add_classes.php        add a class
add_results.php        enter the paper marks for a student
add_students.php       add a student
dashboard.php          admin dashboard
init.php               configuration, database access and shared helpers
login.php              administrator sign in
logout.php             sign out
manage_classes.php     list and delete classes
manage_results.php     list, update and delete results
manage_students.php    list and delete students
partials/nav.php       shared admin navigation
scripts/create_admin.php  create or reset an administrator
student.php            public result lookup
tests/                 test suite
```
