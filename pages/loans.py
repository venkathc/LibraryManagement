"""Circulation workspace for lending, returns, and borrower activity."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.export_service import ExportService
from services.image_service import ImageService
from services.loan_service import LoanService
from services.reminder_service import ReminderService
from utils.page_ui import render_page_header


def _styles() -> None:
    st.html("""<style>
    .loan-heading{color:#123c55;font:700 1rem/1.25 'Poppins',sans-serif;margin:0}.loan-copy{color:#55717b;font:.78rem/1.45 'Poppins',sans-serif;margin:.18rem 0 .8rem}.loan-cover{align-items:center;background:linear-gradient(145deg,#146c72,#123c55);border-radius:6px;color:#f7d574;display:flex;font:700 1rem 'Poppins',sans-serif;height:130px;justify-content:center}.loan-name{color:#123c55;font:700 .9rem/1.3 'Poppins',sans-serif;margin:.55rem 0 .1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.loan-meta{color:#55717b;font:.72rem/1.4 'Poppins',sans-serif;margin:0}.borrower-avatar{align-items:center;background:#d8f1ed;border-radius:50%;color:#146c72;display:flex;font:700 .8rem 'Poppins',sans-serif;height:34px;justify-content:center;width:34px}.loan-alert{border-left:4px solid #d05b36;padding-left:.75rem}[data-testid='stMainBlockContainer'] [data-testid='stMetric']{background:#fff;border-radius:8px}[data-testid='stMainBlockContainer'] [data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(135deg,rgba(247,252,251,.96),#fff);box-shadow:0 6px 18px rgba(18,60,85,.05)}</style>""")


def _status(loan) -> tuple[str, str, str]:
    if loan.actual_return_date:
        return "Returned", "green", "Returned"
    if loan.expected_return_date and loan.expected_return_date < date.today():
        return "Overdue", "red", f"{(date.today() - loan.expected_return_date).days} day(s) overdue"
    if loan.expected_return_date and loan.expected_return_date <= date.today() + timedelta(days=7):
        return "Due soon", "orange", f"{(loan.expected_return_date - date.today()).days} day(s) remaining"
    return "On time", "blue", "No due date" if not loan.expected_return_date else f"{(loan.expected_return_date - date.today()).days} day(s) remaining"


def _loan_frame(loans: list) -> pd.DataFrame:
    return pd.DataFrame([{"Loan ID": loan.id, "Book": loan.book.book_name, "Author": loan.book.author, "Borrower": loan.borrower_name, "Contact": loan.borrower_contact, "Borrowed date": loan.borrowed_date, "Expected return": loan.expected_return_date, "Returned date": loan.actual_return_date, "Status": _status(loan)[0], "Notes": loan.notes} for loan in loans])


def _overview(loans: list) -> None:
    today = date.today()
    active = [loan for loan in loans if loan.actual_return_date is None]
    returned_month = [loan for loan in loans if loan.actual_return_date and loan.actual_return_date.month == today.month and loan.actual_return_date.year == today.year]
    borrowers = {loan.borrower_name.casefold() for loan in active}
    yearly = [loan for loan in loans if loan.borrowed_date.year == today.year]
    cards = ((":material/import_contacts: Books currently lent", len(active), "Out with readers", "normal"), (":material/warning: Overdue books", sum(_status(loan)[0] == "Overdue" for loan in active), "Needs attention", "inverse"), (":material/assignment_return: Returned this month", len(returned_month), None, "normal"), (":material/group: Active borrowers", len(borrowers), None, "normal"), (":material/timeline: Total loans this year", len(yearly), None, "normal"))
    for column, (label, value, detail, color) in zip(st.columns(5), cards):
        column.metric(label, value, detail, delta_color=color, border=True)


def _cover(book) -> None:
    path = ImageService.resolve_cover(book.cover_image_path)
    if path:
        st.image(str(path), width="stretch")
    else:
        st.html('<div class="loan-cover">BOOK</div>')


def _lend_form(service: LoanService, books: list, active_book_ids: set[int]) -> None:
    available = [book for book in books if book.id not in active_book_ids]
    with st.container(border=True):
        st.html('<p class="loan-heading">Quick lend a book</p><p class="loan-copy">Select an available book and record the borrower details in one step.</p>')
        if not available:
            st.info("Every book in this library is currently lent out.", icon=":material/import_contacts:")
            return
        query = st.text_input(
            "Find an available book",
            placeholder="Search by title, author, ISBN, or category",
            key="loan_book_search",
            icon=":material/search:",
        ).strip()
        if query:
            query_folded = query.casefold()
            candidates = [
                book for book in available
                if query_folded in " ".join(
                    filter(None, (book.book_name, book.author, book.isbn, book.category))
                ).casefold()
            ]
        else:
            candidates = available[:12]
            st.caption(f"Showing 12 of {len(available)} available books. Search to narrow the list.")
        if not candidates:
            st.info("No available books match that search.", icon=":material/search_off:")
            return
        choices = {f"{book.book_name} · {book.author} · #{book.id}": book for book in candidates}
        selected_label = st.selectbox("Available book", choices, key="loan_book")
        book = choices[selected_label]
        preview, fields = st.columns((1, 3))
        with preview:
            _cover(book)
        with fields:
            st.write(f"**{book.book_name}**  \n{book.author} · {book.category or 'Uncategorised'}")
            st.badge("Available", icon=":material/check_circle:", color="green")
            with st.form("lend_book_form", clear_on_submit=True):
                borrower, contact, relationship = st.columns(3)
                borrower_name = borrower.text_input("Borrower name *")
                phone = contact.text_input("Phone number")
                email = relationship.text_input("Email address")
                dates = st.columns(2)
                borrowed_date = dates[0].date_input("Borrowed date", value=date.today())
                expected_return_date = dates[1].date_input("Expected return date", value=date.today() + timedelta(days=14))
                relation = st.selectbox("Relationship", ["Friend", "Family", "Student", "Colleague", "Other"])
                notes = st.text_area("Loan notes", placeholder="Optional condition or lending notes", height=65)
                record, clear = st.columns(2)
                submitted = record.form_submit_button("Record loan", type="primary", icon=":material/add_circle:", width="stretch")
                cleared = clear.form_submit_button("Clear", icon=":material/refresh:", width="stretch")
            if cleared:
                st.rerun()
            if submitted:
                contact_value = " | ".join(value for value in (phone.strip(), email.strip()) if value)
                note_value = f"Relationship: {relation}" + (f"\n{notes.strip()}" if notes.strip() else "")
                try:
                    service.lend_book({"book_id": book.id, "borrower_name": borrower_name, "borrower_contact": contact_value, "borrowed_date": borrowed_date, "expected_return_date": expected_return_date, "notes": note_value})
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.toast(f"Loan recorded for {borrower_name}.", icon=":material/check_circle:")
                    st.rerun()


@st.dialog("Loan details", width="large")
def _details(loan) -> None:
    cover, content = st.columns((1, 2))
    with cover:
        _cover(loan.book)
    with content:
        status, color, days = _status(loan)
        st.subheader(loan.book.book_name)
        st.caption(f"{loan.book.author} · {loan.book.category or 'Uncategorised'}")
        st.badge(status, color=color)
        st.write(f"**Borrower:** {loan.borrower_name}  \n**Contact:** {loan.borrower_contact or 'Not recorded'}  \n**Borrowed:** {loan.borrowed_date.strftime('%d %b %Y')}  \n**Expected return:** {loan.expected_return_date.strftime('%d %b %Y') if loan.expected_return_date else 'Not set'}  \n**Status:** {days}")
    st.write(loan.notes or "No loan notes.")
    st.markdown("**Extension history**")
    if loan.extensions:
        st.dataframe(pd.DataFrame([{"Previous due date": item.previous_return_date, "New due date": item.extended_return_date, "Changed": item.created_at} for item in loan.extensions]), hide_index=True, width="stretch")
    else:
        st.caption("This loan has not been extended.")


def _reminder(loan, key_suffix: str) -> None:
    status, _, days = _status(loan)
    due = loan.expected_return_date.strftime("%d %b %Y") if loan.expected_return_date else "soon"
    message = f"Hi {loan.borrower_name}, friendly reminder that '{loan.book.book_name}' is {status.lower()} for return {due}. {days}."
    with st.popover("Reminder", icon=":material/notifications:", key=f"reminder_{key_suffix}_{loan.id}"):
        st.caption("SMS / email / WhatsApp template")
        st.code(message, language=None)
        sender = ReminderService()
        recipient = sender.email_from_contact(loan.borrower_contact)
        if not recipient:
            st.caption("Add an email address to this borrower's contact when recording a loan to send email reminders.")
        elif not sender.configured:
            st.caption("Gmail is not configured yet. Add the sender address and app password to .env.")
        elif st.button("Send email", type="primary", icon=":material/send:", key=f"send_email_{key_suffix}_{loan.id}", width="stretch"):
            try:
                sender.send_email(recipient, f"Library return reminder: {loan.book.book_name}", message)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"Reminder sent to {recipient}.")


