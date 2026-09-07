import sqlite3
from pathlib import Path
from models import Posting

def get_connection(db_path="data/postings.db"):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS postings (
            unique_key  TEXT PRIMARY KEY,
            company     TEXT NOT NULL,
            title       TEXT NOT NULL,
            location    TEXT,
            url         TEXT,
            job_id      TEXT,
            term        TEXT,
            posted_at   TEXT,
            scraped_at  TEXT                     
        )
    """)
    conn.commit()
    
def save_postings(conn, postings):
    rows = [
        (p.unique_key, p.company,p.title, p.location, p.url,
         p.job_id, p.term, p.posted_at, p.scraped_at)
        for p in postings
    ]
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO postings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return conn.total_changes - before

def get_existing_keys(conn):
    rows = conn.execute("SELECT unique_key FROM postings").fetchall()
    return {row[0] for row in rows}