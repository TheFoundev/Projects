<?php
/**
 * Enter marks for a student.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$error = null;
$rollNo = trim((string) ($_POST['rno'] ?? ''));
$className = trim((string) ($_POST['class_name'] ?? ''));
$marks = [1, 2, 3, 4, 5];

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    $values = [];
    foreach ($marks as $index) {
        $values[$index] = (int) ($_POST['p' . $index] ?? 0);
    }

    if ($className === '') {
        $error = 'Please select class';
    } elseif ($rollNo === '') {
        $error = 'Please enter roll number';
    } elseif (!ctype_digit($rollNo)) {
        $error = 'Please enter valid roll number';
    } else {
        $outOfRange = false;
        foreach ($values as $value) {
            if ($value < 0 || $value > 100) {
                $outOfRange = true;
            }
        }
        if ($outOfRange) {
            $error = 'Please enter valid marks';
        } else {
            $student = db_one(
                'SELECT name FROM students WHERE rno = :rno AND class_name = :class',
                [':rno' => $rollNo, ':class' => $className]
            );
            if ($student === null) {
                $error = 'No student with that roll number in the selected class';
            } else {
                $total = array_sum($values);
                $percentage = $total / 5;
                try {
                    // Portable upsert: update the existing row, insert when
                    // there is none. Written this way so the same code runs on
                    // MySQL and SQLite without driver specific syntax.
                    $params = [
                        ':name' => $student['name'],
                        ':rno' => (int) $rollNo,
                        ':class' => $className,
                        ':p1' => $values[1],
                        ':p2' => $values[2],
                        ':p3' => $values[3],
                        ':p4' => $values[4],
                        ':p5' => $values[5],
                        ':marks' => $total,
                        ':percentage' => $percentage,
                    ];
                    $updated = db_query(
                        'UPDATE result SET
                            name = :name, p1 = :p1, p2 = :p2, p3 = :p3, p4 = :p4, p5 = :p5,
                            marks = :marks, percentage = :percentage
                         WHERE rno = :rno AND class_name = :class',
                        $params
                    )->rowCount();
                    if ($updated === 0) {
                        db_query(
                            'INSERT INTO result
                                (name, rno, class_name, p1, p2, p3, p4, p5, marks, percentage)
                             VALUES
                                (:name, :rno, :class, :p1, :p2, :p3, :p4, :p5, :marks, :percentage)',
                            $params
                        );
                    }
                    flash('Result saved.');
                } catch (PDOException $exception) {
                    $error = 'Invalid details';
                }
            }
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
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <link rel="stylesheet" href="./css/home.css">
    <link rel="stylesheet" type="text/css" href="./css/form.css" media="all">
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
    <link rel="stylesheet" href="./css/font-awesome-4.7.0/css/font-awesome.css">
    <title>Add Results</title>
</head>
<body>

    <div class="title">
        <a href="dashboard.php"><img src="./images/logo1.png" alt="" class="logo"></a>
        <span class="heading">Dashboard</span>
        <a href="logout.php" style="color: white"><span class="fa fa-sign-out fa-2x">Logout</span></a>
    </div>

    <div class="nav">
        <ul>
            <li class="dropdown" onclick="toggleDisplay('1')">
                <a href="" class="dropbtn">Classes &nbsp;
                    <span class="fa fa-angle-down"></span>
                </a>
                <div class="dropdown-content" id="1">
                    <a href="add_classes.php">Add Class</a>
                    <a href="manage_classes.php">Manage Class</a>
                </div>
            </li>
            <li class="dropdown" onclick="toggleDisplay('2')">
                <a href="#" class="dropbtn">Students &nbsp;
                    <span class="fa fa-angle-down"></span>
                </a>
                <div class="dropdown-content" id="2">
                    <a href="add_students.php">Add Students</a>
                    <a href="manage_students.php">Manage Students</a>
                </div>
            </li>
            <li class="dropdown" onclick="toggleDisplay('3')">
                <a href="#" class="dropbtn">Results &nbsp;
                    <span class="fa fa-angle-down"></span>
                </a>
                <div class="dropdown-content" id="3">
                    <a href="add_results.php">Add Results</a>
                    <a href="manage_results.php">Manage Results</a>
                </div>
            </li>
        </ul>
    </div>

    <div class="main">
        <?php echo render_flash(); ?>
        <?php if ($error !== null) : ?>
            <p class="error"><?php echo e($error); ?></p>
        <?php endif; ?>
        <form action="add_results.php" method="post">
            <fieldset>
                <legend>Enter Marks</legend>

                <select name="class_name">
                    <option selected disabled value="">Select Class</option>
                    <?php foreach ($classes as $class) : ?>
                        <option value="<?php echo e($class['name']); ?>" <?php echo $className === $class['name'] ? 'selected' : ''; ?>><?php echo e($class['name']); ?></option>
                    <?php endforeach; ?>
                </select>

                <input type="text" name="rno" placeholder="Roll No" value="<?php echo e($rollNo); ?>">
                <input type="text" name="p1" placeholder="Paper 1">
                <input type="text" name="p2" placeholder="Paper 2">
                <input type="text" name="p3" placeholder="Paper 3">
                <input type="text" name="p4" placeholder="Paper 4">
                <input type="text" name="p5" placeholder="Paper 5">
                <?php echo csrf_field(); ?>
                <input type="submit" value="Submit">
            </fieldset>
        </form>
    </div>

</body>
</html>
