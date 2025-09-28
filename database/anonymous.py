from database.mysql import get_connection


def save_anon_message(user_id: int, message: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO anonymous_messages (user_id, message) VALUES (%s, %s)", (user_id, message))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
