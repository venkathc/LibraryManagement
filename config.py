"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

SOURCE_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(os.getenv("LIBRARY_MANAGER_DATA_DIR", SOURCE_DIR)).expanduser()
BASE_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'library.db'}")
APP_NAME = "Personal AI Library Manager"
