"""Modern, library-scoped catalogue workspace."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.export_service import ExportService
from services.image_service import ImageService
from services.loan_service import LoanService
from services.wishlist_service import WishlistService
from utils.formatters import format_inr
from utils.page_ui import render_page_header


def _styles() -> None:
    st.html("""<style>
    .books-heading{color:#123c55;font:700 1rem/1.25 'Poppins',sans-serif;margin:0}.books-copy{color:#55717b;font:.78rem/1.45 'Poppins',sans-serif;margin:.2rem 0 .8rem}.cover-placeholder{align-items:center;background:linear-gradient(145deg,#146c72,#123c55);border-radius:6px;color:#f7d574;display:flex;font:700 1.15rem 'Poppins',sans-serif;height:150px;justify-content:center}.book-name{color:#123c55;font:700 .88rem/1.3 'Poppins',sans-serif;margin:.6rem 0 .1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.book-meta{color:#55717b;font:.72rem/1.35 'Poppins',sans-serif;margin:0}.shelf{background:linear-gradient(180deg,#8e684b,#42291f);border-radius:8px;display:flex;gap:.45rem;min-height:220px;overflow-x:auto;padding:1rem}.spine{background:linear-gradient(90deg,#123c55,#1c8a83);border-left:3px solid rgba(255,255,255,.16);border-radius:3px;color:#fff;flex:0 0 54px;font:600 .67rem/1.25 'Poppins',sans-serif;min-height:185px;overflow:hidden;padding:.55rem .35rem;writing-mode:vertical-rl}[data-testid='stMainBlockContainer'] [data-testid='stMetric']{background:#fff;border-radius:8px}[data-testid='stMainBlockContainer'] [data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(135deg,rgba(247,252,251,.96),#fff);box-shadow:0 6px 18px rgba(18,60,85,.05)}</style>""")


def _active_loans(session: Session, library_id: int | None) -> dict[int, str]:
    return {loan.book_id: loan.status for loan in LoanService(session).list_loans(library_id) if loan.actual_return_date is None}


def _filter(books: list, loans: dict[int, str]) -> list:
    with st.expander("Filters", icon=":material/tune:"):
        left, middle, right, last = st.columns(4)
        categories = left.multiselect("Category", sorted({book.category or "Uncategorised" for book in books}), key="books_categories")
        authors = middle.multiselect("Author", sorted({book.author for book in books}), key="books_authors")
        statuses = right.multiselect("Reading status", sorted({book.reading_status for book in books}), key="books_statuses")
        availability = last.selectbox("Availability", ["All", "Available", "Borrowed", "Overdue"], key="books_availability")
        max_price = max((float(book.price) for book in books), default=0.0)
        price = st.slider("Price range", 0.0, max_price, (0.0, max_price), key="books_price")
    result = [book for book in books if (not categories or (book.category or "Uncategorised") in categories) and (not authors or book.author in authors) and (not statuses or book.reading_status in statuses) and price[0] <= float(book.price) <= price[1]]
    if availability == "Available":
        return [book for book in result if book.id not in loans]
    if availability == "Borrowed":
        return [book for book in result if loans.get(book.id) == "Lent"]
    if availability == "Overdue":
        return [book for book in result if loans.get(book.id) == "Overdue"]
    return result


def _overview(books: list, loans: dict[int, str], wishlist_count: int) -> None:
    added = sum(book.created_at and book.created_at.month == date.today().month and book.created_at.year == date.today().year for book in books)
    cards = ((":material/menu_book: Total books", len(books), f"{added} added this month", "normal"), (":material/check_circle: Available", sum(book.id not in loans for book in books), "Ready to read", "normal"), (":material/auto_stories: Reading", sum(book.reading_status == "Reading" for book in books), None, "normal"), (":material/task_alt: Completed", sum(book.reading_status == "Read" for book in books), None, "normal"), (":material/star: Favourites", sum(book.is_favourite for book in books), None, "normal"), (":material/favorite: Wishlist", wishlist_count, None, "normal"), (":material/import_contacts: Borrowed", sum(status == "Lent" for status in loans.values()), None, "normal"), (":material/warning: Overdue", sum(status == "Overdue" for status in loans.values()), "Needs attention", "inverse"))
    for group in (cards[:4], cards[4:]):
        for column, (label, value, delta, color) in zip(st.columns(4), group):
            column.metric(label, value, delta, delta_color=color, border=True)
    st.metric(":material/payments: Total library value", format_inr(sum(book.price for book in books)), f"Across {len(books)} books", border=True)


@st.dialog("Book details", width="large")
def _details(book, loan_status: str | None) -> None:
    cover, information = st.columns((1, 2))
    with cover:
        path = ImageService.resolve_cover(book.cover_image_path)
        if path:
            st.image(str(path), width="stretch")
        else:
            st.html('<div class="cover-placeholder">BOOK</div>')
    with information:
        st.subheader(book.book_name)
        st.caption(f"{book.author} · {book.publisher or 'Publisher not set'}")
        st.badge(book.reading_status, icon=":material/auto_stories:", color="blue")
        if loan_status:
            st.badge("Overdue" if loan_status == "Overdue" else "Borrowed", icon=":material/warning:" if loan_status == "Overdue" else ":material/import_contacts:", color="red" if loan_status == "Overdue" else "orange")
        st.write(f"**Category:** {book.category or 'Uncategorised'}  \n**ISBN:** {book.isbn or 'Not recorded'}  \n**Price:** {format_inr(book.price)}  \n**Rating:** {book.rating or 'Not rated'} / 5")
    overview, notes, collections = st.tabs(["Overview", "Notes & review", "Collections"])
    with overview:
        st.write(book.personal_review or "No review has been added.")
    with notes:
        st.write(book.notes or "No reading notes have been added.")
    with collections:
        st.write(", ".join(item.name for item in book.collections) or "Not in a collection.")


def _card(book, status: str | None) -> None:
    path = ImageService.resolve_cover(book.cover_image_path)
    if path:
        st.image(str(path), width="stretch")
    else:
        st.html('<div class="cover-placeholder">BOOK</div>')
    st.html(f'<p class="book-name">{book.book_name}</p><p class="book-meta">{book.author}</p>')
    st.caption(f"{book.category or 'Uncategorised'} · {book.reading_status} · {format_inr(book.price)}")
    if status:
        st.caption("Overdue" if status == "Overdue" else "Borrowed")
    if st.button("View", icon=":material/visibility:", key=f"book_view_{book.id}", width="stretch"):
        _details(book, status)


def _collection(books: list, loans: dict[int, str]) -> None:
    view = st.segmented_control("View", ["Table", "Cards", "Bookshelf", "Reading board"], default=st.session_state.get("books_view", "Cards"), key="books_view") or "Cards"
    if view == "Table":
        rows = [{"Title": book.book_name, "Author": book.author, "Category": book.category or "-", "Reading": book.reading_status, "Availability": "Overdue" if loans.get(book.id) == "Overdue" else "Borrowed" if book.id in loans else "Available", "Rating": book.rating, "Price": format_inr(book.price), "Favourite": "Yes" if book.is_favourite else ""} for book in books]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=480)
    elif view == "Cards":
        for offset in range(0, len(books), 4):
            for column, book in zip(st.columns(4), books[offset:offset + 4]):
                with column.container(border=True):
                    _card(book, loans.get(book.id))
    elif view == "Bookshelf":
        st.html('<div class="shelf">' + ''.join(f'<div class="spine">{book.book_name}<br><br>{book.author}</div>' for book in books) + '</div>')
        labels = {f"{book.book_name} · {book.author}": book for book in books}
        selected_label = st.selectbox("Open a book", labels, key="bookshelf_selection")
        chosen = labels[selected_label]
        if st.button("Open details", icon=":material/visibility:", key="bookshelf_details"):
            _details(chosen, loans.get(chosen.id))
    else:
        board = {"To read": [book for book in books if book.reading_status == "Unread"], "Currently reading": [book for book in books if book.reading_status == "Reading"], "Completed": [book for book in books if book.reading_status == "Read"]}
        for column, (label, items) in zip(st.columns(3), board.items()):
            with column.container(border=True):
                st.markdown(f"**{label}**")
                for book in items:
                    if st.button(book.book_name, icon=":material/menu_book:", key=f"kanban_{label}_{book.id}", width="stretch"):
                        _details(book, loans.get(book.id))


