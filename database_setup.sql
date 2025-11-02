-- GirlClub Bot Database Setup Script
-- Run this script to manually create the database and tables

-- Create database (run as root/admin user)
CREATE DATABASE IF NOT EXISTS girl_club_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user and grant permissions (run as root/admin user)
CREATE USER IF NOT EXISTS 'botuser'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON girl_club_bot.* TO 'botuser'@'localhost';
FLUSH PRIVILEGES;

-- Switch to the database (run as botuser or continue as admin)
USE girl_club_bot;

-- Create tables (these are created automatically by the bot, but here for reference)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Photos table
CREATE TABLE IF NOT EXISTS photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id VARCHAR(255) NOT NULL,
    file_unique_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    caption TEXT,
    uploaded_by BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    planned_at DATETIME NOT NULL,
    theme TEXT NOT NULL,
    place TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Anonymous messages table
CREATE TABLE IF NOT EXISTS anonymous_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample data (optional - for testing)
-- INSERT INTO quotes (text) VALUES
-- ('Каждый день - это новый шанс!', 'Поверь в себя и все получится!', 'Ты сильнее, чем думаешь!');

-- Show created tables
SHOW TABLES;

-- Show table structures (optional)
-- DESCRIBE users;
-- DESCRIBE quotes;
-- DESCRIBE photos;
-- DESCRIBE events;
-- DESCRIBE anonymous_messages;
