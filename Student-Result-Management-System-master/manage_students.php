<?php
/**
 * List and delete students.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$error = null;

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    $action = (string) ($_POST['action'] ?? '');
    if ($action === 'delete') {
        $rollNo = trim((string) ($_POST['rno'] ?? ''));
        $className = trim((string) ($_POST['class_name'] ?? ''));
        if ($rollNo === '' || !ctype_digit($rollNo) || $className === '') {
            $error = 'Invalid student reference';
        } else {
            try {
                db_query(
                    'DELETE FROM students WHERE rno = :rno AND class_name = :class',
                    [':rno' => (int) $rollNo, ':class' => $className]
                );
                flash('Student deleted.');
            } catch (PDOException $exception) {
                $error = 'Could not delete the student';
            }
        }
    }
}

$students = db_all('SELECT name, rno, class_name FROM students ORDER BY class_name, rno');
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
    <title>Manage Students</title>
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
        <?php if (count($students) > 0) : ?>
            <table>
                <caption>Manage Students</caption>
                <tr>
                    <th>NAME</th>
                    <th>ROLL NO</th>
                    <th>CLASS</th>
                    <th>ACTION</th>
                </tr>
                <?php foreach ($students as $student) : ?>
                    <tr>
                        <td><?php echo e($student['name']); ?></td>
                        <td><?php echo e($student['rno']); ?></td>
                        <td><?php echo e($student['class_name']); ?></td>
                        <td>
                            <form action="manage_students.php" method="post">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="rno" value="<?php echo e($student['rno']); ?>">
                                <input type="hidden" name="class_name" value="<?php echo e($student['class_name']); ?>">
                                <?php echo csrf_field(); ?>
                                <input type="submit" value="Delete">
                            </form>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </table>
        <?php else : ?>
            <p>0 Students</p>
        <?php endif; ?>
    </div>

    <div class="footer">
        <!-- <span>Designed & Coded By Jibin Thomas</span> -->
    </div>
</body>
</html>
