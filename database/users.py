from database.mysql import get_connection


def add_user(user_id: int, username: str, first_name: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT IGNORE INTO users (id, username, first_name) VALUES (%s, %s, %s)",
                       (user_id, username, first_name))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_all_user_ids() -> list[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids
