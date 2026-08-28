"""View-books page."""

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from utils.formatters import format_inr


def render(session: Session) -> None:
    """Render a searchable catalogue table."""
    st.header("View Books")
    query = st.text_input("Search title, author, category, publisher, or ISBN", key="view_book_query")
    books = BookService(session).search_books(query)
    if not books:
        st.info("No books found. Add your first book from the sidebar.")
        return
    rows = [
        {
            "ID": book.id,
            "Title": book.book_name,
            "Author": book.author,
            "Category": book.category or "-",
            "Price": format_inr(book.price),
            "Status": book.reading_status,
            "Rating": book.rating or "-",
            "Favourite": "Yes" if book.is_favourite else "No",
        }
        for book in books
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
