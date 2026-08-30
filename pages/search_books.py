"""Catalogue search page with normal and optional fuzzy matching."""

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Search books with normal modes or an optional ranked fuzzy match."""
    render_page_header("Search books", "Find titles, authors, notes, and collections with precise or flexible matching.", "S")
    service = BookService(session)
    query = st.text_input(
        "Search", placeholder="Title, author, category, publisher, ISBN, tags, or notes", key="search_query"
    )
    if not query.strip():
        st.info("Enter a search term to find books.")
        return
    fuzzy_enabled = st.toggle("Enable fuzzy search", value=False, help="Find similar spelling and typing variants.")
    if fuzzy_enabled:
        threshold = st.slider("Similarity threshold", min_value=0, max_value=100, value=70, step=5)
        results = service.fuzzy_search_books(query, threshold)
        if not results:
            st.warning("No similar books meet this threshold.")
            return
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Match score": round(result.score, 1),
                        "ID": result.book.id,
                        "Title": result.book.book_name,
                        "Author": result.book.author,
                        "Category": result.book.category or "-",
                    }
                    for result in results
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        return

    match_mode = st.selectbox("Normal match", ("Contains", "Starts with", "Exact"))
    normalized_query = query.strip().casefold()
    books = service.search_books(query)
    if match_mode != "Contains":
        def matches(book: object) -> bool:
            values = (
                book.book_name,
                book.author,
                book.category,
                book.publisher,
                book.isbn,
                book.notes,
                book.personal_review,
                *(tag.name for tag in book.tags),
                *(collection.name for collection in book.collections),
            )
            normalized_values = [str(value or "").casefold() for value in values]
            if match_mode == "Starts with":
                return any(value.startswith(normalized_query) for value in normalized_values)
            return any(value == normalized_query for value in normalized_values)

        books = [book for book in books if matches(book)]
    if not books:
        st.warning("No matching books found.")
        return
    st.dataframe(
        pd.DataFrame(
            [{"ID": book.id, "Title": book.book_name, "Author": book.author, "Category": book.category or "-"} for book in books]
        ),
        hide_index=True,
        width="stretch",
    )