def _extend(service: LoanService, loan, key_suffix: str) -> None:
    base = loan.expected_return_date or date.today()
    with st.popover("Extend", icon=":material/event_repeat:", key=f"extend_{key_suffix}_{loan.id}"):
        option = st.segmented_control("Extension", ["+7 days", "+15 days", "+30 days", "Custom"], default="+7 days", key=f"extension_option_{key_suffix}_{loan.id}")
        offsets = {"+7 days": 7, "+15 days": 15, "+30 days": 30}
        new_date = st.date_input("New return date", value=base + timedelta(days=offsets.get(option, 7)), key=f"extension_date_{key_suffix}_{loan.id}")
        if st.button("Confirm extension", type="primary", key=f"confirm_extension_{key_suffix}_{loan.id}", width="stretch"):
            try:
                service.extend_loan(loan.id, new_date)
            except ValueError as error:
                st.error(str(error))
            else:
                st.toast("Return date extended.", icon=":material/event_available:")
                st.rerun()


def _loan_card(service: LoanService, loan, section: str) -> None:
    _cover(loan.book)
    status, color, days = _status(loan)
    st.html(f'<p class="loan-name">{escape(loan.book.book_name)}</p><p class="loan-meta">{escape(loan.book.author)}</p>')
    st.caption(f"Borrowed by {loan.borrower_name}")
    st.caption(f"Due {loan.expected_return_date.strftime('%d %b %Y') if loan.expected_return_date else 'not set'} · {days}")
    st.badge(status, color=color)
    view, extend, returned = st.columns(3)
    if view.button("View", icon=":material/visibility:", key=f"loan_view_{section}_{loan.id}", width="stretch"):
        _details(loan)
    if loan.actual_return_date is None:
        with extend:
            _extend(service, loan, section)
        if returned.button("Return", icon=":material/assignment_return:", key=f"loan_return_{section}_{loan.id}", width="stretch"):
            service.mark_returned(loan.id, date.today())
            st.toast("Book marked as returned.", icon=":material/check_circle:")
            st.rerun()


