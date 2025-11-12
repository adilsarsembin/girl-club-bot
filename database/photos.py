from database.postgres import get_connection


def add_photo(file_id: str, file_unique_id: str, filename: str = None, caption: str = None, uploaded_by: int = None) -> int:
    """
    Add a photo to the database.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO photos (file_id, file_unique_id, filename, caption, uploaded_by)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (file_id, file_unique_id, filename, caption, uploaded_by))
        photo_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return photo_id
    except Exception as exception:
        print(exception)
        return 0


def get_random_photo() -> dict:
    """
    Get a random photo from the database.
    Returns dict with photo info or None if no photos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, file_unique_id, filename, caption, uploaded_at FROM photos ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return dict(result) if result else None


def get_all_photos() -> list[tuple]:
    """
    Get all photos with their info.
    Returns list of tuples: (id, file_id, filename, caption, uploaded_at)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, filename, caption, uploaded_at FROM photos ORDER BY uploaded_at DESC")
    photos = [(row['id'], row['file_id'], row['filename'], row['caption'], row['uploaded_at']) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return photos


def delete_photo(photo_id: int) -> bool:
    """
    Delete a photo by its ID.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM photos WHERE id = %s", (photo_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted
    except Exception as exception:
        print(exception)
        return False


def get_photo_by_id(photo_id: int) -> dict:
    """
    Get photo info by ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, file_unique_id, filename, caption, uploaded_at FROM photos WHERE id = %s", (photo_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return dict(result) if result else None
