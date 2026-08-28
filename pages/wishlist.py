"""Wishlist management page."""

from decimal import Decimal

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.export_service import ExportService
from services.wishlist_service import WishlistService
from utils.constants import READING_STATUSES, WISHLIST_PRIORITIES, WISHLIST_STATUSES


def render(session: Session) -> None:
    """Render wishlist creation, filtering, deletion, and purchase conversion."""
    st.header("Wishlist")
    service = WishlistService(session)
    with st.form("wishlist_add_form", clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            book_name = st.text_input("Book name *")
            author = st.text_input("Author")
            category = st.text_input("Category")
            expected_price = st.number_input("Expected price", min_value=0.0, value=0.0)
        with right:
            priority = st.selectbox("Priority", WISHLIST_PRIORITIES)
            expected_purchase_date = st.date_input("Expected purchase date", value=None)
            status = st.selectbox("Status", WISHLIST_STATUSES)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add to wishlist", type="primary")
    if submitted:
        try:
            service.create_item({"book_name": book_name, "author": author, "category": category, "expected_price": Decimal(str(expected_price)), "priority": priority, "expected_purchase_date": expected_purchase_date, "notes": notes, "status": status})
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("Wishlist item added.")
            st.rerun()

    filters = st.columns(3)
    query = filters[0].text_input("Search wishlist")
    selected_priority = filters[1].selectbox("Priority filter", ("All", *WISHLIST_PRIORITIES))
    selected_status = filters[2].selectbox("Status filter", ("All", *WISHLIST_STATUSES))
    items = service.list_items(query, None if selected_priority == "All" else selected_priority, None if selected_status == "All" else selected_status)
    if not items:
        st.info("No wishlist items match these filters.")
        return
    frame = ExportService.wishlist_frame(items)
    st.dataframe(frame, hide_index=True, use_container_width=True)
    st.download_button("Download wishlist CSV", ExportService.to_csv(frame), "wishlist.csv", "text/csv")
    if ExportService.excel_available():
        st.download_button("Download wishlist Excel", ExportService.to_excel({"Wishlist": frame}), "wishlist.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    choices = {f"{item.id}: {item.book_name}": item for item in items}
    selected = st.selectbox("Manage item", choices, key="wishlist_item")
    item = choices[selected]
    action_columns = st.columns(2)
    with action_columns[0]:
        if item.status != "Purchased" and st.button("Mark as purchased", key=f"purchase_{item.id}"):
            if not item.author:
                st.warning("Add an author before converting this item to a book.")
            else:
                try:
                    book = service.mark_purchased(item.id, {"book_name": item.book_name, "author": item.author, "category": item.category, "price": item.expected_price or Decimal("0"), "purchase_date": item.expected_purchase_date, "publisher": "", "isbn": "", "language": "", "rating": None, "reading_status": "Unread", "personal_review": "", "notes": item.notes or "", "is_favourite": False})
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.success(f"Created book ID {book.id} and marked the wishlist item purchased.")
                    st.rerun()
    with action_columns[1]:
        if st.button("Delete item", key=f"delete_wishlist_{item.id}"):
            service.delete_item(item.id)
            st.success("Wishlist item deleted.")
            st.rerun()