def _borrowers(loans: list) -> None:
    st.html('<p class="loan-heading">Borrower directory</p><p class="loan-copy">Profiles are built from your lending history in this library.</p>')
    by_borrower: dict[str, list] = {}
    for loan in loans:
        by_borrower.setdefault(loan.borrower_name, []).append(loan)
    for offset in range(0, len(by_borrower), 3):
        for column, (name, history) in zip(st.columns(3), list(by_borrower.items())[offset:offset + 3]):
            active = [loan for loan in history if loan.actual_return_date is None]
            returned = [loan for loan in history if loan.actual_return_date]
            with column.container(border=True):
                initials = "".join(part[0] for part in name.split()[:2]).upper()
                st.html(f'<div class="borrower-avatar">{escape(initials)}</div>')
                st.markdown(f"**{name}**")
                st.caption(history[-1].borrower_contact or "Contact not recorded")
                st.caption(f"Currently borrowing: {len(active)} · Total loans: {len(history)} · Return rate: {len(returned) / len(history) * 100:.0f}%")
                with st.popover("View history", key=f"borrower_history_{name}"):
                    st.dataframe(_loan_frame(history), hide_index=True, width="stretch")
                if active:
                    _reminder(active[0], "borrower")


def _filtered_loans(loans: list) -> list:
    with st.expander("Search and filters", icon=":material/tune:"):
        book_query, borrower_query, state, sort = st.columns(4)
        book_text = book_query.text_input("Search book")
        borrower_text = borrower_query.text_input("Search borrower")
        selected_status = state.selectbox("Status", ["All", "Active", "Returned", "Overdue", "Due soon"])
        order = sort.selectbox("Sort by", ["Borrow date", "Return date", "Borrower", "Book name"])
    result = [loan for loan in loans if (not book_text or book_text.casefold() in loan.book.book_name.casefold()) and (not borrower_text or borrower_text.casefold() in loan.borrower_name.casefold())]
    if selected_status != "All":
        result = [loan for loan in result if (selected_status == "Active" and loan.actual_return_date is None) or _status(loan)[0] == selected_status]
    keys = {"Borrow date": lambda loan: loan.borrowed_date, "Return date": lambda loan: loan.actual_return_date or date.max, "Borrower": lambda loan: loan.borrower_name.casefold(), "Book name": lambda loan: loan.book.book_name.casefold()}
    return sorted(result, key=keys[order], reverse=order == "Borrow date")


