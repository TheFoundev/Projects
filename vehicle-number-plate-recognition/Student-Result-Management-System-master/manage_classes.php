<?php
/**
 * List and delete classes.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$error = null;

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    $action = (string) ($_POST['action'] ?? '');
    if ($action === 'delete') {
        $id = trim((string) ($_POST['id'] ?? ''));
        if ($id === '' || !ctype_digit($id)) {
            $error = 'Invalid class id';
        } else {
            try {
                db_query('DELETE FROM class WHERE id = :id', [':id' => (int) $id]);
                flash('Class deleted.');
            } catch (PDOException $exception) {
                $error = 'Could not delete the class';
            }
        }
    }
}

$classes = db_all('SELECT name, id FROM class ORDER BY id');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="css/home.css">
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
    <link rel="stylesheet" href="./css/font-awesome-4.7.0/css/font-awesome.css">
    <link rel="stylesheet" type='text/css' href="css/manage.css">
    <title>Manage Classes</title>
</head>
<body>

    <div class="title">
        <a href="dashboard.php"><img src="./images/logo1.png" alt="" class="logo"></a>
        <span class="heading">Dashboard</span>
        <a href="logout.php" style="color: white"><span class="fa fa-sign-out fa-2x">Logout</span></a>
    </div>

    <?php include __DIR__ . '/partials/nav.php'; ?>

    <div class="main">
        <?php echo render_flash(); ?>
        <?php if ($error !== null) : ?>
            <p class="error"><?php echo e($error); ?></p>
        <?php endif; ?>
        <?php if (count($classes) > 0) : ?>
            <table>
                <caption>Manage Classes</caption>
                <tr>
                    <th>ID</th>
                    <th>NAME</th>
                    <th>ACTION</th>
                </tr>
                <?php foreach ($classes as $class) : ?>
                    <tr>
                        <td><?php echo e($class['id']); ?></td>
                        <td><?php echo e($class['name']); ?></td>
                        <td>
                            <form action="manage_classes.php" method="post">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="<?php echo e($class['id']); ?>">
                                <?php echo csrf_field(); ?>
                                <input type="submit" value="Delete">
                            </form>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </table>
        <?php else : ?>
            <p>0 results</p>
        <?php endif; ?>
    </div>

</body>
</html>
