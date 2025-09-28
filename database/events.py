from database.mysql import get_connection


def add_event(date: str, theme: str, place: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (date, theme, place) VALUES (%s, %s, %s)", (date, theme, place))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
