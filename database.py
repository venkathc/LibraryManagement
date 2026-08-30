"""SQLAlchemy engine and session lifecycle helpers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL


class Base(DeclarativeBase):
    """Base class for ORM models."""


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialise_database() -> None:
    """Create application tables if they do not already exist."""
    from models import Book  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if DATABASE_URL.startswith("sqlite"):
        _apply_sqlite_migrations()


def _apply_sqlite_migrations() -> None:
    """Apply additive SQLite schema updates that create_all cannot perform."""
    columns = {column["name"] for column in inspect(engine).get_columns("books")}
    with engine.begin() as connection:
        if "cover_image_path" not in columns:
            connection.execute(text("ALTER TABLE books ADD COLUMN cover_image_path VARCHAR(255)"))
        if "archived_at" not in columns:
            connection.execute(text("ALTER TABLE books ADD COLUMN archived_at DATETIME"))
        if "deleted_at" not in columns:
            connection.execute(text("ALTER TABLE books ADD COLUMN deleted_at DATETIME"))
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "role" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'User'"))
            connection.execute(text("UPDATE users SET role = 'Administrator' WHERE is_admin = 1"))
    if "display_name" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(120)"))


def get_session() -> Generator[Session, None, None]:
    """Yield a session and ensure its resources are released."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
