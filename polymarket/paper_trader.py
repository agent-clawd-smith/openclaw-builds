"""
Paper trading engine for Polymarket.
Logs simulated trades and tracks performance.
No real money involved.
"""
import json
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.openclaw/workspace/polymarket/paper_trades.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            condition_id TEXT,
            question TEXT,
            outcome TEXT,
            price REAL,
            size REAL,
            signal TEXT,
            signal_confidence REAL,
            notes TEXT,
            resolved INTEGER DEFAULT 0,
            resolution TEXT,
            pnl REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            condition_id TEXT,
            source TEXT,
            signal TEXT,
            confidence REAL,
            raw TEXT
        )
    """)
    conn.commit()
    return conn


def log_trade(condition_id, question, outcome, price, size, signal, confidence, notes=""):
    """Log a simulated trade."""
    conn = init_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades (timestamp, condition_id, question, outcome, price, size, signal, signal_confidence, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), condition_id, question, outcome, price, size, signal, confidence, notes))
    conn.commit()
    trade_id = c.lastrowid
    conn.close()
    print(f"[PAPER TRADE #{trade_id}] {outcome} @ {price:.2f} | size: ${size:.2f} | {question[:60]}")
    return trade_id


def log_signal(condition_id, source, signal, confidence, raw=""):
    """Log an alpha signal."""
    conn = init_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals (timestamp, condition_id, source, signal, confidence, raw)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), condition_id, source, signal, confidence, raw))
    conn.commit()
    conn.close()


def get_open_trades():
    """Get all unresolved paper trades."""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT * FROM trades WHERE resolved = 0 ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def resolve_trade(trade_id, resolution, final_price):
    """Mark a trade resolved and calculate P&L."""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT outcome, price, size FROM trades WHERE id = ?", (trade_id,))
    row = c.fetchone()
    if not row:
        print(f"Trade #{trade_id} not found")
        return
    outcome, entry_price, size = row
    # If our outcome won, final_price = 1.0 (100 cents)
    pnl = (final_price - entry_price) * size
    c.execute("""
        UPDATE trades SET resolved = 1, resolution = ?, pnl = ? WHERE id = ?
    """, (resolution, pnl, trade_id))
    conn.commit()
    conn.close()
    print(f"[RESOLVED #{trade_id}] Resolution: {resolution} | P&L: ${pnl:+.2f}")
    return pnl


def portfolio_summary():
    """Print current paper portfolio stats."""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(size) FROM trades WHERE resolved = 0")
    open_count, open_exposure = c.fetchone()
    c.execute("SELECT COUNT(*), SUM(pnl) FROM trades WHERE resolved = 1")
    closed_count, total_pnl = c.fetchone()
    conn.close()
    print(f"\n=== PAPER PORTFOLIO ===")
    print(f"Open positions: {open_count or 0} | Exposure: ${open_exposure or 0:.2f}")
    print(f"Closed trades: {closed_count or 0} | Total P&L: ${total_pnl or 0:+.2f}")
    print("=======================\n")


if __name__ == "__main__":
    init_db()
    portfolio_summary()
    print("Open trades:")
    for t in get_open_trades():
        print(f"  #{t[0]} | {t[6]} @ {t[5]:.2f} | {t[3][:60]}")
