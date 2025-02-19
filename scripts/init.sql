CREATE DATABASE credentials;
CREATE DATABASE uploads;
CREATE USER 'upload_service'@'172.21.0.%' IDENTIFIED BY 'upload_service';
CREATE USER 'stream_service'@'172.21.0.%' IDENTIFIED BY 'stream_service';
GRANT ALL PRIVILEGES ON credentials.* TO 'upload_service'@'172.21.0.%';
GRANT ALL PRIVILEGES ON uploads.* TO 'upload_service'@'172.21.0.%';
GRANT ALL PRIVILEGES ON credentials.* TO 'stream_service'@'172.21.0.%';
GRANT ALL PRIVILEGES ON uploads.* TO 'stream_service'@'172.21.0.%';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS credentials.users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS uploads.files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath TEXT NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
