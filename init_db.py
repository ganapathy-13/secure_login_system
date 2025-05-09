import sqlite3
from werkzeug.security import generate_password_hash

con = sqlite3.connect("users.db")
cur = con.cursor()

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    failed_attempts INTEGER DEFAULT 0,
    last_failed_login TEXT,
    is_locked INTEGER DEFAULT 0
)
""")

# Login logs table
cur.execute("""
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    ip_address TEXT,
    timestamp TEXT,
    browser TEXT,
    device TEXT,
    status TEXT
)
""")

# Optional: Insert a test user
cur.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")))

con.commit()
con.close()
