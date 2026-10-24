-- Student Result Management System schema (MySQL / MariaDB).
--
-- The application creates the tables automatically when they are missing, so
-- this file is only needed to provision a database by hand.
--
-- The admin_login table stores a bcrypt hash in password_hash. The legacy
-- password column is kept so that an old installation can be upgraded in
-- place: the first successful sign in hashes the stored value and clears the
-- column.

CREATE TABLE IF NOT EXISTS `admin_login` (
  `userid` varchar(64) NOT NULL,
  `password` varchar(255) NULL,
  `password_hash` varchar(255) NULL,
  PRIMARY KEY (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `class` (
  `name` varchar(64) NOT NULL,
  `id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `students` (
  `name` varchar(128) NOT NULL,
  `rno` int NOT NULL,
  `class_name` varchar(64) NOT NULL,
  PRIMARY KEY (`rno`, `class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `result` (
  `name` varchar(128) NOT NULL,
  `rno` int NOT NULL,
  `class_name` varchar(64) NOT NULL,
  `p1` int NOT NULL,
  `p2` int NOT NULL,
  `p3` int NOT NULL,
  `p4` int NOT NULL,
  `p5` int NOT NULL,
  `marks` int NOT NULL,
  `percentage` double NOT NULL,
  PRIMARY KEY (`rno`, `class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `login_attempts` (
  `userid` varchar(64) NOT NULL,
  `attempts` int NOT NULL DEFAULT 0,
  `last_attempt` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create the first administrator. Replace the password before running this.
-- INSERT INTO `admin_login` (`userid`, `password_hash`)
-- VALUES ('admin', '$2y$10$REPLACE.WITH.THE.OUTPUT.OF.scripts/create_admin.php');
