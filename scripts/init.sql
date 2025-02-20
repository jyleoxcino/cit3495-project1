-- Ensure databases exist
CREATE DATABASE IF NOT EXISTS credentials;
CREATE DATABASE IF NOT EXISTS uploads;

USE credentials;

-- Ensure users table exists
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_dir VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user'  -- Added role for future user management
);

USE uploads;

-- Ensure files table exists
CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath TEXT NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (username) REFERENCES credentials.users(username) ON DELETE CASCADE
);

-- Create index on filename for faster lookups
CREATE INDEX idx_filename ON files(filename);

-- Create MySQL users
CREATE USER IF NOT EXISTS 'auth_service'@'%' IDENTIFIED BY 'auth_service';  -- Ensure auth service has a user
CREATE USER IF NOT EXISTS 'upload_service'@'%' IDENTIFIED BY 'upload_service';
CREATE USER IF NOT EXISTS 'stream_service'@'%' IDENTIFIED BY 'stream_service';

-- Grant privileges to services
GRANT ALL PRIVILEGES ON credentials.* TO 'auth_service'@'%';
GRANT ALL PRIVILEGES ON credentials.* TO 'upload_service'@'%';
GRANT ALL PRIVILEGES ON uploads.* TO 'upload_service'@'%';
GRANT ALL PRIVILEGES ON credentials.* TO 'stream_service'@'%';
GRANT ALL PRIVILEGES ON uploads.* TO 'stream_service'@'%';

-- Allow services to read credentials
GRANT SELECT, INSERT, UPDATE, DELETE ON credentials.users TO 'auth_service'@'%';
GRANT SELECT ON credentials.users TO 'upload_service'@'%';
GRANT SELECT ON credentials.users TO 'stream_service'@'%';

FLUSH PRIVILEGES;
