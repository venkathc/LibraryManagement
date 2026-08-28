"""Shared Streamlit form for creating and editing books."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from models import Book, Collection, Tag
from services.image_service import ImageService
from utils.constants import READING_STATUSES


def render_book_form(
    book: Book | None = None,
    form_key: str = "book_form",
    tags: list[Tag] | None = None,
    collections: list[Collection] | None = None,
) -> dict[str, object] | None:
    """Render a book form and return submitted data, or None."""
    is_editing = book is not None
    with st.form(form_key, clear_on_submit=not is_editing):
        left_column, right_column = st.columns(2)
        with left_column:
            book_name = st.text_input("Book name *", value=book.book_name if book else "")
            author = st.text_input("Author *", value=book.author if book else "")
            category = st.text_input("Category / genre", value=book.category or "" if book else "")
            price = st.number_input(
                "Price (INR) *", min_value=0.0, value=float(book.price) if book else 0.0, step=1.0
            )
            purchase_date = st.date_input(
                "Purchase date", value=book.purchase_date if book and book.purchase_date else None
            )
        with right_column:
            publisher = st.text_input("Publisher", value=book.publisher or "" if book else "")
            isbn = st.text_input("ISBN", value=book.isbn or "" if book else "", help="Unique when supplied.")
            language = st.text_input("Language", value=book.language or "" if book else "")
            rating = st.selectbox(
                "Rating", [None, 1, 2, 3, 4, 5], index=([None, 1, 2, 3, 4, 5].index(book.rating) if book and book.rating else 0)
            )
            reading_status = st.selectbox(
                "Reading status", READING_STATUSES,
                index=READING_STATUSES.index(book.reading_status) if book else 0,
            )
            is_favourite = st.checkbox("Favourite", value=book.is_favourite if book else False)
        personal_review = st.text_area("Personal review", value=book.personal_review or "" if book else "")
        notes = st.text_area("Notes", value=book.notes or "" if book else "")
        existing_images = [image.image_path for image in book.images] if book else []
        if book and book.cover_image_path and book.cover_image_path not in existing_images:
            existing_images.insert(0, book.cover_image_path)
        cover_paths = [ImageService.resolve_cover(path) for path in existing_images]
        if visible_covers := [str(path) for path in cover_paths if path]:
            st.caption("Current book images")
            st.image(visible_covers, width=120)
        cover_uploads = st.file_uploader(
            "Book images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
        )
        tag_lookup = {tag.name: tag.id for tag in tags or []}
        collection_lookup = {collection.name: collection.id for collection in collections or []}
        selected_tags = st.multiselect(
            "Tags", tag_lookup, default=[tag.name for tag in book.tags] if book else []
        )
        selected_collections = st.multiselect(
            "Collections", collection_lookup,
            default=[collection.name for collection in book.collections] if book else [],
        )
        submitted = st.form_submit_button("Save changes" if is_editing else "Add book", type="primary")
    if not submitted:
        return None
    return {
        "book_name": book_name,
        "author": author,
        "category": category,
        "price": Decimal(str(price)),
        "purchase_date": purchase_date,
        "publisher": publisher,
        "isbn": isbn,
        "language": language,
        "rating": rating,
        "reading_status": reading_status,
        "personal_review": personal_review,
        "notes": notes,
        "is_favourite": is_favourite,
        "tag_ids": [tag_lookup[name] for name in selected_tags],
        "collection_ids": [collection_lookup[name] for name in selected_collections],
        "cover_uploads": cover_uploads,
    }
