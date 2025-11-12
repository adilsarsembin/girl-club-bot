import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # Fallback for local development
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'girl_club_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            cursor_factory=RealDictCursor
        )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables with PostgreSQL syntax
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            planned_at TIMESTAMP NOT NULL,
            theme TEXT NOT NULL,
            place TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check if photos table exists and has correct structure
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'photos'
        )
    """)
    table_exists = cursor.fetchone()[0]

    if not table_exists:
        cursor.execute("""
            CREATE TABLE photos (
                id SERIAL PRIMARY KEY,
                file_id VARCHAR(255) NOT NULL,
                file_unique_id VARCHAR(255) NOT NULL,
                filename VARCHAR(255),
                caption TEXT,
                uploaded_by BIGINT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add explicit index for better performance
        cursor.execute("""
            CREATE INDEX idx_photos_uploaded_at ON photos(uploaded_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX idx_photos_file_id ON photos(file_id)
        """)
    else:
        # Ensure required columns exist (for migration compatibility)
        cursor.execute("""
            ALTER TABLE photos
            ADD COLUMN IF NOT EXISTS file_unique_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS filename VARCHAR(255),
            ADD COLUMN IF NOT EXISTS caption TEXT,
            ADD COLUMN IF NOT EXISTS uploaded_by BIGINT,
            ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
