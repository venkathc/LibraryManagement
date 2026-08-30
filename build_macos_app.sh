#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$project_dir"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "Personal AI Library Manager" \
  --add-data "app.py:." \
  --add-data "pages:pages" \
  --add-data "services:services" \
  --add-data "repositories:repositories" \
  --add-data "utils:utils" \
  --collect-all streamlit \
  launcher.py

echo "Created: $project_dir/dist/Personal AI Library Manager.app"