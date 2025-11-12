from database.postgres import get_connection


def add_quote(text: str) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quotes (text) VALUES (%s) RETURNING id", (text,))
        quote_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return quote_id
    except Exception as exception:
        print(exception)
        return 0


def get_random_quote() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM quotes ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['text'] if result else "💕 Цитат пока нет, но скоро появятся вдохновляющие слова! ✨"


def get_all_quotes() -> list[tuple]:
    """
    Get all quotes with their IDs and creation dates.
    Returns list of tuples: (id, text, created_at)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, created_at FROM quotes ORDER BY created_at DESC")
    quotes = [(row['id'], row['text'], row['created_at']) for row in cursor.fetchall()]
    cursor.close()
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
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted
    except Exception as exception:
        print(exception)
        return False
