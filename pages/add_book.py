"""Add-book page."""

import streamlit as st
from sqlalchemy.orm import Session

from pages.book_form import render_book_form
from services.book_service import BookService
from services.catalog_service import CatalogService
from services.image_service import ImageService
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Render the Phase 1 add-book workflow."""
    render_page_header("Add book", "Build your collection with the details that make every book easy to find later.", "+")
    catalog = CatalogService(session)
    submitted_data = render_book_form(
        form_key="add_book_form", tags=catalog.list_tags(), collections=catalog.list_collections()
    )
    if submitted_data:
        saved_covers: list[str] = []
        try:
            cover_uploads = submitted_data.pop("cover_uploads")
            saved_covers = [ImageService.save_cover(upload) for upload in cover_uploads]
            if saved_covers:
                submitted_data["cover_image_path"] = saved_covers[0]
                submitted_data["image_paths"] = saved_covers
            book = BookService(session).create_book(submitted_data)
        except ValueError as error:
            for path in saved_covers:
                ImageService.delete_cover(path)
            st.error(str(error))
        else:
            st.success(f"Added '{book.book_name}' with ID {book.id}.")
