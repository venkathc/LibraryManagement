"""Basic Phase 1 dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.loan_service import LoanService
from utils.formatters import format_inr


def render(session: Session) -> None:
    """Render essential catalogue metrics and recent books."""
    st.header("Dashboard")
    service = BookService(session)
    metrics = service.metrics()
    loan_metrics = LoanService(session).metrics()
    st.html(
        """
        <style>
        .st-key-dashboard-metrics-table [data-testid="stHorizontalBlock"] {
            gap: 0;
        }
        .st-key-dashboard-metrics-table [data-testid="stMetric"] {
            border-bottom: 1px solid #d1d5db;
            border-right: 1px solid #d1d5db;
            box-sizing: border-box;
            min-height: 5.8rem;
            padding: 0.7rem;
        }
        .st-key-dashboard-metrics-table > [data-testid="stLayoutWrapper"]:first-child [data-testid="stMetric"] {
            background: #ecfdf5;
            border-top: 1px solid #d1d5db;
        }
        .st-key-dashboard-metrics-table > [data-testid="stLayoutWrapper"]:nth-child(2) [data-testid="stMetric"] {
            background: #fffbeb;
        }
        .st-key-dashboard-metrics-table [data-testid="stColumn"]:first-child [data-testid="stMetric"] {
            border-left: 1px solid #d1d5db;
        }
        </style>
        """
    )
    with st.container(key="dashboard-metrics-table"):
        columns = st.columns(4, gap=None)
        columns[0].metric("Total books", metrics["total_books"])
        columns[1].metric("Invested", format_inr(metrics["total_investment"]))
        columns[2].metric("Unique authors", metrics["unique_authors"])
        columns[3].metric("Unique categories", metrics["unique_categories"])

        loan_columns = st.columns(3, gap=None)
        loan_columns[0].metric("Books lent", loan_metrics["active"])
        loan_columns[1].metric("Overdue loans", loan_metrics["overdue"])
        loan_columns[2].metric("Due within 7 days", loan_metrics["due_soon"])

    books = service.search_books()
    if not books:
        st.info("Your library is empty. Add a book to start tracking your collection.")
        return
    st.subheader("Latest books")
    st.dataframe(
        pd.DataFrame([{"Title": book.book_name, "Author": book.author, "Price": format_inr(book.price)} for book in books[:5]]),
        use_container_width=True,
        hide_index=True,
    )
    categories = [book.category or "Uncategorised" for book in books]
    chart_data = pd.DataFrame({"Category": categories}).value_counts().reset_index(name="Books")
    st.plotly_chart(px.bar(chart_data, x="Category", y="Books", title="Books by category"), use_container_width=True)
    status_data = pd.DataFrame({"Status": [book.reading_status for book in books]}).value_counts().reset_index(name="Books")
    st.plotly_chart(px.pie(status_data, names="Status", values="Books", title="Reading status"), use_container_width=True)
