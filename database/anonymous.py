from database.postgres import get_connection


def add_anonymous_message(user_id: int, message: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO anonymous_messages (user_id, message) VALUES (%s, %s)",
                      (user_id, message))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception:
        return False


def get_all_anonymous_messages() -> list[tuple]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, message, created_at FROM anonymous_messages ORDER BY created_at DESC")
    messages = [(row['id'], row['user_id'], row['message'], row['created_at']) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return messages


def delete_anonymous_message(message_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM anonymous_messages WHERE id = %s", (message_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted
    except Exception:
        return False
