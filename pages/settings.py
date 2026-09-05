"""SQLite backup and restore page."""

from pathlib import Path

import streamlit as st
from sqlalchemy.orm import Session

from services.auth_service import AuthService
from services.backup_service import BackupService
from services.library_service import LibraryService
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Render local SQLite backup, download, and guarded restore controls."""
    render_page_header("Settings and backup", "Create restore points and keep a portable copy of your personal catalogue.", "C")
    authenticated_user = st.session_state.get("authenticated_user", {})
    username = authenticated_user.get("username")
    if username:
        libraries = LibraryService(session).list_libraries(
            username, authenticated_user.get("role") == "Administrator"
        )
        if libraries:
            account = AuthService(session).find_user(username)
            choices = {library.name: library.id for library in libraries}
            default_index = next(
                (index for index, library in enumerate(libraries) if library.id == account.default_library_id),
                0,
            )
            with st.container(border=True):
                st.subheader("Default library")
                st.caption("This library opens automatically whenever you sign in. You can still switch libraries from the sidebar.")
                selected_name = st.selectbox("Open this library by default", choices, index=default_index)
                if st.button("Save default library", type="primary", icon=":material/bookmark:"):
                    AuthService(session).set_default_library(username, choices[selected_name])
                    st.session_state.selected_library_id = choices[selected_name]
                    st.success(f"Default library set to {selected_name}.")
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