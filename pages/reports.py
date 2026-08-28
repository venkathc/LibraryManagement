"""Phase 2 catalogue reports and downloads."""

import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from services.export_service import ExportService
from services.report_service import ReportService


def render(session: Session) -> None:
    """Render author, category, price, and reading reports with exports."""
    st.header("Reports")
    service = ReportService(session)
    export_service = ExportService()
    books = service.books_frame()
    if books.empty:
        st.info("Add books before generating reports.")
        return
    author_tab, category_tab, price_tab, reading_tab, export_tab = st.tabs(
        ["Author", "Category", "Price", "Reading", "Export"]
    )
    with author_tab:
        report = service.author_report()
        st.dataframe(report, hide_index=True, use_container_width=True)
        st.plotly_chart(px.bar(report, x="Author", y="Books", title="Books by author"), use_container_width=True)
    with category_tab:
        report = service.category_report()
        st.dataframe(report, hide_index=True, use_container_width=True)
        st.plotly_chart(px.bar(report, x="Category", y="Investment", title="Investment by category"), use_container_width=True)
    with price_tab:
        columns = st.columns(3)
        columns[0].metric("Total investment", f"₹{books['Price'].sum():,.2f}")
        columns[1].metric("Average price", f"₹{books['Price'].mean():,.2f}")
        columns[2].metric("Median price", f"₹{books['Price'].median():,.2f}")
        st.plotly_chart(px.histogram(books, x="Price", title="Price distribution"), use_container_width=True)
    with reading_tab:
        reading = books.groupby("Reading Status").size().reset_index(name="Books")
        st.metric("Reading completion", f"{(books['Reading Status'] == 'Read').mean() * 100:.1f}%")
        st.plotly_chart(px.pie(reading, names="Reading Status", values="Books", title="Reading status"), use_container_width=True)
    with export_tab:
        st.download_button("Download books CSV", export_service.to_csv(books), "books.csv", "text/csv")
        if export_service.excel_available():
            st.download_button(
                "Download books Excel",
                export_service.to_excel({"Books": books, "Author Report": service.author_report(), "Category Report": service.category_report()}),
                "library_reports.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning("Excel export requires openpyxl. Install dependencies with `.venv/bin/python -m pip install -r requirements.txt`.")
