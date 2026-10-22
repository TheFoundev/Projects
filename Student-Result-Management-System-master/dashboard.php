<?php
/**
 * Admin dashboard.
 */

declare(strict_types=1);

require_once __DIR__ . '/session.php';

$classCount = (int) (db_one('SELECT COUNT(*) AS total FROM class')['total'] ?? 0);
$studentCount = (int) (db_one('SELECT COUNT(*) AS total FROM students')['total'] ?? 0);
$resultCount = (int) (db_one('SELECT COUNT(*) AS total FROM result')['total'] ?? 0);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="./css/home.css">
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
    <link rel="stylesheet" href="./css/font-awesome-4.7.0/css/font-awesome.css">
    <link rel="stylesheet" href="normalize.css">
    <title>Dashboard</title>
    <style>
        .main{
            border-radius: 10px;
            border-width: 5px;
            border-style: solid;
            padding: 20px;
            margin: 7% 20% 0 20%;
        }
    </style>
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
        <p>Number of classes: <?php echo e($classCount); ?></p>
        <p>Number of students: <?php echo e($studentCount); ?></p>
        <p>Number of results: <?php echo e($resultCount); ?></p>
    </div>

    <div class="footer">
        <!-- <span>Designed & Coded By Jibin Thomas</span> -->
    </div>
</body>
</html>
