from database.mysql import get_connection


def add_quote(text: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quotes (text) VALUES (%s)", (text,))
        conn.commit()
        conn.close()
        return True
    except Exception as exception:
        print(exception)
        return False


def get_random_quote() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM quotes ORDER BY RAND() LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "💕 Цитат пока нет, но скоро появятся вдохновляющие слова! ✨"


def get_all_quotes() -> list[tuple]:
    """
    Get all quotes with their IDs and creation dates.
    Returns list of tuples: (id, text, created_at)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, created_at FROM quotes ORDER BY created_at DESC")
    quotes = cursor.fetchall()
    conn.close()
    return quotes


def delete_quote(quote_id: int) -> bool:
    """
    Delete a quote by its ID.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quotes WHERE id = %s", (quote_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0  # Returns True if at least one row was deleted
    except Exception as exception:
        print(exception)
        return False