def _analytics(loans: list) -> None:
    if not st.toggle("Show lending analytics", key="lending_analytics"):
        return
    st.html('<p class="loan-heading">Lending analytics</p><p class="loan-copy">Review the patterns behind your circulation activity.</p>')
    completed = [loan for loan in loans if loan.actual_return_date]
    average = sum((loan.actual_return_date - loan.borrowed_date).days for loan in completed) / len(completed) if completed else 0
    overdue = sum(_status(loan)[0] == "Overdue" for loan in loans)
    cards = st.columns(3)
    cards[0].metric("Average lending duration", f"{average:.0f} days", border=True)
    cards[1].metric("Overdue percentage", f"{overdue / len(loans) * 100:.0f}%" if loans else "0%", border=True)
    cards[2].metric("Most active borrower", Counter(loan.borrower_name for loan in loans).most_common(1)[0][0] if loans else "-", border=True)
    months = Counter(loan.borrowed_date.strftime("%b %Y") for loan in loans)
    popular = Counter(loan.book.book_name for loan in loans).most_common(6)
    left, right = st.columns(2)
    with left:
        st.bar_chart(pd.DataFrame(months.items(), columns=["Month", "Loans"]), x="Month", y="Loans")
    with right:
        st.bar_chart(pd.DataFrame(popular, columns=["Book", "Loans"]), x="Book", y="Loans")


def render(session: Session) -> None:
    """Render the active library's lending desk."""
    render_page_header("Lending desk", "Manage circulation, borrower activity, due dates, and returns for the active library.", "L")
    _styles()
    library_id = st.session_state.get("selected_library_id")
    service = LoanService(session)
    books = BookService(session).search_books(library_id=library_id)
    loans = service.list_loans(library_id)
    _overview(loans)
    _lend_form(service, books, {loan.book_id for loan in loans if loan.actual_return_date is None})
    if not loans:
        st.info("No loan history yet. Start by recording a loan above.", icon=":material/import_contacts:")
        return
    active = [loan for loan in loans if loan.actual_return_date is None]
    overdue = [loan for loan in active if _status(loan)[0] == "Overdue"]
    if overdue:
        st.html('<p class="loan-heading loan-alert">Overdue books</p><p class="loan-copy">Prioritise these returns and send a reminder when needed.</p>')
        for offset in range(0, len(overdue), 3):
            for column, loan in zip(st.columns(3), overdue[offset:offset + 3]):
                with column.container(border=True):
                    _loan_card(service, loan, "overdue")
                    _reminder(loan, "overdue")
    st.html('<p class="loan-heading">Active loans board</p><p class="loan-copy">Track every active loan, extend due dates, or record a return.</p>')
    filtered = _filtered_loans(loans)
    if not filtered:
        st.info("No loans match the selected filters.", icon=":material/search_off:")
    else:
        for offset in range(0, len(filtered), 3):
            for column, loan in zip(st.columns(3), filtered[offset:offset + 3]):
                with column.container(border=True):
                    _loan_card(service, loan, "board")
    _borrowers(loans)
    with st.container(border=True):
        st.html('<p class="loan-heading">Quick return</p><p class="loan-copy">Find an active loan by book, borrower, or loan ID and mark it returned.</p>')
        choices = {f"#{loan.id} · {loan.book.book_name} · {loan.borrower_name}": loan for loan in active}
        if choices:
            selected = st.selectbox("Active loan", choices, key="quick_return_loan")
            if st.button("Mark returned", type="primary", icon=":material/assignment_return:", key="quick_return"):
                service.mark_returned(choices[selected].id, date.today())
                st.toast("Book marked as returned.", icon=":material/check_circle:")
                st.rerun()
        else:
            st.caption("There are no active loans to return.")
    frame = _loan_frame(loans)
    csv, excel = st.columns(2)
    csv.download_button("Export loan CSV", ExportService.to_csv(frame), "loan_history.csv", "text/csv", icon=":material/download:", width="stretch")
    if ExportService.excel_available():
        excel.download_button("Export loan Excel", ExportService.to_excel({"Loans": frame}), "loan_history.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/table_view:", width="stretch")
    _analytics(loans)
