"""Visual purchase-planning workspace for desired books."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from html import escape

import streamlit as st
from sqlalchemy.orm import Session

from services.export_service import ExportService
from services.wishlist_service import WishlistService
from utils.constants import WISHLIST_PRIORITIES, WISHLIST_STATUSES
from utils.formatters import format_inr
from utils.page_ui import render_page_header


def _styles() -> None:
    st.html("""<style>
    .wish-title{color:#123c55;font:700 1rem/1.25 'Poppins',sans-serif;margin:0}.wish-copy{color:#55717b;font:.78rem/1.45 'Poppins',sans-serif;margin:.2rem 0 .8rem}.wish-cover{align-items:center;background:linear-gradient(145deg,#9b5b39,#c98f4b);border-radius:6px;color:#fff8e7;display:flex;font:700 1.1rem 'Poppins',sans-serif;height:145px;justify-content:center}.wish-card-title{color:#123c55;font:700 .9rem/1.3 'Poppins',sans-serif;margin:.55rem 0 .1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.wish-meta{color:#55717b;font:.72rem/1.4 'Poppins',sans-serif;margin:0}.wish-priority{border-radius:99px;display:inline-block;font:600 .68rem/1 'Poppins',sans-serif;margin:.45rem 0;padding:.32rem .5rem}.priority-high{background:#fde8e7;color:#b3382e}.priority-medium{background:#fff0d9;color:#9c5a00}.priority-low{background:#e3f4ea;color:#237745}[data-testid='stMainBlockContainer'] [data-testid='stMetric']{background:#fff;border-radius:8px}[data-testid='stMainBlockContainer'] [data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(135deg,rgba(255,250,243,.94),#fff);box-shadow:0 6px 18px rgba(91,59,35,.06)}</style>""")


def _priority_class(priority: str) -> str:
    return {"High": "priority-high", "Medium": "priority-medium", "Low": "priority-low"}[priority]


def _overview(items: list) -> None:
    planned = [item for item in items if item.status in {"Planned", "Ordered"}]
    purchased = [item for item in items if item.status == "Purchased"]
    high = [item for item in planned if item.priority == "High"]
    upcoming = [item for item in planned if item.expected_purchase_date and item.expected_purchase_date >= date.today()]
    estimated = sum((item.expected_price or Decimal("0") for item in items), Decimal("0"))
    cards = ((":material/favorite: Wishlist books", len(items), f"{len(planned)} to plan", "normal"), (":material/payments: Estimated cost", format_inr(estimated), None, "normal"), (":material/local_fire_department: High priority", len(high), "Next to consider", "inverse"), (":material/check_circle: Purchased", len(purchased), None, "normal"), (":material/event: Upcoming", len(upcoming), None, "normal"))
    for column, (label, value, detail, color) in zip(st.columns(5), cards):
        column.metric(label, value, detail, delta_color=color, border=True)
    progress = len(purchased) / len(items) if items else 0
    st.progress(progress, text=f"Purchase progress: {len(purchased)} of {len(items)} books purchased")


def _quick_add(service: WishlistService) -> None:
    with st.container(border=True):
        st.html('<p class="wish-title">Quick add a wishlist book</p><p class="wish-copy">Start with a title, then add the purchase details that matter.</p>')
        with st.form("wishlist_add_form", clear_on_submit=True):
            title_column, author_column, category_column = st.columns(3)
            book_name = title_column.text_input("Book title *", placeholder="e.g. Deep Work")
            author = author_column.text_input("Author")
            category = category_column.text_input("Category")
            price_column, priority_column, date_column = st.columns(3)
            expected_price = price_column.number_input("Expected price", min_value=0.0, value=0.0, step=1.0)
            priority = priority_column.selectbox("Priority", WISHLIST_PRIORITIES)
            expected_purchase_date = date_column.date_input("Target purchase date", value=None)
            notes = st.text_area("Notes", placeholder="Edition, store, or reason to buy", height=80)
            submitted = st.form_submit_button("Add to wishlist", type="primary", icon=":material/add:")
        if submitted:
            try:
                service.create_item({"book_name": book_name, "author": author, "category": category, "expected_price": Decimal(str(expected_price)), "priority": priority, "expected_purchase_date": expected_purchase_date, "notes": notes, "status": "Planned"})
            except ValueError as error:
                st.error(str(error))
            else:
                st.toast("Added to your wishlist.", icon=":material/favorite:")
                st.rerun()


def _filters(items: list) -> list:
    with st.expander("Filters and sorting", icon=":material/tune:"):
        query_column, category_column, priority_column, status_column = st.columns(4)
        query = query_column.text_input("Search wishlist", placeholder="Title or author")
        categories = category_column.multiselect("Category", sorted({item.category or "Uncategorised" for item in items}))
        priorities = priority_column.multiselect("Priority", WISHLIST_PRIORITIES)
        statuses = status_column.multiselect("Status", WISHLIST_STATUSES)
        sort = st.segmented_control("Sort by", ["Recently added", "Price", "Priority", "Purchase date"], default="Recently added") or "Recently added"
    filtered = [item for item in items if (not query or query.casefold() in item.book_name.casefold() or query.casefold() in (item.author or "").casefold()) and (not categories or (item.category or "Uncategorised") in categories) and (not priorities or item.priority in priorities) and (not statuses or item.status in statuses)]
    if sort == "Price":
        return sorted(filtered, key=lambda item: item.expected_price or Decimal("0"))
    if sort == "Priority":
        return sorted(filtered, key=lambda item: {"High": 0, "Medium": 1, "Low": 2}[item.priority])
    if sort == "Purchase date":
        return sorted(filtered, key=lambda item: item.expected_purchase_date or date.max)
    return filtered


def _convert_to_book(service: WishlistService, item: object) -> None:
    if not item.author:
        st.warning("Add an author before converting this item to a book.")
        return
    try:
        book = service.mark_purchased(item.id, {"book_name": item.book_name, "author": item.author, "category": item.category, "price": item.expected_price or Decimal("0"), "purchase_date": item.expected_purchase_date, "publisher": "", "isbn": "", "language": "", "rating": None, "reading_status": "Unread", "personal_review": "", "notes": item.notes or "", "is_favourite": False, "library_id": st.session_state.get("selected_library_id")})
    except ValueError as error:
        st.error(str(error))
    else:
        st.success(f"Added '{book.book_name}' to the active library.")
        st.rerun()


def _card(service: WishlistService, item: object) -> None:
    st.html('<div class="wish-cover">WISH</div>')
    st.html(f'<p class="wish-card-title">{escape(item.book_name)}</p><p class="wish-meta">{escape(item.author or "Author not set")}</p><span class="wish-priority {_priority_class(item.priority)}">{escape(item.priority)} priority</span>')
    st.caption(f"{item.category or 'Uncategorised'} · {format_inr(item.expected_price or 0)}")
    st.caption(f"{item.status} · {item.expected_purchase_date.strftime('%d %b %Y') if item.expected_purchase_date else 'No target date'}")
    first, second = st.columns(2)
    if item.status == "Planned" and first.button("Mark ordered", icon=":material/local_shipping:", key=f"order_{item.id}", width="stretch"):
        service.update_item(item.id, {"book_name": item.book_name, "author": item.author, "category": item.category, "expected_price": item.expected_price, "priority": item.priority, "expected_purchase_date": item.expected_purchase_date, "notes": item.notes, "status": "Ordered"})
        st.rerun()
    if item.status != "Purchased" and second.button("Add to library", icon=":material/library_add:", key=f"purchase_{item.id}", width="stretch"):
        _convert_to_book(service, item)
    if st.button("Delete", icon=":material/delete:", key=f"delete_wishlist_{item.id}", width="stretch"):
        service.delete_item(item.id)
        st.toast("Wishlist item deleted.", icon=":material/delete:")
        st.rerun()


def render(session: Session) -> None:
    """Render a visual wishlist and purchase tracking workspace."""
    render_page_header("Wishlist", "Plan the books you want to own, prioritise your next purchase, and add them to your library.", "W")
    _styles()
    service = WishlistService(session)
    items = service.list_items()
    _overview(items)
    _quick_add(service)
    if not items:
        st.info("Your wishlist is ready for its first book. Add a title to start planning your next purchase.", icon=":material/favorite:")
        return
    pending = [item for item in items if item.status in {"Planned", "Ordered"}]
    if pending:
        recommendation = min(pending, key=lambda item: ({"High": 0, "Medium": 1, "Low": 2}[item.priority], item.expected_price or Decimal("0")))
        with st.container(border=True):
            st.html('<p class="wish-title">Recommended next purchase</p><p class="wish-copy">High priority and lowest estimated cost among your pending books.</p>')
            st.write(f"**{recommendation.book_name}** by {recommendation.author or 'Unknown author'} · {format_inr(recommendation.expected_price or 0)}")
    filtered = _filters(items)
    st.html('<p class="wish-title">Your wishlist</p><p class="wish-copy">Review purchase plans and move a book into your active library when it arrives.</p>')
    if not filtered:
        st.info("No wishlist books match these filters.", icon=":material/search_off:")
        return
    for offset in range(0, len(filtered), 4):
        for column, item in zip(st.columns(4), filtered[offset:offset + 4]):
            with column.container(border=True):
                _card(service, item)
    frame = ExportService.wishlist_frame(filtered)
    csv, excel = st.columns(2)
    csv.download_button("Export wishlist CSV", ExportService.to_csv(frame), "wishlist.csv", "text/csv", icon=":material/download:", width="stretch")
    if ExportService.excel_available():
        excel.download_button("Export wishlist Excel", ExportService.to_excel({"Wishlist": frame}), "wishlist.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/table_view:", width="stretch")
