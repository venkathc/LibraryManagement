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
        with st.expander("Basic information", expanded=True, icon=":material/menu_book:"):
            details_column, cover_column = st.columns((3, 2))
            with details_column:
                book_name = st.text_input("Book title *", value=book.book_name if book else "")
                author = st.text_input("Author *", value=book.author if book else "")
                publisher = st.text_input("Publisher", value=book.publisher or "" if book else "")
                isbn = st.text_input("ISBN", value=book.isbn or "" if book else "", help="Unique when supplied.")
                category_column, genre_column, language_column = st.columns(3)
                category = category_column.text_input("Category", value=book.category or "" if book else "")
                genre = genre_column.text_input("Genre", value=book.genre or "" if book else "")
                language = language_column.text_input("Language", value=book.language or "" if book else "")
            with cover_column:
                existing_images = [image.image_path for image in book.images] if book else []
                if book and book.cover_image_path and book.cover_image_path not in existing_images:
                    existing_images.insert(0, book.cover_image_path)
                cover_paths = [ImageService.resolve_cover(path) for path in existing_images]
                if visible_covers := [str(path) for path in cover_paths if path]:
                    st.image(visible_covers[0], width="stretch")
                    st.caption("Current cover")
                else:
                    st.info("Add a cover to make this book easier to recognise.", icon=":material/image:")
                cover_uploads = st.file_uploader(
                    "Upload or replace cover", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
                )

        with st.expander("Reading information", expanded=True, icon=":material/auto_stories:"):
            first, second, third = st.columns(3)
            with first:
                reading_status = st.selectbox(
                    "Reading status", READING_STATUSES,
                    index=READING_STATUSES.index(book.reading_status) if book else 0,
                )
            with second:
                book_format = st.selectbox(
                    "Format", ("Physical", "E-book", "Audiobook"),
                    index=("Physical", "E-book", "Audiobook").index(book.book_format) if book else 0,
                )
            with third:
                is_favourite = st.checkbox("Favourite", value=book.is_favourite if book else False)
            rating = st.segmented_control(
                "Rating",
                [1, 2, 3, 4, 5],
                default=book.rating if book and book.rating else None,
                format_func=lambda value: "★" * value,
                selection_mode="single",
                help="1 star: Poor. 2: Average. 3: Good. 4: Very good. 5: Excellent.",
            )
            st.caption("★ Poor · ★★ Average · ★★★ Good · ★★★★ Very good · ★★★★★ Excellent")

        with st.expander("Purchase information", expanded=False, icon=":material/payments:"):
            price_column, date_column = st.columns(2)
            with price_column:
                price = st.number_input(
                    "Purchase price (INR) *", min_value=0.0, value=float(book.price) if book else 0.0, step=1.0
                )
            with date_column:
                purchase_date = st.date_input(
                    "Purchase date", value=book.purchase_date if book and book.purchase_date else None
                )

        with st.expander("Personal information", expanded=False, icon=":material/edit_note:"):
            tag_lookup = {tag.name: tag.id for tag in tags or []}
            collection_lookup = {collection.name: collection.id for collection in collections or []}
            tags_column, collections_column = st.columns(2)
            selected_tags = tags_column.multiselect(
                "Tags", tag_lookup, default=[tag.name for tag in book.tags] if book else []
            )
            selected_collections = collections_column.multiselect(
                "Collections", collection_lookup,
                default=[collection.name for collection in book.collections] if book else [],
            )
            personal_review = st.text_area(
                "Personal review", value=book.personal_review or "" if book else "", height=110
            )
            notes = st.text_area("Notes", value=book.notes or "" if book else "", height=110)
        submitted = st.form_submit_button("Save changes" if is_editing else "Add book", type="primary")
    if not submitted:
        return None
    return {
        "book_name": book_name,
        "author": author,
        "category": category,
        "genre": genre,
        "book_format": book_format,
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
