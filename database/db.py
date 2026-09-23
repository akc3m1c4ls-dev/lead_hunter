import json
import sqlite3
from pathlib import Path
from datetime import datetime

from lead_hunter.models import Business, BusinessAnalysis, WebsiteResearch


DATABASE_PATH = Path(__file__).resolve().parent / "opps.db"


def get_conn():
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    conn = get_conn()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            location TEXT NOT NULL,
            category TEXT NOT NULL,
            score INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            reason TEXT,

            created_at TEXT NOT NULL,

            UNIQUE(location, category)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS opps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            business_name TEXT NOT NULL,
            category TEXT,
            location TEXT,

            website TEXT UNIQUE,
            phone TEXT,
            email TEXT,

            score INTEGER,

            problems TEXT,
            opportunities TEXT,
            existing_systems TEXT,

            target_problem TEXT,
            proposed_solution TEXT,
            evidence TEXT,
            pitch_angle TEXT,

            relevant_pages TEXT,
            signals TEXT,

            confidence REAL,

            status TEXT DEFAULT 'pending',

            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_categories(location: str, categories: list[dict]):
    conn = get_conn()

    for category in categories:
        conn.execute(
            """
            INSERT OR IGNORE INTO categories
            (location, category, score, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                location,
                category["name"],
                category["score"],
                category["reason"],
                datetime.utcnow().isoformat(),
            ),
        )

    conn.commit()
    conn.close()

def get_categories(location: str) -> list[dict]:
    conn = get_conn()

    rows = conn.execute(
        """
        SELECT location, category, score
        FROM categories
        WHERE location = ?
        ORDER BY score DESC
        """,
        (location,),
    ).fetchall()

    conn.close()

    return [
        {
            "category": row[1],
            "score": row[2],
        }
        for row in rows
    ]

def save_businesses(
    businesses: list[Business],
):
    conn = get_conn()

    for business in businesses:
        conn.execute(
            """
            INSERT OR IGNORE INTO opps (
                business_name,
                category,
                location,
                website,
                phone,
                email,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business.name,
                business.category,
                business.location,
                business.website,
                business.phone,
                business.email,
                "pending",
                datetime.utcnow().isoformat(),
            ),
        )

    conn.commit()
    conn.close()

def get_next_category(location: str):
    conn = get_conn()

    row = conn.execute(
        """
        SELECT category, score
        FROM categories
        WHERE location = ?
          AND status = 'pending'
        ORDER BY score DESC
        LIMIT 1
        """,
        (location,),
    ).fetchone()

    conn.close()

    if not row:
        return None

    return {
        "category": row[0],
        "score": row[1],
    }

def mark_category_done(
    location: str,
    category: str,
):
    conn = get_conn()

    conn.execute(
        """
        UPDATE categories
        SET status = 'done'
        WHERE location = ?
          AND category = ?
        """,
        (location, category),
    )

    conn.commit()
    conn.close()

def get_pending_businesses(limit: int = 30) -> list[Business]:
    conn = get_conn()

    rows = conn.execute(
        """
        SELECT
            business_name,
            category,
            location,
            website,
            phone,
            email
        FROM opps
        WHERE status = 'pending'
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [
        Business(
            name=row[0],
            category=row[1],
            location=row[2],
            website=row[3],
            phone=row[4],
            email=row[5],
        )
        for row in rows
    ]

def update_business_analysis(
    business: Business,
    research: WebsiteResearch,
    analysis: BusinessAnalysis,
):
    conn = get_conn()

    email = research.emails[0] if research.emails else business.email

    conn.execute(
        """
        UPDATE opps
        SET
            email = ?,
            score = ?,
            problems = ?,
            opportunities = ?,
            existing_systems = ?,
            target_problem = ?,
            proposed_solution = ?,
            evidence = ?,
            pitch_angle = ?,
            confidence = ?,
            status = 'done'
        WHERE business_name = ?
          AND category = ?
          AND location = ?
        """,
        (
            email,
            analysis.score,
            json.dumps(analysis.problems),
            json.dumps(analysis.opportunities),
            json.dumps(analysis.existing_systems),
            analysis.target_problem,
            analysis.proposed_solution,
            json.dumps(analysis.evidence),
            analysis.pitch_angle,
            analysis.confidence,
            business.name,
            business.category,
            business.location,
        ),
    )

    conn.commit()
    conn.close()