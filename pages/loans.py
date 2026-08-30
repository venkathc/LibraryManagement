"""Borrowed and lent book management page."""

from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.loan_service import LoanService
from utils.page_ui import render_page_header


def render(session: Session) -> None:
    """Render loan creation, return processing, and loan history."""
    render_page_header("Lending desk", "Record loans, monitor returns, and keep your books moving with confidence.", "L")
    service = LoanService(session)
    books = BookService(session).search_books()
    if not books:
        st.info("Add a book before creating a loan.")
        return
    with st.form("lend_book_form", clear_on_submit=True):
        choices = {f"{book.id}: {book.book_name} - {book.author}": book.id for book in books}
        selected_book = st.selectbox("Book to lend", choices)
        left, right = st.columns(2)
        with left:
            borrower_name = st.text_input("Borrower name *")
            borrower_contact = st.text_input("Borrower contact")
        with right:
            borrowed_date = st.date_input("Borrowed date", value=date.today())
            expected_return_date = st.date_input("Expected return date", value=None)
        notes = st.text_area("Loan notes")
        submitted = st.form_submit_button("Record loan", type="primary")
    if submitted:
        try:
            service.lend_book({"book_id": choices[selected_book], "borrower_name": borrower_name, "borrower_contact": borrower_contact, "borrowed_date": borrowed_date, "expected_return_date": expected_return_date, "notes": notes})
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("Loan recorded.")
            st.rerun()

    loans = service.list_loans()
    if not loans:
        st.info("No loan history yet.")
        return
    overdue_count = sum(loan.status == "Overdue" for loan in loans)
    if overdue_count:
        st.warning(f"{overdue_count} loan(s) are overdue.")
    st.dataframe(pd.DataFrame([{"Loan ID": loan.id, "Book": loan.book.book_name, "Borrower": loan.borrower_name, "Borrowed": loan.borrowed_date, "Expected return": loan.expected_return_date, "Returned": loan.actual_return_date, "Status": loan.status} for loan in loans]), hide_index=True, width="stretch")
    active_loans = {f"{loan.id}: {loan.book.book_name} - {loan.borrower_name}": loan.id for loan in loans if loan.actual_return_date is None}
    if active_loans:
        selected_loan = st.selectbox("Active loan to return", active_loans)
        return_date = st.date_input("Actual return date", value=date.today())
        if st.button("Mark as returned", type="primary"):
            try:
                service.mark_returned(active_loans[selected_loan], return_date)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Book marked as returned.")
                st.rerun()