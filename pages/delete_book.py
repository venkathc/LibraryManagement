"""Delete-book page with explicit confirmation."""

import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService


def render(session: Session) -> None:
    """Render a two-step, deliberate deletion flow."""
    st.header("Delete Book")
    service = BookService(session)
    books = service.search_books()
    if not books:
        st.info("No books available to delete.")
        return
    choices = {f"{book.id}: {book.book_name} - {book.author}": book.id for book in books}
    selected_label = st.selectbox("Select a book", choices, key="delete_book_selector")
    book = service.get_book(choices[selected_label])
    if book is None:
        st.error("Book no longer exists.")
        return
    st.warning(f"You are about to delete '{book.book_name}' by {book.author}.")
    confirm = st.checkbox("I understand this action cannot be undone.", key=f"delete_confirm_{book.id}")
    if st.button("Delete book", type="primary", disabled=not confirm, key=f"delete_button_{book.id}"):
        service.delete_book(book.id)
        st.success("Book deleted.")
        st.rerun()
