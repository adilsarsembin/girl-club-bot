from database.postgres import get_connection


def add_user(user_id: int, username: str, first_name: str, role: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id, username, first_name, role) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                       (user_id, username, first_name, role))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception:
        return False


def get_all_user_ids_by_role(role: str) -> list[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role = %s", (role,))
    user_ids = [row['id'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return user_ids
