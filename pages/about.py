"""About page for the Personal AI Library Manager."""

import streamlit as st
from sqlalchemy.orm import Session

from config import APP_NAME
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Render application information without requiring database access."""
    del session
    render_page_header("About this app", "A private workspace for cataloguing, organising, and enjoying your books.", "i")
    st.subheader(APP_NAME)
    st.caption("Version 1.0.0")

    st.write(
        "A local library manager for cataloguing books, tracking loans, "
        "maintaining a wishlist, and organizing books with tags and collections."
    )

    with st.container(border=True):
        st.subheader("Developed by")
        st.write("Venkatesh Kumar HC")
        st.caption("AI Engineer | Telstra India Ltd")
        st.link_button("venkus@gmail.com", "mailto:venkus@gmail.com", icon=":material/mail:")

    with st.container(border=True):
        st.subheader("Your data")
        st.write(
            "Your catalogue is stored locally in the configured SQLite database. "
            "Use Settings and Backup to create and restore local backups."
        )

    with st.container(border=True):
        st.subheader("Included features")
        st.write("Book catalogue, search, tags, collections, wishlist, loans, reports, image uploads, and local backup and restore.")