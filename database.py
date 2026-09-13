import sqlite3
from pathlib import Path
from models import Posting, _now_iso


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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scrape_runs (
            company  TEXT    NOT NULL,
            run_at   TEXT    NOT NULL,
            status   TEXT    NOT NULL,
            found    INTEGER NOT NULL,
            error    TEXT
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

def record_runs(conn, outcomes):
    now = _now_iso()
    rows = [
        (name, now, status, len(postings), error)
        for (name, postings, status, error) in outcomes
    ]
    conn.executemany(
        "INSERT INTO scrape_runs (company, run_at, status, found, error) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    
def recent_counts(conn, company, limit=5):
    rows = conn.execute(
        "SELECT found FROM scrape_runs WHERE company = ? AND status = 'ok' "
        "ORDER BY run_at DESC LIMIT ?",
        (company, limit),
    ).fetchall()
    return [row[0] for row in rows]

def get_existing_keys(conn):
    rows = conn.execute("SELECT unique_key FROM postings").fetchall()
    return {row[0] for row in rows}