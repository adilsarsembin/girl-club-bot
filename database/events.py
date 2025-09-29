from datetime import datetime

from database.mysql import get_connection


def add_event(planned_at: str, theme: str, place: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (planned_at, theme, place) VALUES (%s, %s, %s)", (planned_at, theme, place))
        conn.commit()
        conn.close()
        return True
    except Exception as exception:
        print(exception)
        return False


def get_all_events() -> list[tuple]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("SELECT id, planned_at, place, theme FROM events WHERE is_active = 1 AND planned_at > %s ORDER BY planned_at ASC", now)
    events = cursor.fetchall()
    conn.close()
    return events


def deactivate_event(event_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE events SET is_active = FALSE WHERE id = %s", (event_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as exception:
        print(exception)
        return False
