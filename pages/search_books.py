"""Intelligent, library-scoped catalogue discovery workspace."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.image_service import ImageService
from services.loan_service import LoanService
from utils.formatters import format_inr
from utils.page_ui import render_page_header


def _styles() -> None:
    st.html("""<style>
    .search-heading{color:#123c55;font:700 1rem/1.25 'Poppins',sans-serif;margin:0}.search-copy{color:#55717b;font:.78rem/1.45 'Poppins',sans-serif;margin:.2rem 0 .8rem}.search-cover{align-items:center;background:linear-gradient(145deg,#146c72,#123c55);border-radius:6px;color:#f7d574;display:flex;font:700 1.1rem 'Poppins',sans-serif;height:145px;justify-content:center}.result-title{color:#123c55;font:700 .9rem/1.3 'Poppins',sans-serif;margin:.55rem 0 .1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.result-meta{color:#55717b;font:.72rem/1.4 'Poppins',sans-serif;margin:0}.shelf{background:linear-gradient(180deg,#8e684b,#42291f);border-radius:8px;display:flex;gap:.45rem;min-height:215px;overflow-x:auto;padding:1rem}.spine{background:linear-gradient(90deg,#123c55,#1c8a83);border-left:3px solid rgba(255,255,255,.18);border-radius:3px;color:#fff;flex:0 0 54px;font:600 .67rem/1.25 'Poppins',sans-serif;min-height:180px;overflow:hidden;padding:.5rem .3rem;writing-mode:vertical-rl}[data-testid='stMainBlockContainer'] [data-testid='stMetric']{background:#fff;border-radius:8px}[data-testid='stMainBlockContainer'] [data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(135deg,rgba(247,252,251,.96),#fff);box-shadow:0 6px 18px rgba(18,60,85,.05)}</style>""")


def _availability(session: Session, library_id: int | None) -> dict[int, str]:
    return {loan.book_id: loan.status for loan in LoanService(session).list_loans(library_id) if loan.actual_return_date is None}


def _matches(book: object, query: str, mode: str) -> bool:
    values = (book.book_name, book.author, book.category, book.publisher, book.isbn, book.language, book.notes, book.personal_review, *(tag.name for tag in book.tags), *(collection.name for collection in book.collections))
    wanted = query.casefold()
    entries = [str(value or "").casefold() for value in values]
    if mode == "Exact match":
        return any(entry == wanted for entry in entries)
    if mode == "Starts with":
        return any(entry.startswith(wanted) for entry in entries)
    if mode == "Ends with":
        return any(entry.endswith(wanted) for entry in entries)
    return any(wanted in entry for entry in entries)


def _filters(books: list, availability: dict[int, str]) -> list:
    with st.expander("Advanced filters", icon=":material/tune:"):
        first, second, third, fourth = st.columns(4)
        categories = first.multiselect("Category", sorted({book.category or "Uncategorised" for book in books}), key="search_categories")
        authors = second.multiselect("Author", sorted({book.author for book in books}), key="search_authors")
        publishers = third.multiselect("Publisher", sorted({book.publisher or "Unspecified" for book in books}), key="search_publishers")
        statuses = fourth.multiselect("Reading status", sorted({book.reading_status for book in books}), key="search_statuses")
        first, second, third, fourth = st.columns(4)
        languages = first.multiselect("Language", sorted({book.language or "Unspecified" for book in books}), key="search_languages")
        rating = second.multiselect("Rating", [1, 2, 3, 4, 5], key="search_ratings")
        state = third.selectbox("Availability", ["All", "Available", "Borrowed", "Overdue"], key="search_availability")
        favourite = fourth.selectbox("Favourite", ["All", "Favourites only"], key="search_favourite")
        max_price = max((float(book.price) for book in books), default=0.0)
        if max_price > 0:
            prices = st.slider("Price range", 0.0, max_price, (0.0, max_price), key="search_price")
        else:
            st.caption("Price filtering is available when matching books have prices.")
            prices = (0.0, 0.0)
        if st.button("Reset filters", icon=":material/filter_alt_off:", key="search_reset_filters"):
            for key in ("search_categories", "search_authors", "search_publishers", "search_statuses", "search_languages", "search_ratings", "search_availability", "search_favourite", "search_price"):
                st.session_state.pop(key, None)
            st.rerun()
    result = [book for book in books if (not categories or (book.category or "Uncategorised") in categories) and (not authors or book.author in authors) and (not publishers or (book.publisher or "Unspecified") in publishers) and (not statuses or book.reading_status in statuses) and (not languages or (book.language or "Unspecified") in languages) and (not rating or book.rating in rating) and prices[0] <= float(book.price) <= prices[1] and (favourite != "Favourites only" or book.is_favourite)]
    if state == "Available":
        return [book for book in result if book.id not in availability]
    if state == "Borrowed":
        return [book for book in result if availability.get(book.id) == "Lent"]
    if state == "Overdue":
        return [book for book in result if availability.get(book.id) == "Overdue"]
    return result


@st.dialog("Book preview", width="large")
def _preview(book: object, loan_status: str | None) -> None:
    cover, copy = st.columns((1, 2))
    with cover:
        path = ImageService.resolve_cover(book.cover_image_path)
        if path:
            st.image(str(path), width="stretch")
        else:
            st.html('<div class="search-cover">BOOK</div>')
    with copy:
        st.subheader(book.book_name)
        st.caption(f"{book.author} · {book.publisher or 'Publisher not set'}")
        st.badge(book.reading_status, icon=":material/auto_stories:", color="blue")
        st.badge("Overdue" if loan_status == "Overdue" else "Borrowed" if loan_status else "Available", icon=":material/warning:" if loan_status == "Overdue" else ":material/check_circle:", color="red" if loan_status == "Overdue" else "orange" if loan_status else "green")
        st.write(f"**Category:** {book.category or 'Uncategorised'}  \n**Rating:** {book.rating or 'Not rated'} / 5  \n**Price:** {format_inr(book.price)}")
        st.write(book.personal_review or book.notes or "No summary or notes have been added yet.")


def _render_results(books: list, availability: dict[int, str]) -> None:
    view = st.segmented_control("Results view", ["Cards", "Table", "Gallery", "Bookshelf"], default=st.session_state.get("search_view", "Cards"), key="search_view") or "Cards"
    if view == "Table":
        rows = [{"Title": book.book_name, "Author": book.author, "Category": book.category or "-", "Status": book.reading_status, "Availability": "Overdue" if availability.get(book.id) == "Overdue" else "Borrowed" if book.id in availability else "Available", "Rating": book.rating, "Library": book.library.name if book.library else "-"} for book in books]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=460)
        return
    if view == "Bookshelf":
        st.html('<div class="shelf">' + ''.join(f'<div class="spine">{book.book_name}<br><br>{book.author}</div>' for book in books) + '</div>')
        selected = st.selectbox("Preview a book", {f"{book.book_name} · {book.author}": book for book in books}, key="search_shelf_selection")
        if st.button("Open preview", icon=":material/visibility:", key="search_shelf_preview"):
            _preview({f"{book.book_name} · {book.author}": book for book in books}[selected], availability.get({f"{book.book_name} · {book.author}": book for book in books}[selected].id))
        return
    columns = 5 if view == "Gallery" else 4
    for offset in range(0, len(books), columns):
        for column, book in zip(st.columns(columns), books[offset:offset + columns]):
            with column.container(border=True):
                path = ImageService.resolve_cover(book.cover_image_path)
                if path:
                    st.image(str(path), width="stretch")
                else:
                    st.html('<div class="search-cover">BOOK</div>')
                st.html(f'<p class="result-title">{book.book_name}</p><p class="result-meta">{book.author}</p>')
                st.caption(f"{book.category or 'Uncategorised'} · {book.reading_status} · {book.rating or '-'} / 5")
                st.badge("Overdue" if availability.get(book.id) == "Overdue" else "Borrowed" if book.id in availability else "Available", color="red" if availability.get(book.id) == "Overdue" else "orange" if book.id in availability else "green")
                if st.button("Preview", icon=":material/visibility:", key=f"search_preview_{book.id}", width="stretch"):
                    _preview(book, availability.get(book.id))