def render(session: Session) -> None:
    """Render a searchable, responsive catalogue for the active library."""
    render_page_header("Books", "Search, organise, and enjoy your library from one focused catalogue workspace.", "B")
    _styles()
    service = BookService(session)
    library_id = st.session_state.get("selected_library_id")
    query = st.text_input("Search your library", placeholder="Title, author, ISBN, category, publisher, tags, language, or notes", key="view_book_query", icon=":material/search:")
    books = service.search_books(query, library_id=library_id)
    loans = _active_loans(session, library_id)
    _overview(books, loans, len(WishlistService(session).list_items()))
    with st.container(border=True):
        st.html('<p class="books-heading">Library workspace</p><p class="books-copy">Filter the catalogue, choose a view, and manage several books at once.</p>')
        add, export = st.columns(2)
        add.page_link("pages/add_book.py", label="Add book", icon=":material/add_circle:")
        export.download_button("Export CSV", ExportService.to_csv(ExportService.books_frame(books)), "books.csv", "text/csv", icon=":material/download:", width="stretch")
        filtered = _filter(books, loans)
        labels = {f"{book.book_name} · {book.author}": book.id for book in filtered}
        selected_ids = st.multiselect("Select books for bulk actions", labels, key="books_bulk_selection")
        action, apply = st.columns((3, 1), vertical_alignment="bottom")
        choice = action.selectbox("Bulk action", ["Mark as favourite", "Remove favourite", "Move to trash"], key="books_bulk_action")
        if apply.button("Apply", icon=":material/done:", disabled=not selected_ids, key="books_apply_bulk", width="stretch"):
            if choice == "Move to trash":
                service.move_to_trash(selected_ids)
            else:
                for book in [book for book in filtered if book.id in selected_ids]:
                    book.is_favourite = choice == "Mark as favourite"
                    service.repository.update(book)
            st.toast("Books updated.", icon=":material/check_circle:")
            st.rerun()
    if not filtered:
        st.info("No books available yet. Add a book or adjust the current search and filters.", icon=":material/menu_book:")
        return
    st.caption(f"Showing {len(filtered):,} of {len(books):,} books in the active library.")
    _collection(filtered, loans)
