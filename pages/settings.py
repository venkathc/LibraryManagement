"""SQLite backup and restore page."""

from pathlib import Path

import streamlit as st
from sqlalchemy.orm import Session

from services.backup_service import BackupService


def render(session: Session) -> None:
    """Render local SQLite backup, download, and guarded restore controls."""
    del session
    st.header("Settings and Backup")
    try:
        service = BackupService()
    except ValueError as error:
        st.info(str(error))
        return
    if st.button("Create local backup", type="primary"):
        try:
            backup = service.create_backup()
        except ValueError as error:
            st.error(str(error))
        else:
            st.success(f"Created {backup.name}.")
    backups = service.list_backups()
    if not backups:
        st.info("No local backups yet.")
        return
    choices = {backup.name: backup for backup in backups}
    selected_name = st.selectbox("Available backups", choices)
    selected_backup = choices[selected_name]
    st.download_button("Download selected backup", selected_backup.read_bytes(), selected_backup.name, "application/x-sqlite3")
    confirm = st.checkbox("I understand restore replaces the active database after creating a safety backup.")
    if st.button("Restore selected backup", disabled=not confirm):
        try:
            safety_backup = service.restore_backup(Path(selected_backup))
        except ValueError as error:
            st.error(str(error))
        else:
            st.success(f"Database restored. Safety backup: {safety_backup.name}. Restart the app to use restored data.")