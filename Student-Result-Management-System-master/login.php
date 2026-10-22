<?php
/**
 * Administrator sign-in.
 *
 * The query is prepared and the password is verified with password_hash() /
 * password_verify(). Accounts that still hold a legacy plaintext password are
 * upgraded to a bcrypt hash the first time they sign in successfully.
 */

declare(strict_types=1);

require_once __DIR__ . '/init.php';

/** A hash of a value nobody knows, used to keep the timing of a failed
 *  lookup similar to the timing of a failed password check. */
const DUMMY_PASSWORD_HASH = '$2y$10$a93lRgDEn3kMU.WvUXn4C.azqacBPfGnk6jvK2tIzenHO/eZOOv06';

const MAX_LOGIN_ATTEMPTS = 5;
const LOGIN_LOCKOUT_SECONDS = 300;

/** Record a failed attempt and return the number of failures so far. */
function record_login_failure(string $userid): int
{
    $now = time();
    $row = db_one(
        'SELECT attempts, last_attempt FROM login_attempts WHERE userid = :userid',
        [':userid' => $userid]
    );
    $attempts = (int) ($row['attempts'] ?? 0);
    $lastAttempt = (int) ($row['last_attempt'] ?? 0);
    if ($lastAttempt > 0 && ($now - $lastAttempt) > LOGIN_LOCKOUT_SECONDS) {
        $attempts = 0;
    }
    $attempts++;

    $updated = db_query(
        'UPDATE login_attempts SET attempts = :attempts, last_attempt = :last WHERE userid = :userid',
        [':attempts' => $attempts, ':last' => $now, ':userid' => $userid]
    )->rowCount();
    if ($updated === 0) {
        db_query(
            'INSERT INTO login_attempts (userid, attempts, last_attempt) VALUES (:userid, :attempts, :last)',
            [':userid' => $userid, ':attempts' => $attempts, ':last' => $now]
        );
    }

    return $attempts;
}

/** Clear the failure counter for a user. */
function clear_login_failures(string $userid): void
{
    db_query('DELETE FROM login_attempts WHERE userid = :userid', [':userid' => $userid]);
}

/** True when the account is currently locked out. */
function login_locked_out(string $userid): bool
{
    $row = db_one(
        'SELECT attempts, last_attempt FROM login_attempts WHERE userid = :userid',
        [':userid' => $userid]
    );
    if ($row === null) {
        return false;
    }
    $attempts = (int) $row['attempts'];
    $lastAttempt = (int) $row['last_attempt'];
    if ($attempts < MAX_LOGIN_ATTEMPTS) {
        return false;
    }

    return (time() - $lastAttempt) < LOGIN_LOCKOUT_SECONDS;
}

$error = null;

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    $userid = trim((string) ($_POST['userid'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');

    if ($userid === '' || $password === '') {
        $error = 'Enter both a username and a password.';
    } elseif (login_locked_out($userid)) {
        $error = 'Too many failed attempts. Try again in a few minutes.';
    } else {
        // Prepared statement: the username can never reach the SQL parser.
        $account = db_one(
            'SELECT userid, password, password_hash FROM admin_login WHERE userid = :userid',
            [':userid' => $userid]
        );

        $verified = false;
        $legacyPlaintext = false;
        if ($account === null) {
            // Keep the timing comparable so the response does not reveal
            // whether the account exists.
            password_verify($password, DUMMY_PASSWORD_HASH);
        } elseif (!empty($account['password_hash'])) {
            $verified = password_verify($password, (string) $account['password_hash']);
            if (!$verified) {
                // Re-hash when the stored hash uses outdated parameters.
                $options = [];
                if (password_needs_rehash((string) $account['password_hash'], PASSWORD_DEFAULT, $options)) {
                    $newHash = password_hash($password, PASSWORD_DEFAULT, $options);
                    db_query(
                        'UPDATE admin_login SET password_hash = :hash WHERE userid = :userid',
                        [':hash' => $newHash, ':userid' => $userid]
                    );
                }
            }
        } elseif (isset($account['password']) && $account['password'] !== null) {
            // Legacy account with a plaintext password: verify, then upgrade.
            $legacyPlaintext = true;
            $verified = hash_equals((string) $account['password'], $password);
        }

        if ($verified) {
            if ($legacyPlaintext) {
                $newHash = password_hash($password, PASSWORD_DEFAULT);
                db_query(
                    'UPDATE admin_login SET password_hash = :hash, password = NULL WHERE userid = :userid',
                    [':hash' => $newHash, ':userid' => $userid]
                );
            }
            clear_login_failures($userid);

            // New session id on privilege change (session fixation defence).
            session_regenerate_id(true);
            $_SESSION['login_user'] = $userid;
            $_SESSION['last_seen'] = time();
            header('Location: dashboard.php');
            exit;
        }

        $attempts = record_login_failure($userid);
        if ($attempts >= MAX_LOGIN_ATTEMPTS) {
            $error = 'Too many failed attempts. Try again in a few minutes.';
        } else {
            $error = 'Invalid username or password.';
        }
    }
}

$classes = db_all('SELECT name FROM class ORDER BY name');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index Page</title>
    <link rel="stylesheet" href="css/login.css">
    <link rel="stylesheet" href="./font-awesome-4.7.0/css/font-awesome.css">
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
</head>
<body>
    <div class="title">
        <span>Student Result Management System</span>
    </div>

    <div class="main">
        <div class="login">
            <form action="login.php" method="post" name="login">
                <fieldset>
                    <legend class="heading">Admin Login</legend>
                    <?php if ($error !== null) : ?>
                        <p class="error"><?php echo e($error); ?></p>
                    <?php endif; ?>
                    <input type="text" name="userid" placeholder="Email" autocomplete="username">
                    <input type="password" name="password" placeholder="Password" autocomplete="current-password">
                    <?php echo csrf_field(); ?>
                    <input type="submit" value="Login">
                </fieldset>
            </form>
        </div>
        <div class="search">
            <form action="./student.php" method="get">
                <fieldset>
                    <legend class="heading">For Students</legend>

                    <?php echo '<select name="class">'; ?>
                    <?php echo '<option selected disabled>Select Class</option>'; ?>
                    <?php foreach ($classes as $classRow) : ?>
                        <option value="<?php echo e($classRow['name']); ?>"><?php echo e($classRow['name']); ?></option>
                    <?php endforeach; ?>
                    <?php echo '</select>'; ?>

                    <input type="text" name="rn" placeholder="Roll No">
                    <input type="submit" value="Get Result">
                </fieldset>
            </form>
        </div>
    </div>

</body>
</html>
