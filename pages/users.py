"""Administrator account-management page."""

import streamlit as st
from sqlalchemy.orm import Session

from services.auth_service import AuthService


def render(session: Session) -> None:
    """Render user creation, password reset, and deletion controls."""
    st.header("User management")
    service = AuthService(session)
    users = service.list_users()
    st.dataframe(
        [{"Username": user.username, "Display name": user.display_name or user.username, "Role": user.role} for user in users],
        hide_index=True,
    )

    with st.form("create_user"):
        st.subheader("Add user")
        username = st.text_input("Username", key="create_username")
        display_name = st.text_input("Display name", key="create_display_name")
        password = st.text_input("Password", type="password", key="create_password")
        role = st.selectbox("Role", ("User", "Administrator", "Guest"), key="create_role")
        create_submitted = st.form_submit_button("Add user", type="primary")
    if create_submitted:
        try:
            service.create_user(username, display_name, password, role)
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("User created.")
            st.rerun()

    usernames = [user.username for user in users]
    selected_account = st.selectbox("User account to edit", usernames, key="edit_username")
    selected_user = next(user for user in users if user.username == selected_account)
    with st.form("edit_user"):
        st.subheader("Edit user")
        new_username = st.text_input("Username", value=selected_user.username, disabled=selected_user.username == "admin")
        display_name = st.text_input("Display name", value=selected_user.display_name or selected_user.username)
        role = st.selectbox(
            "Role",
            ("User", "Administrator", "Guest"),
            index=("User", "Administrator", "Guest").index(selected_user.role),
            disabled=selected_user.username == "admin",
        )
        edit_submitted = st.form_submit_button("Save user changes", type="primary")
    if edit_submitted:
        try:
            service.update_user(selected_account, new_username, display_name, role)
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("User details and role updated.")
            st.rerun()

    with st.form("reset_user_password"):
        st.subheader("Reset password")
        selected_user = st.selectbox("User account", usernames, key="reset_username")
        new_password = st.text_input("New password", type="password", key="reset_password")
        reset_submitted = st.form_submit_button("Reset password")
    if reset_submitted:
        try:
            service.reset_password(selected_user, new_password)
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("Password reset successfully.")

    deletable_users = [user.username for user in users if not user.is_admin]
    if deletable_users:
        with st.form("delete_user"):
            st.subheader("Delete user")
            selected_user = st.selectbox("User to delete", deletable_users, key="delete_username")
            confirmed = st.checkbox("I understand this removes the user account.")
            delete_submitted = st.form_submit_button("Delete user", type="primary")
        if delete_submitted:
            if not confirmed:
                st.error("Confirm account deletion before continuing.")
            else:
                service.delete_user(selected_user)
                st.success("User deleted.")
                st.rerun()