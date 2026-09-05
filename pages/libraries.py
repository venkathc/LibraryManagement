"""Library creation, membership, and access management."""

from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.auth_service import AuthService
from services.library_service import LibraryService
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Render controls for administrators to manage library membership."""
    render_page_header("Libraries", "Create separate libraries and give each member the right level of access.", "L")
    library_service = LibraryService(session)
    auth_service = AuthService(session)
    is_global_administrator = st.session_state.get("is_global_administrator", False)
    selected_library_id = st.session_state.get("selected_library_id")
    if is_global_administrator:
        libraries = library_service.list_libraries("", is_administrator=True)
    else:
        libraries = [library for library in library_service.list_libraries(
            st.session_state.authenticated_user["username"]
        ) if library.id == selected_library_id]
    st.dataframe(
        [
            {
                "Library": library.name,
                "Created": library.created_at,
                "Members": len(library.memberships),
                "Books": len(library.books),
            }
            for library in libraries
        ],
        hide_index=True,
        width="stretch",
    )
    if is_global_administrator:
        with st.form("create_library"):
            library_name = st.text_input("Library name")
            create_submitted = st.form_submit_button("Create library", type="primary")
        if create_submitted:
            try:
                library_service.create_library(library_name, st.session_state.authenticated_user["username"])
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Library created.")
                st.rerun()
    if not libraries:
        return
    library = st.selectbox(
        "Library",
        libraries,
        format_func=lambda item: item.name,
        disabled=not is_global_administrator,
    )
    users = auth_service.list_users()
    member_names = {membership.user.username for membership in library.memberships}
    st.subheader("Current members")
    st.dataframe(
        [
            {
                "Username": membership.user.username,
                "Display name": membership.user.display_name or membership.user.username,
                "Library role": membership.role,
            }
            for membership in library.memberships
        ],
        hide_index=True,
        width="stretch",
    )
    available_users = [user.username for user in users if user.username not in member_names]
    if not available_users:
        st.info("All current accounts are already members of this library.")
    else:
        with st.form("add_library_member"):
            st.subheader("Add member")
            username = st.selectbox("User", available_users)
            role = st.selectbox("Library role", ("Member", "Admin"))
            add_submitted = st.form_submit_button("Add member")
        if add_submitted:
            try:
                library_service.add_member(library.id, username, role)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Library member added.")
                st.rerun()