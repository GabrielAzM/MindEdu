"""SQLAlchemy models are intentionally lightweight in this MVP.

Main access uses SQL for explicit control over SQLite JSON fields and triggers.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
