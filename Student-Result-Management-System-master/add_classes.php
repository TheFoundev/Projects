<?php
/**
 * Add a class.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$error = null;
$name = trim((string) ($_POST['class_name'] ?? ''));
$id = trim((string) ($_POST['class_id'] ?? ''));

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    require_csrf();

    if ($name === '') {
        $error = 'Please enter class';
    } elseif ($id === '') {
        $error = 'Please enter class id';
    } elseif (preg_match('/[a-z]/i', $id) || !ctype_digit($id)) {
        $error = 'Please enter valid class id';
    } else {
        try {
            db_query('INSERT INTO class (name, id) VALUES (:name, :id)', [
                ':name' => $name,
                ':id' => (int) $id,
            ]);
            flash('Class added.');
        } catch (PDOException $exception) {
            $error = 'Invalid class name or class id';
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
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <link rel="stylesheet" href="./css/home.css">
    <link rel="stylesheet" type="text/css" href="./css/form.css" media="all">
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
    <link rel="stylesheet" href="./css/font-awesome-4.7.0/css/font-awesome.css">
    <title>Add Classes</title>
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
        <form action="add_classes.php" method="post">
            <fieldset>
                <legend>Add Class</legend>
                <input type="text" name="class_name" placeholder="Class Name" value="<?php echo e($name); ?>">
                <input type="text" name="class_id" placeholder="Class ID" value="<?php echo e($id); ?>">
                <?php echo csrf_field(); ?>
                <input type="submit" value="Submit">
            </fieldset>
        </form>

        <table>
            <caption>Existing classes</caption>
            <tr><th>ID</th><th>NAME</th></tr>
            <?php foreach ($classes as $class) : ?>
                <tr>
                    <td><?php echo e($class['id']); ?></td>
                    <td><?php echo e($class['name']); ?></td>
                </tr>
            <?php endforeach; ?>
        </table>
    </div>

    <div class="footer">
        <!-- <span>Designed & Coded By Jibin Thomas</span> -->
    </div>
</body>
</html>
