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
    return result[0] if result else "Цитат пока нет."
