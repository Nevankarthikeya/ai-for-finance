import sqlite3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from backend.config import DB_PATH

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Return a thread-safe connection to the SQLite database."""
    target_path = str(db_path or DB_PATH)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize the database tables if they do not exist."""
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_prices (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume REAL,
                PRIMARY KEY(symbol, date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS download_log (
                symbol TEXT PRIMARY KEY,
                status TEXT,
                rows_downloaded INTEGER,
                message TEXT,
                updated_at TEXT
            )
            """
        )
    conn.close()

def downloaded_ok(symbol: str, db_path: Optional[Path] = None) -> bool:
    """Check if the symbol was previously downloaded successfully."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT status FROM download_log WHERE symbol=?", (symbol,))
        row = cur.fetchone()
        return row is not None and row["status"] == "success"
    finally:
        conn.close()

def save_daily_prices(rows: List[tuple], db_path: Optional[Path] = None) -> None:
    """Insert or replace daily price records."""
    if not rows:
        return
    conn = get_connection(db_path)
    with conn:
        conn.executemany(
            "INSERT OR REPLACE INTO daily_prices VALUES (?,?,?,?,?,?,?,?)",
            rows
        )
    conn.close()

def log_download_status(symbol: str, status: str, rows_downloaded: int, message: str, db_path: Optional[Path] = None) -> None:
    """Insert or update download log status."""
    conn = get_connection(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO download_log VALUES (?,?,?,?,?)",
            (symbol, status, rows_downloaded, str(message)[:500], now_iso)
        )
    conn.close()

def get_coverage(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Return database coverage statistics per symbol."""
    conn = get_connection(db_path)
    try:
        query = (
            "SELECT symbol, COUNT(*) AS daily_rows, MIN(date) AS first_date, "
            "MAX(date) AS last_date FROM daily_prices GROUP BY symbol ORDER BY symbol"
        )
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def get_failures(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Return download failures log."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM download_log WHERE status='failed' ORDER BY symbol"
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def get_all_daily_prices(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Fetch all daily price records ordered by symbol and date."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM daily_prices ORDER BY symbol, date"
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def get_symbol_prices(symbol: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """Fetch all daily price records for a single symbol."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM daily_prices WHERE symbol=? ORDER BY date"
        return pd.read_sql_query(query, conn, params=(symbol,))
    finally:
        conn.close()

def get_total_symbols_count(db_path: Optional[Path] = None) -> int:
    """Count unique symbols in the database."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT symbol) FROM daily_prices")
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()

def reset_database(db_path: Optional[Path] = None) -> None:
    """Reset the database tables."""
    conn = get_connection(db_path)
    with conn:
        conn.execute("DROP TABLE IF EXISTS daily_prices")
        conn.execute("DROP TABLE IF EXISTS download_log")
    conn.close()
    init_db(db_path)

