"""Streamlit entry point for Personal AI Library Manager."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

import streamlit as st

from config import APP_NAME
from database import SessionLocal, initialise_database
from pages import about, add_book, catalog, dashboard, delete_book, edit_book, loans, reports, search_books, settings, users, view_books, wishlist
from services.auth_service import AuthService

st.set_page_config(page_title=APP_NAME, page_icon="books", layout="wide")
initialise_database()

_AUTH_SESSION_SECRET = os.environ.setdefault("AUTH_SESSION_SECRET", secrets.token_urlsafe(32)).encode()
_AUTH_SESSION_MAX_AGE = 60 * 60 * 24 * 7

PAGES = {
    "Dashboard": ("Dashboard", dashboard, ":material/home:"),
    "Add Book": ("Add book", add_book, ":material/add_circle:"),
    "View Books": ("Books", view_books, ":material/menu_book:"),
    "Search Books": ("Search books", search_books, ":material/search:"),
    "Edit Book": ("Edit book", edit_book, ":material/edit:"),
    "Delete Book": ("Delete book", delete_book, ":material/delete:"),
    "Reports": ("Reports", reports, ":material/bar_chart:"),
    "Tags and Collections": ("Categories", catalog, ":material/local_offer:"),
    "Wishlist": ("Wishlist", wishlist, ":material/favorite:"),
    "Borrowed/Lent Books": ("Lending", loans, ":material/import_contacts:"),
    "Settings and Backup": ("Settings", settings, ":material/settings:"),
    "About this app": ("About", about, ":material/info:"),
}


def _create_auth_token(username: str) -> str:
    """Create a signed, short-lived browser session token."""
    payload = json.dumps({"username": username, "expires_at": int(time.time()) + _AUTH_SESSION_MAX_AGE}, separators=(",", ":")).encode()
    signature = hmac.new(_AUTH_SESSION_SECRET, payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload + signature).decode()


def _read_auth_token() -> str | None:
    """Return the signed username from the query string when the token is valid."""
    token = st.query_params.get("auth")
    if not isinstance(token, str):
        return None
    try:
        raw_token = base64.urlsafe_b64decode(token.encode())
        payload, received_signature = raw_token[:-32], raw_token[-32:]
        expected_signature = hmac.new(_AUTH_SESSION_SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(received_signature, expected_signature):
            return None
        session_data = json.loads(payload)
        if not isinstance(session_data["username"], str) or session_data["expires_at"] < time.time():
            return None
        return session_data["username"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _remember_user(username: str) -> None:
    """Store the signed session token in the browser URL for page refreshes."""
    st.query_params["auth"] = _create_auth_token(username)


def _forget_user() -> None:
    """Remove the persisted browser session token."""
    if "auth" in st.query_params:
        del st.query_params["auth"]


def main() -> None:
    """Run the selected library screen with a scoped database session."""
    st.session_state.setdefault("authenticated_user", None)
    st.session_state.setdefault("switch_back_user", None)
    with SessionLocal() as session:
        auth_service = AuthService(session)
        auth_service.ensure_admin()
        if st.session_state.authenticated_user is None:
            remembered_username = _read_auth_token()
            remembered_user = auth_service.find_user(remembered_username) if remembered_username else None
            if remembered_user is not None:
                st.session_state.authenticated_user = {"username": remembered_user.username, "display_name": remembered_user.display_name, "role": remembered_user.role}
            elif remembered_username is not None:
                _forget_user()
        if st.session_state.authenticated_user is None:
            _, sign_in_column, _ = st.columns((2, 3, 2))
            with sign_in_column:
                st.title("Sign in")
                with st.form("sign_in"):
                    usernames = [user.username for user in auth_service.list_users()]
                    username = st.selectbox(
                        "Username",
                        [""] + usernames,
                        format_func=lambda value: "Select a user" if not value else value,
                    )
                    password = st.text_input("Password", type="password")
                    sign_in_submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
                    cancel_submitted = st.form_submit_button("Cancel switch", width="stretch") if st.session_state.switch_back_user else False
                if cancel_submitted:
                    st.session_state.authenticated_user = st.session_state.switch_back_user
                    st.session_state.switch_back_user = None
                    _remember_user(st.session_state.authenticated_user["username"])
                    st.rerun()
                if sign_in_submitted:
                    user = auth_service.authenticate(username, password)
                    if user is None:
                        st.error("Incorrect username or password.")
                    else:
                        st.session_state.authenticated_user = {"username": user.username, "display_name": user.display_name, "role": user.role}
                        st.session_state.switch_back_user = None
                        _remember_user(user.username)
                        st.rerun()
            return

    st.sidebar.title(APP_NAME)
    authenticated_user = st.session_state.authenticated_user
    if "role" not in authenticated_user:
        authenticated_user["role"] = "Administrator" if authenticated_user.get("is_admin") else "User"
    pages = dict(PAGES)
    if authenticated_user["role"] == "Guest":
        pages = {
            name: page for name, page in pages.items()
            if name in {"Dashboard", "View Books", "Search Books", "Reports", "About this app"}
        }
    elif authenticated_user["role"] == "User":
        pages.pop("Delete Book")
    else:
        pages["User management"] = ("Users", users, ":material/group:")
    st.sidebar.caption(f"Signed in as {authenticated_user['username']}")
    switch_user_column, sign_out_column = st.sidebar.columns(2)
    if switch_user_column.button("Switch user"):
        st.session_state.switch_back_user = authenticated_user
        st.session_state.authenticated_user = None
        _forget_user()
        st.rerun()
    if sign_out_column.button("Sign out"):
        st.session_state.authenticated_user = None
        st.session_state.switch_back_user = None
        _forget_user()
        st.rerun()
    selected_page = st.sidebar.radio(
        "Navigation",
        list(pages),
        format_func=lambda page: f"{pages[page][2]} {pages[page][0]}",
        key="navigation",
    )
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
        .library-masthead {
            align-items: center;
            background: linear-gradient(112deg, #123c55 0%, #146c72 56%, #1c8a83 100%);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 14px;
            box-shadow: 0 10px 24px rgba(12, 58, 78, 0.2);
            box-sizing: border-box;
            display: flex;
            gap: 1rem;
            left: 21rem;
            min-height: 92px;
            overflow: hidden;
            padding: 1rem 1.25rem;
            position: fixed;
            right: 1.25rem;
            top: 3.25rem;
            z-index: 1000;
        }
        .library-masthead::after {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 50%;
            content: "";
            height: 230px;
            position: absolute;
            right: -68px;
            top: -128px;
            width: 230px;
        }
        .library-masthead-spacer { height: 9.5rem; }
        .library-mark {
            align-items: center;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.34);
            border-radius: 12px;
            box-shadow: 0 5px 12px rgba(3, 44, 61, 0.18);
            color: #ffffff;
            display: flex;
            flex: 0 0 54px;
            font-family: "Poppins", sans-serif;
            font-size: 1rem;
            font-weight: 700;
            height: 54px;
            justify-content: center;
            letter-spacing: 0.06em;
            line-height: 1;
            width: 54px;
            z-index: 1;
        }
        .library-masthead-copy { min-width: 0; position: relative; z-index: 1; }
        .library-masthead h1 {
            color: #ffffff;
            font-family: "Poppins", sans-serif;
            font-size: 1.45rem;
            font-weight: 700;
            letter-spacing: 0;
            line-height: 1.2;
            margin: 0;
        }
        .library-subtitle {
            color: #d6f0ee;
            font-family: "Poppins", sans-serif;
            font-size: 0.76rem;
            font-weight: 500;
            letter-spacing: 0;
            line-height: 1.35;
            margin: 0.22rem 0 0;
        }
        .library-contact-row {
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 0.38rem;
            justify-content: flex-end;
            margin-left: auto;
            position: relative;
            z-index: 1;
        }
        .library-contact-item {
            align-items: center;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.17);
            border-radius: 8px;
            color: #ffffff;
            display: inline-flex;
            font-family: "Poppins", sans-serif;
            font-size: 0.7rem;
            font-weight: 500;
            gap: 0.35rem;
            padding: 0.42rem 0.55rem;
        }
        .library-contact-icon { color: #f7d574; font-size: 0.75rem; line-height: 1; }
        .library-mobile-icon {
            border: 1.5px solid #f7d574;
            border-radius: 3px;
            box-sizing: border-box;
            display: inline-block;
            height: 0.9rem;
            position: relative;
            width: 0.56rem;
        }
        .library-mobile-icon::after {
            background: #f7d574;
            border-radius: 50%;
            bottom: 1px;
            content: "";
            height: 2px;
            left: 50%;
            position: absolute;
            transform: translateX(-50%);
            width: 2px;
        }
        @media (max-width: 900px) {
            .library-masthead {
                align-items: flex-start;
                display: grid;
                grid-template-columns: 54px minmax(0, 1fr);
                left: 19.5rem;
                min-height: 112px;
                padding: 0.85rem;
                right: 0.75rem;
            }
            .library-masthead h1 { font-size: 1.25rem; }
            .library-contact-row { grid-column: 1 / -1; justify-content: flex-start; margin: 0.1rem 0 0; }
        }
        @media (max-width: 640px) {
            .library-masthead {
                align-items: flex-start;
                gap: 0.75rem;
                left: 0.5rem;
                min-height: 0;
                padding: 0.9rem;
                right: 0.5rem;
                top: 3rem;
            }
            .library-masthead-spacer { height: 13rem; }
            .library-mark { flex-basis: 44px; height: 44px; width: 44px; }
            .library-masthead h1 { font-size: 1.1rem; }
            .library-contact-row { justify-content: flex-start; margin: 0.8rem 0 0 -3.6rem; }
            .library-contact-item { font-size: 0.64rem; }
        }
        </style>
        <section class="library-masthead">
            <div class="library-mark" aria-label="Venkatesh Gowda library monogram">VG</div>
            <div class="library-masthead-copy">
                <h1>Library Management System</h1>
                <p class="library-subtitle">Your personal catalogue, lending history, and reading journey in one place.</p>
            </div>
            <div class="library-contact-row" aria-label="Library contact information">
                <span class="library-contact-item"><span class="library-contact-icon" aria-hidden="true">&#9906;</span>Bengaluru, Karnataka</span>
                <span class="library-contact-item"><span class="library-mobile-icon" aria-hidden="true"></span>9740819001</span>
                <span class="library-contact-item"><span class="library-contact-icon" aria-hidden="true">&#9993;</span>venkus@gmail.com</span>
            </div>
        </section>
        <div class="library-masthead-spacer" aria-hidden="true"></div>
        """
    )
    with SessionLocal() as session:
        pages[selected_page][1].render(session)


if __name__ == "__main__":
    main()
