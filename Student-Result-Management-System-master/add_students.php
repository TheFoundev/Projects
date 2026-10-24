<?php
/**
 * Add a student.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$error = null;
$name = trim((string) ($_POST['student_name'] ?? ''));
$rollNo = trim((string) ($_POST['roll_no'] ?? ''));
$className = trim((string) ($_POST['class_name'] ?? ''));

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    if ($name === '') {
        $error = 'Please enter student name';
    } elseif ($rollNo === '') {
        $error = 'Please enter roll number';
    } elseif ($className === '') {
        $error = 'Please select class';
    } elseif (preg_match('/[a-z]/i', $rollNo) || !ctype_digit($rollNo)) {
        $error = 'Please enter valid roll number';
    } else {
        $known = db_one('SELECT id FROM class WHERE name = :name', [':name' => $className]);
        if ($known === null) {
            $error = 'Please select a valid class';
        } else {
            try {
                db_query(
                    'INSERT INTO students (name, rno, class_name) VALUES (:name, :rno, :class)',
                    [':name' => $name, ':rno' => (int) $rollNo, ':class' => $className]
                );
                flash('Student added.');
            } catch (PDOException $exception) {
                $error = 'Invalid student details';
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
    <title>Add Students</title>
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
        <form action="add_students.php" method="post">
            <fieldset>
                <legend>Add Student</legend>
                <input type="text" name="student_name" placeholder="Student Name" value="<?php echo e($name); ?>">
                <input type="text" name="roll_no" placeholder="Roll No" value="<?php echo e($rollNo); ?>">
                <select name="class_name">
                    <option selected disabled value="">Select Class</option>
                    <?php foreach ($classes as $class) : ?>
                        <option value="<?php echo e($class['name']); ?>" <?php echo $className === $class['name'] ? 'selected' : ''; ?>><?php echo e($class['name']); ?></option>
                    <?php endforeach; ?>
                </select>
                <?php echo csrf_field(); ?>
                <input type="submit" value="Submit">
            </fieldset>
        </form>
    </div>

    <div class="footer">
        <!-- <span>&copy Designed & Coded By Jibin Thomas</span> -->
    </div>
</body>
</html>
