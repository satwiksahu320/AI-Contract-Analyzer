CREATE DATABASE IF NOT EXISTS risk_analyzer_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'risk_user'@'localhost'
IDENTIFIED BY 'risk_password';

GRANT ALL PRIVILEGES ON risk_analyzer_db.* TO 'risk_user'@'localhost';
FLUSH PRIVILEGES;

USE risk_analyzer_db;

-- After running this in MySQL Workbench, run these commands in the project folder:
-- pip install mysqlclient
-- python manage.py migrate
-- python manage.py runserver
