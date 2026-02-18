import json
from pathlib import Path
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _table_exists(raw: SQLiteConnection, table_name: str) -> bool:
    row = raw.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(raw: SQLiteConnection, table_name: str, column_name: str) -> bool:
    rows = raw.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(str(row[1]) == column_name for row in rows)


def _ensure_column(raw: SQLiteConnection, table_name: str, column_name: str, definition: str) -> bool:
    if _column_exists(raw, table_name, column_name):
        return False
    raw.execute(f"ALTER TABLE {table_name} ADD COLUMN {definition}")
    return True


def _run_post_schema_migrations(raw: SQLiteConnection) -> None:
    approval_status_added = _ensure_column(
        raw,
        "users",
        "approval_status",
        "approval_status TEXT NOT NULL DEFAULT 'pending'",
    )
    _ensure_column(raw, "users", "approved_by_user_pk", "approved_by_user_pk INTEGER")
    _ensure_column(raw, "users", "approved_at", "approved_at DATETIME")
    _ensure_column(raw, "users", "rejected_reason", "rejected_reason TEXT")

    if approval_status_added:
        # Preserva contas antigas em bancos locais ja existentes.
        raw.execute("UPDATE users SET approval_status='approved'")

    raw.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_trails (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_pk INTEGER NOT NULL,
          trail_key TEXT NOT NULL,
          title TEXT NOT NULL,
          description TEXT NOT NULL,
          difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')),
          focus_tags_json TEXT NOT NULL DEFAULT '[]',
          lesson_bundle_json TEXT NOT NULL DEFAULT '[]',
          recommended_xp INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (user_pk, trail_key),
          FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    raw.execute("CREATE INDEX IF NOT EXISTS idx_generated_trails_user ON generated_trails(user_pk, created_at DESC)")

    raw.execute(
        """
        CREATE TABLE IF NOT EXISTS coop_pairs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_low_pk INTEGER NOT NULL,
          user_high_pk INTEGER NOT NULL,
          requested_by_user_pk INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'rejected')),
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          confirmed_at DATETIME,
          rejected_at DATETIME,
          UNIQUE (user_low_pk, user_high_pk),
          CHECK (user_low_pk <> user_high_pk),
          FOREIGN KEY (user_low_pk) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (user_high_pk) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (requested_by_user_pk) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    raw.execute("CREATE INDEX IF NOT EXISTS idx_coop_pairs_status ON coop_pairs(status, created_at DESC)")
    raw.execute("CREATE INDEX IF NOT EXISTS idx_coop_pairs_users ON coop_pairs(user_low_pk, user_high_pk)")

    raw.execute(
        """
        CREATE TABLE IF NOT EXISTS friendship_xp_rewards (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_pk INTEGER NOT NULL,
          milestone INTEGER NOT NULL,
          xp_awarded INTEGER NOT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (user_pk, milestone),
          FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    raw.execute("CREATE INDEX IF NOT EXISTS idx_friendship_rewards_user ON friendship_xp_rewards(user_pk, created_at DESC)")

    raw.execute(
        """
        CREATE TABLE IF NOT EXISTS user_mascot_inventory (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_pk INTEGER NOT NULL,
          item_id TEXT NOT NULL,
          item_name TEXT NOT NULL,
          rarity TEXT NOT NULL CHECK (rarity IN ('common', 'rare', 'epic')),
          slot TEXT NOT NULL CHECK (slot IN ('head', 'face', 'neck', 'back', 'effect', 'hand', 'chest')),
          obtained_from TEXT NOT NULL CHECK (obtained_from IN ('seed', 'levelup')),
          obtained_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (user_pk, item_id),
          FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    raw.execute("CREATE INDEX IF NOT EXISTS idx_mascot_inventory_user ON user_mascot_inventory(user_pk, obtained_at DESC)")

    raw.execute(
        """
        CREATE TABLE IF NOT EXISTS user_mascot_equipment (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_pk INTEGER NOT NULL,
          mascot_id TEXT NOT NULL CHECK (mascot_id IN ('fox', 'owl')),
          item_id TEXT,
          equipped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (user_pk, mascot_id),
          FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    raw.execute("CREATE INDEX IF NOT EXISTS idx_mascot_equipment_user ON user_mascot_equipment(user_pk, mascot_id)")

    raw.execute(
        """
        CREATE TABLE IF NOT EXISTS user_level_reward_claims (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_pk INTEGER NOT NULL,
          level INTEGER NOT NULL CHECK (level >= 1),
          item_id TEXT NOT NULL,
          duplicate_converted INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_converted IN (0, 1)),
          converted_xp INTEGER NOT NULL DEFAULT 0 CHECK (converted_xp >= 0),
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (user_pk, level),
          FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    raw.execute("CREATE INDEX IF NOT EXISTS idx_level_rewards_user ON user_level_reward_claims(user_pk, level)")

    _ensure_column(raw, "missions", "target_user_pk", "target_user_pk INTEGER")
    raw.execute("CREATE INDEX IF NOT EXISTS idx_missions_target ON missions(target_user_pk, status, created_at DESC)")


def init_db() -> None:
    schema_path = Path("backend/sql/schema.sql")
    seed_path = Path("backend/sql/seed.sql")
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
        seed_path = Path(__file__).resolve().parents[2] / "sql" / "seed.sql"

    raw = engine.raw_connection()
    try:
        if not _table_exists(raw, "users"):
            raw.executescript(schema_path.read_text(encoding="utf-8"))
            raw.executescript(seed_path.read_text(encoding="utf-8"))
        _run_post_schema_migrations(raw)
        raw.commit()
    finally:
        raw.close()


def table_has_rows(db: Session, table_name: str) -> bool:
    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return int(result.scalar_one()) > 0


def load_json_seed(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
