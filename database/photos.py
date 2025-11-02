from database.mysql import get_connection


def add_photo(file_id: str, file_unique_id: str, filename: str = None, caption: str = None, uploaded_by: int = None) -> bool:
    """
    Add a photo to the database.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO photos (file_id, file_unique_id, filename, caption, uploaded_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (file_id, file_unique_id, filename, caption, uploaded_by))
        conn.commit()
        conn.close()
        return True
    except Exception as exception:
        print(exception)
        return False


def get_random_photo() -> dict:
    """
    Get a random photo from the database.
    Returns dict with photo info or None if no photos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, file_unique_id, filename, caption, uploaded_at FROM photos ORDER BY RAND() LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'id': result[0],
            'file_id': result[1],
            'file_unique_id': result[2],
            'filename': result[3],
            'caption': result[4],
            'uploaded_at': result[5]
        }
    return None


def get_all_photos() -> list[tuple]:
    """
    Get all photos with their info.
    Returns list of tuples: (id, file_id, filename, caption, uploaded_at)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, filename, caption, uploaded_at FROM photos ORDER BY uploaded_at DESC")
    photos = cursor.fetchall()
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
        conn.close()
        return cursor.rowcount > 0  # Returns True if at least one row was deleted
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
    conn.close()

    if result:
        return {
            'id': result[0],
            'file_id': result[1],
            'file_unique_id': result[2],
            'filename': result[3],
            'caption': result[4],
            'uploaded_at': result[5]
        }
    return None
