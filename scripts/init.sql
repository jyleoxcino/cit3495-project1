-- Ensure databases exist
CREATE DATABASE IF NOT EXISTS credentials;
CREATE DATABASE IF NOT EXISTS uploads;

USE credentials;

-- Ensure users table exists
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_dir VARCHAR(255) NOT NULL
);

USE uploads;

-- Ensure files table exists
CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath TEXT NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MySQL users
CREATE USER IF NOT EXISTS 'upload_service'@'%' IDENTIFIED BY 'upload_service';
CREATE USER IF NOT EXISTS 'stream_service'@'%' IDENTIFIED BY 'stream_service';

-- Grant privileges after table creation
GRANT ALL PRIVILEGES ON credentials.* TO 'upload_service'@'%';
GRANT ALL PRIVILEGES ON uploads.* TO 'upload_service'@'%';
GRANT ALL PRIVILEGES ON credentials.* TO 'stream_service'@'%';
GRANT ALL PRIVILEGES ON uploads.* TO 'stream_service'@'%';

-- Allow upload_service and stream_service to read user credentials
GRANT SELECT ON credentials.users TO 'upload_service'@'%';
GRANT SELECT ON credentials.users TO 'stream_service'@'%';

FLUSH PRIVILEGES;