def render(session: Session) -> None:
    """Render fast, rich discovery within the active library."""
    render_page_header("Search books", "Find books, authors, categories, ISBNs, notes, collections, and more.", "S")
    _styles()
    service = BookService(session)
    library_id = st.session_state.get("selected_library_id")
    catalogue = service.search_books(library_id=library_id)
    availability = _availability(session, library_id)
    total, authors, categories = st.columns(3)
    total.metric(":material/menu_book: Total books", len(catalogue), border=True)
    authors.metric(":material/edit: Total authors", len({book.author for book in catalogue}), border=True)
    categories.metric(":material/sell: Categories", len({book.category for book in catalogue if book.category}), border=True)
    query = st.text_input("Search books", placeholder="Title, author, ISBN, publisher, tags, language, notes, or collections", key="search_query", icon=":material/search:")
    chips = st.pills("Quick filters", ["All books", "Unread", "Reading", "Completed", "Favourites", "Recently added", "Highest rated"], default=st.session_state.get("search_chip", "All books"), key="search_chip", selection_mode="single") or "All books"
    with st.expander("Search options", icon=":material/manage_search:"):
        mode, fuzzy = st.columns(2)
        match_mode = mode.selectbox("Match mode", ["Contains", "Starts with", "Ends with", "Exact match"], key="search_match_mode")
        fuzzy_enabled = fuzzy.toggle("Fuzzy matching", value=False, key="search_fuzzy", help="Find titles with similar spelling.")
        threshold = st.slider("Fuzzy similarity", 50, 100, 70, 5, key="search_threshold", disabled=not fuzzy_enabled)
    if query.strip():
        history = st.session_state.setdefault("recent_searches", [])
        if query not in history:
            history.insert(0, query)
            del history[10:]
    with st.container(border=True):
        st.html('<p class="search-heading">Discovery tools</p><p class="search-copy">Use filters for precision, or fuzzy matching when the title is only partly remembered.</p>')
        saved = st.session_state.setdefault("saved_searches", [])
        save, recent = st.columns(2)
        if save.button("Save current search", icon=":material/bookmark_add:", disabled=not query.strip(), key="save_search") and query not in saved:
            saved.append(query)
            st.toast("Search saved for this session.", icon=":material/bookmark_added:")
        if recent.button("Clear recent searches", icon=":material/delete_sweep:", disabled=not st.session_state.get("recent_searches"), key="clear_searches"):
            st.session_state.recent_searches = []
            st.rerun()
        if st.session_state.get("recent_searches"):
            st.caption("Recent: " + " · ".join(st.session_state.recent_searches))
        if saved:
            st.caption("Saved: " + " · ".join(saved))
    results = catalogue
    if query.strip():
        if fuzzy_enabled:
            results = [match.book for match in service.fuzzy_search_books(query, threshold) if match.book.library_id == library_id]
        else:
            results = [book for book in catalogue if _matches(book, query.strip(), match_mode)]
    if chips == "Unread":
        results = [book for book in results if book.reading_status == "Unread"]
    elif chips == "Reading":
        results = [book for book in results if book.reading_status == "Reading"]
    elif chips == "Completed":
        results = [book for book in results if book.reading_status == "Read"]
    elif chips == "Favourites":
        results = [book for book in results if book.is_favourite]
    elif chips == "Recently added":
        results = sorted(results, key=lambda book: book.created_at, reverse=True)[:12]
    elif chips == "Highest rated":
        results = sorted(results, key=lambda book: book.rating or 0, reverse=True)
    results = _filters(results, availability)
    if not query.strip():
        st.html('<p class="search-heading">Discover your library</p><p class="search-copy">Recently added and highly rated books are ready to explore.</p>')
    if not results:
        st.info("No books found matching your search. Try another keyword or reset the current filters.", icon=":material/search_off:")
        return
    st.caption(f"{len(results):,} matching books")
    _render_results(results, availability)
