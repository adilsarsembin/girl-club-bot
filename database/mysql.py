import pymysql
import os
from dotenv import load_dotenv


load_dotenv()
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'charset': 'utf8mb4'
}

def get_connection():
    conn = pymysql.connect(**DB_CONFIG)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            planned_at DATETIME NOT NULL,
            theme TEXT NOT NULL,
            place TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_id VARCHAR(255) NOT NULL,
            file_unique_id VARCHAR(255) NOT NULL,
            filename VARCHAR(255),
            caption TEXT,
            uploaded_by BIGINT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            role VARCHAR(20) DEFAULT 'user'
        )
    """)
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS anonymous_messages (
                                                             id INT AUTO_INCREMENT PRIMARY KEY,
                                                             user_id BIGINT NOT NULL,
                                                             message TEXT NOT NULL,
                                                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
   """)
    conn.commit()
    conn.close()
