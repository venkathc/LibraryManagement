"""Shared presentation helpers for library workspace pages."""

from __future__ import annotations

from html import escape

import streamlit as st


def render_page_header(title: str, description: str, icon: str) -> None:
    """Render a consistent, compact header for a library workspace page."""
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
        .workspace-page-header {
            align-items: center;
            background: linear-gradient(112deg, #123c55 0%, #146c72 58%, #1c8a83 100%);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 14px;
            box-shadow: 0 10px 24px rgba(12, 58, 78, 0.16);
            box-sizing: border-box;
            color: #ffffff;
            display: flex;
            gap: 0.9rem;
            margin: 0 0 1.15rem;
            min-height: 104px;
            overflow: hidden;
            padding: 1.1rem 1.25rem;
            position: relative;
        }
        .workspace-page-header::after {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 50%;
            content: "";
            height: 180px;
            position: absolute;
            right: -52px;
            top: -104px;
            width: 180px;
        }
        .workspace-page-icon {
            align-items: center;
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.28);
            border-radius: 11px;
            color: #f7d574;
            display: flex;
            flex: 0 0 46px;
            font: 700 1.35rem/1 "Poppins", sans-serif;
            height: 46px;
            justify-content: center;
            position: relative;
            width: 46px;
            z-index: 1;
        }
        .workspace-page-copy { min-width: 0; position: relative; z-index: 1; }
        .workspace-page-title { color: #ffffff; font: 700 1.45rem/1.2 "Poppins", sans-serif; letter-spacing: 0; margin: 0; }
        .workspace-page-description { color: #d6f0ee; font: 400 0.8rem/1.45 "Poppins", sans-serif; margin: 0.3rem 0 0; max-width: 760px; }
        [data-testid="stMainBlockContainer"] .stButton > button,
        [data-testid="stMainBlockContainer"] [data-testid="stDownloadButton"] > button {
            border-radius: 8px;
            font-family: "Poppins", sans-serif;
            font-weight: 600;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stDataFrame"] {
            border: 1px solid rgba(28, 138, 131, 0.22);
            border-radius: 10px;
            overflow: hidden;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(28, 138, 131, 0.22);
            border-radius: 10px;
        }
        @media (max-width: 640px) {
            .workspace-page-header { min-height: 0; padding: 1rem; }
            .workspace-page-title { font-size: 1.2rem; }
            .workspace-page-description { font-size: 0.75rem; }
            .workspace-page-icon { flex-basis: 40px; height: 40px; width: 40px; }
        }
        </style>
        """
    )
    st.html(
        f'<section class="workspace-page-header"><div class="workspace-page-icon">{escape(icon)}</div>'
        f'<div class="workspace-page-copy"><h1 class="workspace-page-title">{escape(title)}</h1>'
        f'<p class="workspace-page-description">{escape(description)}</p></div></section>'
    )