from datetime import datetime

from database.mysql import get_connection


def add_event(planned_at: str, theme: str, place: str) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (planned_at, theme, place) VALUES (%s, %s, %s)", (planned_at, theme, place))
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return event_id
    except Exception as exception:
        print(exception)
        return 0


def get_all_events() -> list[tuple]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("SELECT id, planned_at, place, theme FROM events WHERE is_active = 1 AND planned_at > %s ORDER BY planned_at ASC", now)
    events = cursor.fetchall()
    conn.close()
    return events


def delete_event(event_id: int) -> bool:
    """
    Delete an event by its ID.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0  # Returns True if at least one row was deleted
    except Exception as exception:
        print(exception)
        return False
