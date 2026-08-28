"""About page for the Personal AI Library Manager."""

import streamlit as st
from sqlalchemy.orm import Session

from config import APP_NAME


def render(session: Session) -> None:
    """Render application information without requiring database access."""
    del session
    st.header("About this app")
    st.subheader(APP_NAME)
    st.caption("Version 1.0.0")

    st.write(
        "A local library manager for cataloguing books, tracking loans, "
        "maintaining a wishlist, and organizing books with tags and collections."
    )

    with st.container(border=True):
        st.subheader("Your data")
        st.write(
            "Your catalogue is stored locally in the configured SQLite database. "
            "Use Settings and Backup to create and restore local backups."
        )

    with st.container(border=True):
        st.subheader("Included features")
        st.write("Book catalogue, search, tags, collections, wishlist, loans, reports, image uploads, and local backup and restore.")