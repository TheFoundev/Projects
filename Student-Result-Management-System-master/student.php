<?php
/**
 * Student-facing result page.
 *
 * The class name and roll number are read from the query string and used only
 * through prepared statements; every value printed into the page is escaped.
 */

declare(strict_types=1);

require_once __DIR__ . '/init.php';

$class = trim((string) ($_GET['class'] ?? ''));
$rollNo = trim((string) ($_GET['rn'] ?? ''));

$error = null;
$student = null;
$result = null;

if ($class === '') {
    $error = 'Please select your class';
} elseif ($rollNo === '') {
    $error = 'Please enter your roll number';
} elseif (preg_match('/[a-z]/i', $rollNo) || !ctype_digit($rollNo)) {
    $error = 'Please enter valid roll number';
} else {
    $student = db_one(
        'SELECT name, rno, class_name FROM students WHERE rno = :rno AND class_name = :class',
        [':rno' => $rollNo, ':class' => $class]
    );
    $result = db_one(
        'SELECT name, rno, class_name, p1, p2, p3, p4, p5, marks, percentage
         FROM result WHERE rno = :rno AND class_name = :class',
        [':rno' => $rollNo, ':class' => $class]
    );
    if ($result === null) {
        $error = 'no result';
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="./css/student.css">
    <title>Result</title>
</head>
<body>
    <?php if ($error !== null) : ?>
        <p class="error"><?php echo e($error); ?></p>
    <?php else : ?>
        <div class="container">
            <div class="details">
                <span>Name:</span> <?php echo e($student['name']); ?> <br>
                <span>Class:</span> <?php echo e($class); ?> <br>
                <span>Roll No:</span> <?php echo e($rollNo); ?> <br>
            </div>

            <div class="main">
                <div class="s1">
                    <p>Subjects</p>
                    <p>Paper 1</p>
                    <p>Paper 2</p>
                    <p>Paper 3</p>
                    <p>Paper 4</p>
                    <p>Paper 5</p>
                </div>
                <div class="s2">
                    <p>Marks</p>
                    <p><?php echo e($result['p1']); ?></p>
                    <p><?php echo e($result['p2']); ?></p>
                    <p><?php echo e($result['p3']); ?></p>
                    <p><?php echo e($result['p4']); ?></p>
                    <p><?php echo e($result['p5']); ?></p>
                </div>
            </div>

            <div class="result">
                <p>Total Marks:&nbsp;<?php echo e($result['marks']); ?></p>
                <p>Percentage:&nbsp;<?php echo e($result['percentage']); ?>%</p>
            </div>

            <div class="button">
                <button onclick="window.print()">Print Result</button>
            </div>
        </div>
    <?php endif; ?>
</body>
</html>
