from datetime import datetime

from database.postgres import get_connection


def add_event(planned_at: str, theme: str, place: str) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (planned_at, theme, place) VALUES (%s, %s, %s) RETURNING id",
                      (planned_at, theme, place))
        event_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return event_id
    except Exception as exception:
        print(exception)
        return 0


def get_all_events() -> list[tuple]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("SELECT id, planned_at, place, theme FROM events WHERE is_active = true AND planned_at > %s ORDER BY planned_at ASC", (now,))
    events = [(row['id'], row['planned_at'], row['place'], row['theme']) for row in cursor.fetchall()]
    cursor.close()
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
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted
    except Exception as exception:
        print(exception)
        return False
