"""Edit-book page."""

import streamlit as st
from sqlalchemy.orm import Session

from pages.book_form import render_book_form
from services.book_service import BookService
from services.catalog_service import CatalogService
from services.image_service import ImageService
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Render a select-then-save edit workflow."""
    render_page_header("Edit book", "Keep your reading record current, from the cover and metadata to tags and notes.", "E")
    service = BookService(session)
    books = service.search_books()
    if not books:
        st.info("No books available to edit.")
        return
    choices = {f"{book.id}: {book.book_name} - {book.author}": book.id for book in books}
    selected_label = st.selectbox("Select a book", choices, key="edit_book_selector")
    book = service.get_book(choices[selected_label])
    if book is None:
        st.error("Book no longer exists.")
        return
    catalog = CatalogService(session)
    submitted_data = render_book_form(
        book,
        form_key=f"edit_book_form_{book.id}",
        tags=catalog.list_tags(),
        collections=catalog.list_collections(),
    )
    if submitted_data:
        new_covers: list[str] = []
        try:
            cover_uploads = submitted_data.pop("cover_uploads")
            new_covers = [ImageService.save_cover(upload) for upload in cover_uploads]
            if new_covers:
                submitted_data["image_paths"] = new_covers
                if not book.cover_image_path:
                    submitted_data["cover_image_path"] = new_covers[0]
            service.update_book(book.id, submitted_data)
        except ValueError as error:
            for path in new_covers:
                ImageService.delete_cover(path)
            st.error(str(error))
        else:
            st.success("Book updated.")
