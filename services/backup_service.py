"""SQLite database backup and restore operations."""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from config import BASE_DIR, DATABASE_URL

BACKUPS_DIR = BASE_DIR / "backups"


class BackupService:
    """Manage timestamped local SQLite backup files."""

    def __init__(self) -> None:
        if not DATABASE_URL.startswith("sqlite:///"):
            raise ValueError("Backup and restore are currently available for SQLite only.")
        self.database_path = Path(DATABASE_URL.removeprefix("sqlite:///"))

    def create_backup(self) -> Path:
        """Create a timestamped copy of the active SQLite database."""
        if not self.database_path.is_file():
            raise ValueError("The database file does not exist yet.")
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        target = BACKUPS_DIR / f"library_{datetime.now():%Y%m%d_%H%M%S}.db"
        shutil.copy2(self.database_path, target)
        return target

    def list_backups(self) -> list[Path]:
        """List locally created backup files, newest first."""
        if not BACKUPS_DIR.exists():
            return []
        return sorted(BACKUPS_DIR.glob("*.db"), key=lambda path: path.stat().st_mtime, reverse=True)

    @staticmethod
    def validate_backup(path: Path) -> None:
        """Confirm a candidate file is a readable SQLite database."""
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.DatabaseError as error:
            raise ValueError("The selected file is not a valid SQLite database.") from error
        if result != ("ok",):
            raise ValueError("The selected SQLite database failed its integrity check.")

    def restore_backup(self, source: Path) -> Path:
        """Validate then restore a local backup after making a safety copy."""
        self.validate_backup(source)
        safety_backup = self.create_backup()
        shutil.copy2(source, self.database_path)
        return safety_backup
