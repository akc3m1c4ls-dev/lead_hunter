from pathlib import Path
import sqlite3


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "opps.db"


def get_connection():
    """
    Open a connection to the shared Lead Hunter database.

    Outreach communicates with Lead Hunter only through
    database/opps.db.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


# ---------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------

def init_outreach_db():
    """
    Create the tables owned by the outreach system.

    Existing Lead Hunter tables are left untouched.
    """

    with get_connection() as conn:

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS outreach_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK (
                        status IN (
                            'draft',
                            'active',
                            'paused',
                            'completed'
                        )
                    ),

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS outreach_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                opp_id INTEGER NOT NULL,
                campaign_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK (
                        status IN (
                            'draft',
                            'ready',
                            'active',
                            'replied',
                            'completed',
                            'stopped',
                            'bounced',
                            'unsubscribed',
                            'failed'
                        )
                    ),

                current_step INTEGER NOT NULL DEFAULT 0,

                next_send_at TEXT,
                last_sent_at TEXT,
                replied_at TEXT,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (opp_id)
                    REFERENCES opps(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (campaign_id)
                    REFERENCES outreach_campaigns(id)
                    ON DELETE CASCADE,

                UNIQUE (opp_id, campaign_id)
            );


            CREATE TABLE IF NOT EXISTS outreach_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                contact_id INTEGER NOT NULL,

                sequence_step INTEGER NOT NULL,

                subject TEXT NOT NULL,
                body TEXT NOT NULL,

                provider TEXT,
                provider_message_id TEXT,

                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK (
                        status IN (
                            'draft',
                            'queued',
                            'sent',
                            'delivered',
                            'failed',
                            'bounced'
                        )
                    ),

                sent_at TEXT,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (contact_id)
                    REFERENCES outreach_contacts(id)
                    ON DELETE CASCADE,

                UNIQUE (contact_id, sequence_step)
            );


            CREATE TABLE IF NOT EXISTS outreach_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                contact_id INTEGER NOT NULL,
                message_id INTEGER,

                event_type TEXT NOT NULL,

                data TEXT,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (contact_id)
                    REFERENCES outreach_contacts(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (message_id)
                    REFERENCES outreach_messages(id)
                    ON DELETE SET NULL
            );


            CREATE TABLE IF NOT EXISTS outreach_suppressions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                email TEXT NOT NULL COLLATE NOCASE UNIQUE,

                reason TEXT NOT NULL,

                source TEXT,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );


            CREATE INDEX IF NOT EXISTS idx_outreach_contacts_status
                ON outreach_contacts(status);

            CREATE INDEX IF NOT EXISTS idx_outreach_contacts_next_send
                ON outreach_contacts(next_send_at);

            CREATE INDEX IF NOT EXISTS idx_outreach_contacts_opp
                ON outreach_contacts(opp_id);

            CREATE INDEX IF NOT EXISTS idx_outreach_messages_status
                ON outreach_messages(status);

            CREATE INDEX IF NOT EXISTS idx_outreach_events_contact
                ON outreach_events(contact_id);

            CREATE INDEX IF NOT EXISTS idx_outreach_suppressions_email
                ON outreach_suppressions(email);
            """
        )


# ---------------------------------------------------------
# LIVE OUTREACH PERSISTENCE
# ---------------------------------------------------------

def get_or_create_campaign(name="AutomateLabs live outreach"):
    """Return the active live campaign, creating it when needed."""
    init_outreach_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM outreach_campaigns WHERE name = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
            (name,),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO outreach_campaigns (name, status) VALUES (?, 'active')",
            (name,),
        )
        return cur.lastrowid


def record_successful_send(*, opp_id, campaign_id, subject, html, provider_message_id):
    """
    Persist a Brevo-accepted live send atomically.

    The contact row makes selector.py exclude this opportunity from future
    outreach runs. The message and event preserve the provider ID for audit.
    """
    init_outreach_db()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM outreach_contacts WHERE opp_id = ? AND campaign_id = ?",
            (opp_id, campaign_id),
        ).fetchone()
        if existing:
            raise RuntimeError(
                f"Opportunity {opp_id} is already registered in campaign {campaign_id}; refusing to record/send it twice."
            )

        contact_cur = conn.execute(
            """
            INSERT INTO outreach_contacts
                (opp_id, campaign_id, status, current_step, last_sent_at, updated_at)
            VALUES (?, ?, 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (opp_id, campaign_id),
        )
        contact_id = contact_cur.lastrowid

        message_cur = conn.execute(
            """
            INSERT INTO outreach_messages
                (contact_id, sequence_step, subject, body, provider,
                 provider_message_id, status, sent_at)
            VALUES (?, 1, ?, ?, 'brevo', ?, 'sent', CURRENT_TIMESTAMP)
            """,
            (contact_id, subject, html, str(provider_message_id)),
        )
        message_id = message_cur.lastrowid

        conn.execute(
            """
            INSERT INTO outreach_events (contact_id, message_id, event_type, data)
            VALUES (?, ?, 'sent', ?)
            """,
            (contact_id, message_id, f"Brevo accepted message {provider_message_id}"),
        )

    return contact_id, message_id

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

def database_info():
    """
    Return basic information useful for verifying that Outreach
    is connected to the correct database.
    """

    with get_connection() as conn:

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        lead_count = conn.execute(
            "SELECT COUNT(*) AS count FROM opps"
        ).fetchone()["count"]

    return {
        "database": str(DATABASE_PATH),
        "lead_count": lead_count,
        "tables": [row["name"] for row in tables],
    }


# ---------------------------------------------------------
# CLI TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    init_outreach_db()

    info = database_info()

    print()
    print("Outreach database initialized.")
    print(f"Database: {info['database']}")
    print(f"Lead Hunter opportunities: {info['lead_count']}")
    print()
    print("Tables:")

    for table in info["tables"]:
        print(f"  - {table}")
