"""Safe archive and trash management for the library catalogue."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.image_service import ImageService
from utils.formatters import format_inr
from utils.page_ui import render_page_header


def _rows(books: list[object]) -> list[dict[str, object]]:
    return [{"ID": book.id, "Title": book.book_name, "Author": book.author, "Category": book.category or "Uncategorised", "Price": format_inr(book.price), "Purchase date": book.purchase_date, "Tags": ", ".join(tag.name for tag in book.tags) or "-", "Collections": ", ".join(item.name for item in book.collections) or "-"} for book in books]


def _active_books(books: list[object]) -> list[object]:
    """Render live finder controls and return matching books."""
    query = st.text_input("Search title, author, category, tags, or purchase year", key="safe_delete_query")
    categories = sorted({book.category or "Uncategorised" for book in books})
    authors = sorted({book.author for book in books}, key=str.casefold)
    tags = sorted({tag.name for book in books for tag in book.tags}, key=str.casefold)
    collections = sorted({item.name for book in books for item in book.collections}, key=str.casefold)
    filters = st.columns(4)
    category = filters[0].selectbox("Category", ["All", *categories], key="safe_delete_category")
    author = filters[1].selectbox("Author", ["All", *authors], key="safe_delete_author")
    tag = filters[2].selectbox("Tag", ["All", *tags], key="safe_delete_tag")
    collection = filters[3].selectbox("Library / collection", ["All", *collections], key="safe_delete_collection")
    sort_by = st.selectbox("Sort books by", ("Title", "Author", "Category", "Date added", "Price"), key="safe_delete_sort")
    query = query.strip().casefold()
    matches = []
    for book in books:
        text = " ".join((book.book_name, book.author, book.category or "", str(book.purchase_date or ""), *(tag.name for tag in book.tags))).casefold()
        if (query and query not in text) or (category != "All" and (book.category or "Uncategorised") != category) or (author != "All" and book.author != author) or (tag != "All" and tag not in {item.name for item in book.tags}) or (collection != "All" and collection not in {item.name for item in book.collections}):
            continue
        matches.append(book)
    sort_keys = {"Title": lambda book: book.book_name.casefold(), "Author": lambda book: book.author.casefold(), "Category": lambda book: (book.category or "").casefold(), "Date added": lambda book: book.created_at or datetime.min, "Price": lambda book: book.price}
    return sorted(matches, key=sort_keys[sort_by])


def _preview_and_impact(all_books: list[object], selected: list[object]) -> bool:
    """Display selection details and return whether the selection can be removed."""
    if len(selected) == 1:
        book = selected[0]
        left, right = st.columns((1, 3))
        with left:
            if cover := ImageService.resolve_cover(book.cover_image_path):
                st.image(str(cover), width="stretch")
            else:
                st.info("No cover", icon=":material/menu_book:")
        with right:
            st.subheader(book.book_name)
            st.caption(f"{book.author} | {book.category or 'Uncategorised'}")
            st.write(f"**Price:** {format_inr(book.price)}  \\n+**Purchased:** {book.purchase_date or 'Not recorded'}  \\n+**Tags:** {', '.join(tag.name for tag in book.tags) or 'None'}")
            if book.notes:
                st.write(f"**Notes:** {book.notes}")
    investment = sum((book.price for book in selected), start=0)
    metrics = st.columns(3)
    metrics[0].metric("Investment affected", format_inr(investment), border=True)
    metrics[1].metric("Categories affected", len({book.category or "Uncategorised" for book in selected}), border=True)
    metrics[2].metric("Authors affected", len({book.author for book in selected}), border=True)
    categories = [book.category or "Uncategorised" for book in all_books]
    for book in selected:
        if sum(item.author == book.author for item in all_books) == 1:
            st.info(f"{book.book_name} is your only book by {book.author}.", icon=":material/person:")
        if book.price == max(item.price for item in all_books):
            st.warning(f"{book.book_name} is the most expensive book in this view.", icon=":material/payments:")
        if categories.count(book.category or "Uncategorised") == max(categories.count(item) for item in categories):
            st.caption(f"{book.book_name} belongs to your largest category.")
    loan_titles = [book.book_name for book in selected if any(loan.actual_return_date is None for loan in book.loans)]
    if loan_titles:
        st.error(f"Resolve the active loan before removing: {', '.join(loan_titles)}.", icon=":material/error:")
        return False
    return True


def _manage_active(service: BookService) -> None:
    books = service.search_books()
    if not books:
        st.info("Your active library is empty. Archived books and Trash remain available below.", icon=":material/library_books:")
        return
    matches = _active_books(books)
    if not matches:
        st.warning("No active books match these filters.", icon=":material/filter_alt_off:")
        return
    st.dataframe(pd.DataFrame(_rows(matches)), hide_index=True, width="stretch")
    options = {f"{book.id}: {book.book_name} - {book.author}": book for book in matches}
    selected = [options[label] for label in st.multiselect("Select books to manage", options, key="safe_delete_selection")]
    if not selected:
        st.caption("Select one or more books to review their impact before archiving or moving them to Trash.")
        return
    if not _preview_and_impact(books, selected):
        return
    actions = st.columns(2)
    if actions[0].button("Archive selected", icon=":material/archive:", key="archive_selected", width="stretch"):
        service.archive_books([book.id for book in selected])
        st.toast(f"Archived {len(selected)} book(s).", icon=":material/archive:")
        st.rerun()
    if actions[1].button("Move selected to Trash", type="primary", icon=":material/delete:", key="trash_selected", width="stretch"):
        service.move_to_trash([book.id for book in selected])
        st.toast(f"Moved {len(selected)} book(s) to Trash. They can be restored for 30 days.", icon=":material/delete:")
        st.rerun()


def _recovery(service: BookService, visibility: str, title: str) -> None:
    books = service.search_books(visibility=visibility)
    if not books:
        st.info(f"No books in {title.lower()}.", icon=":material/inventory_2:")
        return
    st.dataframe(pd.DataFrame(_rows(books)), hide_index=True, width="stretch")
    options = {f"{book.id}: {book.book_name} - {book.author}": book for book in books}
    selected = [options[label] for label in st.multiselect(f"Select books in {title}", options, key=f"{visibility}_selection")]
    if not selected:
        return
    if st.button("Restore selected", icon=":material/restore:", key=f"restore_{visibility}"):
        service.restore_books([book.id for book in selected])
        st.success(f"Restored {len(selected)} book(s) to your active library.")
        st.rerun()
    if visibility == "trash":
        remaining = [max(0, 30 - (datetime.now() - book.deleted_at).days) for book in selected if book.deleted_at]
        st.caption(f"Selected books remain recoverable for {min(remaining) if remaining else 30} more day(s).")
        confirmed = st.checkbox("I understand permanent deletion cannot be undone.", key="permanent_delete_confirm")
        if st.button("Delete permanently", type="primary", icon=":material/delete_forever:", disabled=not confirmed, key="permanent_delete"):
            for book in selected:
                service.delete_book(book.id)
            st.success(f"Permanently deleted {len(selected)} book(s).")
            st.rerun()


def render(session: Session) -> None:
    """Render safe archive, trash, restoration, and permanent deletion workflows."""
    render_page_header("Manage library records", "Archive books or move them to Trash with a clear impact preview and a 30-day recovery window.", "!")
    service = BookService(session)
    expired_count = service.purge_expired_trash()
    if expired_count:
        st.info(f"Permanently removed {expired_count} expired Trash record(s).", icon=":material/delete_forever:")
    active, archive, trash = st.tabs(["Active library", "Archived", "Trash"])
    with active:
        _manage_active(service)
    with archive:
        _recovery(service, "archived", "Archive")
    with trash:
        _recovery(service, "trash", "Trash")
