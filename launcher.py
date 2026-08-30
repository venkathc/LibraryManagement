"""macOS application launcher for the bundled Streamlit app."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Personal AI Library Manager"


def main() -> None:
    """Run Streamlit with a per-user writable application-data directory."""
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app_path = bundle_dir / "app.py"
    data_dir = Path.home() / "Library" / "Application Support" / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("LIBRARY_MANAGER_DATA_DIR", str(data_dir))
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "false")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    from streamlit.web import cli as streamlit_cli

    sys.argv = ["streamlit", "run", str(app_path)]
    sys.exit(streamlit_cli.main())


if __name__ == "__main__":
    main()