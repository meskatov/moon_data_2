import sqlite3
from datetime import datetime
from config import TECH_ADMIN_ID  # <-- ЭТА СТРОКА ДОЛЖНА БЫТЬ

DB_PATH = "data/moon_data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        join_date TEXT,
        search_count INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        search_type TEXT,
        search_query TEXT,
        result TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        rank TEXT,
        added_by INTEGER,
        added_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bot_config (
        key TEXT PRIMARY KEY, 
        value TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS verified_users (
        user_id INTEGER PRIMARY KEY, 
        verified_at TEXT
    )''')

    c.execute("SELECT value FROM bot_config WHERE key = 'bot_enabled'")
    if not c.fetchone():
        c.execute("INSERT INTO bot_config (key, value) VALUES ('bot_enabled', 'true')")

    conn.commit()
    conn.close()


async def send_tech_log(bot, action, details):
    try:
        await bot.send_message(
            TECH_ADMIN_ID,
            f"🔐 **Технический лог Moon Data**\n\n"
            f"**Действие:** {action}\n"
            f"**Детали:** {details}\n"
            f"**Время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )
    except:
        pass


def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, last_name, join_date) VALUES (?, ?, ?, ?, ?)",
                  (user_id, username, first_name, last_name, datetime.now().isoformat()))
        conn.commit()
    conn.close()


def add_search_log(user_id, search_type, search_query, result):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO search_history (user_id, search_type, search_query, result, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, search_type, search_query, result, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET search_count = search_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user


def get_user_history(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT search_type, search_query, timestamp FROM search_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit))
    history = c.fetchall()
    conn.close()
    return history


def is_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT rank FROM admins WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None


def add_admin(user_id, rank, added_by):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO admins (user_id, rank, added_by, added_at) VALUES (?, ?, ?, ?)",
              (user_id, rank, added_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def remove_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_admins():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, rank FROM admins")
    res = c.fetchall()
    conn.close()
    return res


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM search_history")
    total_searches = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM verified_users")
    verified_count = c.fetchone()[0]
    conn.close()
    return {"users": total_users, "searches": total_searches, "verified": verified_count}


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, join_date, search_count FROM users ORDER BY join_date DESC")
    res = c.fetchall()
    conn.close()
    return res


def get_bot_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_config WHERE key = 'bot_enabled'")
    res = c.fetchone()
    conn.close()
    return res[0] == 'true' if res else True


def set_bot_status(enabled: bool):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bot_config (key, value) VALUES ('bot_enabled', ?)",
              ('true' if enabled else 'false'))
    conn.commit()
    conn.close()


def is_user_verified(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verified_at FROM verified_users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res is not None


def add_verified_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO verified_users (user_id, verified_at) VALUES (?, ?)",
              (user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()