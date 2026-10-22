<?php
/**
 * Delete and update results.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$error = null;

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    $action = (string) ($_POST['action'] ?? '');
    $className = trim((string) ($_POST['class_name'] ?? ''));
    $rollNo = trim((string) ($_POST['rno'] ?? ''));

    if ($action === 'delete') {
        if ($className === '' || $rollNo === '' || !ctype_digit($rollNo)) {
            $error = 'Invalid result reference';
        } else {
            try {
                db_query(
                    'DELETE FROM result WHERE rno = :rno AND class_name = :class',
                    [':rno' => (int) $rollNo, ':class' => $className]
                );
                flash('Result deleted.');
            } catch (PDOException $exception) {
                $error = 'Could not delete the result';
            }
        }
    } elseif ($action === 'update') {
        $values = [];
        foreach ([1, 2, 3, 4, 5] as $index) {
            $values[$index] = (int) ($_POST['p' . $index] ?? 0);
        }
        $outOfRange = false;
        foreach ($values as $value) {
            if ($value < 0 || $value > 100) {
                $outOfRange = true;
            }
        }
        if ($className === '' || $rollNo === '' || !ctype_digit($rollNo)) {
            $error = 'Invalid result reference';
        } elseif ($outOfRange) {
            $error = 'Please enter valid marks';
        } else {
            $total = array_sum($values);
            $percentage = $total / 5;
            try {
                $updated = db_query(
                    'UPDATE result SET
                        p1 = :p1, p2 = :p2, p3 = :p3, p4 = :p4, p5 = :p5,
                        marks = :marks, percentage = :percentage
                     WHERE rno = :rno AND class_name = :class',
                    [
                        ':p1' => $values[1],
                        ':p2' => $values[2],
                        ':p3' => $values[3],
                        ':p4' => $values[4],
                        ':p5' => $values[5],
                        ':marks' => $total,
                        ':percentage' => $percentage,
                        ':rno' => (int) $rollNo,
                        ':class' => $className,
                    ]
                )->rowCount();
                if ($updated === 0) {
                    $error = 'No result for that roll number and class';
                } else {
                    flash('Result updated.');
                }
            } catch (PDOException $exception) {
                $error = 'Invalid details';
            }
        }
    }
}

$classes = db_all('SELECT name FROM class ORDER BY name');
$results = db_all(
    'SELECT name, rno, class_name, p1, p2, p3, p4, p5, marks, percentage
     FROM result ORDER BY class_name, rno'
);
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
    <title>Manage Results</title>
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

        <form action="manage_results.php" method="post">
            <fieldset>
                <legend>Delete Result</legend>
                <input type="hidden" name="action" value="delete">
                <select name="class_name">
                    <option selected disabled value="">Select Class</option>
                    <?php foreach ($classes as $class) : ?>
                        <option value="<?php echo e($class['name']); ?>"><?php echo e($class['name']); ?></option>
                    <?php endforeach; ?>
                </select>
                <input type="text" name="rno" placeholder="Roll No">
                <?php echo csrf_field(); ?>
                <input type="submit" value="Delete">
            </fieldset>
        </form>
        <br><br>

        <form action="manage_results.php" method="post">
            <fieldset>
                <legend>Update Result</legend>
                <input type="hidden" name="action" value="update">
                <select name="class_name">
                    <option selected disabled value="">Select Class</option>
                    <?php foreach ($classes as $class) : ?>
                        <option value="<?php echo e($class['name']); ?>"><?php echo e($class['name']); ?></option>
                    <?php endforeach; ?>
                </select>
                <input type="text" name="rno" placeholder="Roll No">
                <input type="text" name="p1" placeholder="Paper 1">
                <input type="text" name="p2" placeholder="Paper 2">
                <input type="text" name="p3" placeholder="Paper 3">
                <input type="text" name="p4" placeholder="Paper 4">
                <input type="text" name="p5" placeholder="Paper 5">
                <?php echo csrf_field(); ?>
                <input type="submit" value="Update">
            </fieldset>
        </form>

        <table>
            <caption>Existing results</caption>
            <tr>
                <th>NAME</th><th>ROLL NO</th><th>CLASS</th>
                <th>P1</th><th>P2</th><th>P3</th><th>P4</th><th>P5</th>
                <th>MARKS</th><th>%</th>
            </tr>
            <?php foreach ($results as $result) : ?>
                <tr>
                    <td><?php echo e($result['name']); ?></td>
                    <td><?php echo e($result['rno']); ?></td>
                    <td><?php echo e($result['class_name']); ?></td>
                    <td><?php echo e($result['p1']); ?></td>
                    <td><?php echo e($result['p2']); ?></td>
                    <td><?php echo e($result['p3']); ?></td>
                    <td><?php echo e($result['p4']); ?></td>
                    <td><?php echo e($result['p5']); ?></td>
                    <td><?php echo e($result['marks']); ?></td>
                    <td><?php echo e($result['percentage']); ?></td>
                </tr>
            <?php endforeach; ?>
        </table>
    </div>

</body>
</html>
