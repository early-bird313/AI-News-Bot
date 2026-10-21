import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .config import settings
from .models import NewsItem, DigestLog

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                title_bn TEXT,
                normalized_title TEXT,
                url TEXT UNIQUE NOT NULL,
                image_url TEXT,
                source TEXT NOT NULL,
                category TEXT DEFAULT 'General AI',
                published_at TEXT NOT NULL,
                raw_summary TEXT,
                ai_summary_bn TEXT,
                impact_score REAL DEFAULT 5.0,
                is_trending INTEGER DEFAULT 0,
                title_hash TEXT,
                sent_in_digest INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
        """)

        # Migration: add title_bn and image_url if table already existed without them
        try:
            cursor.execute("ALTER TABLE news_items ADD COLUMN title_bn TEXT;")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE news_items ADD COLUMN image_url TEXT;")
        except sqlite3.OperationalError:
            pass # Column already exists
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_published ON news_items (published_at DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_trending ON news_items (is_trending, impact_score DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_url ON news_items (url);
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS digest_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TEXT NOT NULL,
                period TEXT NOT NULL,
                item_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT
            );
        """)
        conn.commit()

def exists_url(url: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM news_items WHERE url = ? LIMIT 1", (url,))
        return cursor.fetchone() is not None

def get_recent_titles(hours: int = 48) -> List[Dict[str, Any]]:
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, title_bn, normalized_title, url, image_url, source, published_at, impact_score
            FROM news_items
            WHERE published_at >= ?
            ORDER BY id DESC
        """, (cutoff,))
        return [dict(row) for row in cursor.fetchall()]

def save_news_item(item: NewsItem) -> Optional[int]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO news_items (
                    title, title_bn, normalized_title, url, image_url, source, category,
                    published_at, raw_summary, ai_summary_bn,
                    impact_score, is_trending, title_hash, sent_in_digest, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.title,
                item.title_bn,
                item.normalized_title,
                item.url,
                item.image_url,
                item.source,
                item.category,
                item.published_at,
                item.raw_summary,
                item.ai_summary_bn,
                item.impact_score,
                1 if item.is_trending else 0,
                item.title_hash,
                1 if item.sent_in_digest else 0,
                item.created_at
            ))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def get_news(
    limit: int = 50,
    offset: int = 0,
    filter_type: str = "all", # all, trending, latest
    category: str = "",
    search: str = ""
) -> List[NewsItem]:
    query = "SELECT * FROM news_items WHERE 1=1"
    params: list = []
    
    if filter_type == "trending":
        query += " AND (is_trending = 1 OR impact_score >= 7.5)"
    
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
        
    if search:
        query += " AND (title LIKE ? OR title_bn LIKE ? OR ai_summary_bn LIKE ? OR raw_summary LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])
        
    if filter_type == "trending":
        query += " ORDER BY impact_score DESC, published_at DESC LIMIT ? OFFSET ?"
    else:
        query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
        
    params.extend([limit, offset])
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        items = []
        for r in rows:
            d = dict(r)
            d["is_trending"] = bool(d["is_trending"])
            d["sent_in_digest"] = bool(d["sent_in_digest"])
            items.append(NewsItem(**d))
        return items

def get_pending_digest_items(limit: int = 5, min_score: float = 6.0) -> List[NewsItem]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(hours=48)).isoformat()
        
        # First priority: unsent high impact items
        cursor.execute("""
            SELECT * FROM news_items
            WHERE sent_in_digest = 0 AND published_at >= ?
            ORDER BY impact_score DESC, published_at DESC
            LIMIT ?
        """, (cutoff, limit))
        rows = cursor.fetchall()
        
        # Second priority: top overall highest impact items
        if len(rows) < limit:
            cursor.execute("""
                SELECT * FROM news_items
                WHERE published_at >= ?
                ORDER BY impact_score DESC, published_at DESC
                LIMIT ?
            """, (cutoff, limit))
            rows = cursor.fetchall()
            
        items = []
        for r in rows:
            d = dict(r)
            d["is_trending"] = bool(d["is_trending"])
            d["sent_in_digest"] = bool(d["sent_in_digest"])
            items.append(NewsItem(**d))
        return items

def mark_as_sent(item_ids: List[int]):
    if not item_ids:
        return
    placeholders = ",".join("?" for _ in item_ids)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE news_items SET sent_in_digest = 1 WHERE id IN ({placeholders})
        """, item_ids)
        conn.commit()

def log_digest(period: str, item_count: int, status: str = "success", error_message: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO digest_logs (sent_at, period, item_count, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), period, item_count, status, error_message))
        conn.commit()

def get_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM news_items")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM news_items WHERE is_trending = 1 OR impact_score >= 7.5")
        trending_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT sent_at, period, item_count FROM digest_logs ORDER BY id DESC LIMIT 1")
        last_log = cursor.fetchone()
        
        return {
            "total_news": total_count,
            "trending_news": trending_count,
            "last_digest": dict(last_log) if last_log else None
        }
