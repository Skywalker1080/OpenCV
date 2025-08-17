import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("violations.sqlite").as_posix()

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_utc TEXT NOT NULL,
        file_path TEXT NOT NULL,
        violation_type TEXT NOT NULL,
        fine INTEGER NOT NULL
    );
    """)
    con.commit()
    con.close()

def insert_violation(file_path, violation_type, fine):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO violations (ts_utc, file_path, violation_type, fine)
        VALUES (?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), file_path, violation_type, fine))
    con.commit()
    con.close()