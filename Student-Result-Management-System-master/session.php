<?php
/**
 * Authentication guard for the admin area.
 *
 * Including this file requires a valid, non-expired administrator session and
 * ends the request with a redirect when there is none.
 */

declare(strict_types=1);

require_once __DIR__ . '/init.php';

$currentUser = $_SESSION['login_user'] ?? null;
if (!is_string($currentUser) || $currentUser === '') {
    flash('Please sign in to continue.', 'error');
    header('Location: login.php');
    exit;
}

// Idle timeout: an abandoned session stops working after SESSION_IDLE_TIMEOUT.
$lastSeen = (int) ($_SESSION['last_seen'] ?? 0);
$now = time();
if ($lastSeen > 0 && ($now - $lastSeen) > SESSION_IDLE_TIMEOUT) {
    unset($_SESSION['login_user'], $_SESSION['last_seen']);
    session_regenerate_id(true);
    flash('Your session expired. Please sign in again.', 'error');
    header('Location: login.php');
    exit;
}
$_SESSION['last_seen'] = $now;

// The session must still refer to an administrator that exists in the
// database. This uses a prepared statement, so the value cannot be injected.
$adminRow = db_one('SELECT userid FROM admin_login WHERE userid = :userid', [
    ':userid' => $currentUser,
]);
if ($adminRow === null) {
    unset($_SESSION['login_user'], $_SESSION['last_seen']);
    session_regenerate_id(true);
    flash('Your account is no longer available.', 'error');
    header('Location: login.php');
    exit;
}

/** True when the signed-in administrator exists. */
function current_admin(): string
{
    return (string) ($_SESSION['login_user'] ?? '');
}
