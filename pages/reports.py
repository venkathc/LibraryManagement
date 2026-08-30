"""Filterable library insights and analytics workspace."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from services.export_service import ExportService
from services.report_service import ReportService
from utils.page_ui import render_page_header


CHART_LAYOUT = {"height": 325, "margin": {"l": 18, "r": 18, "t": 46, "b": 18}, "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)", "font": {"family": "Poppins, sans-serif"}}
CHART_COLORS = ["#1c8a83", "#2d6f9e", "#f0a85b", "#79b6b0", "#d05b36", "#b18a38"]


def _period_frame(frame: pd.DataFrame, date_column: str, value_column: str | None = None) -> pd.DataFrame:
    """Group data into chronologically sorted monthly periods."""
    dated = frame.dropna(subset=[date_column]).copy()
    result_column = "Books" if value_column is None else value_column
    if dated.empty:
        return pd.DataFrame(columns=["Period", result_column])
    dated["Period"] = pd.to_datetime(dated[date_column]).dt.to_period("M").dt.to_timestamp()
    if value_column is None:
        return dated.groupby("Period").size().reset_index(name="Books")
    return dated.groupby("Period", as_index=False)[value_column].sum()


def _values(frame: pd.DataFrame, column: str) -> list[str]:
    values = frame[column].fillna("").str.split(", ").explode()
    return sorted({value.strip() for value in values if value.strip()}, key=str.casefold)


def _filters(books: pd.DataFrame, loans: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply advanced report filters to the owned books and loan history."""
    books = books.copy()
    books["Activity Date"] = pd.to_datetime(books["Purchase Date"]).fillna(pd.to_datetime(books["Added At"]))
    dates = books["Activity Date"].dropna()
    first_date = dates.min().date() if not dates.empty else date.today()
    last_date = dates.max().date() if not dates.empty else date.today()
    with st.expander("Advanced filters", icon=":material/tune:"):
        row = st.columns(3)
        selected_dates = row[0].date_input("Date range", value=(first_date, last_date), key="report_date_range")
        categories = row[1].multiselect("Categories", sorted(books["Category"].unique()), key="report_categories")
        authors = row[2].multiselect("Authors", sorted(books["Author"].unique(), key=str.casefold), key="report_authors")
        row = st.columns(4)
        minimum = row[0].number_input("Minimum price", min_value=0.0, value=float(books["Price"].min()), key="report_minimum_price")
        maximum = row[1].number_input("Maximum price", min_value=0.0, value=float(books["Price"].max()), key="report_maximum_price")
        tags = row[2].multiselect("Tags", _values(books, "Tags"), key="report_tags")
        collections = row[3].multiselect("Library / collection", _values(books, "Collections"), key="report_collections")
        borrowers = st.multiselect("Borrowers", sorted(loans["Borrower"].unique(), key=str.casefold) if not loans.empty else [], key="report_borrowers")
    if len(selected_dates) == 2:
        books = books[books["Activity Date"].between(pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1]))]
    if categories:
        books = books[books["Category"].isin(categories)]
    if authors:
        books = books[books["Author"].isin(authors)]
    books = books.iloc[0:0] if minimum > maximum else books[books["Price"].between(minimum, maximum)]
    for tag in tags:
        books = books[books["Tags"].str.contains(tag, case=False, regex=False, na=False)]
    for collection in collections:
        books = books[books["Collections"].str.contains(collection, case=False, regex=False, na=False)]
    if borrowers:
        loans = loans[loans["Borrower"].isin(borrowers)]
        books = books[books["ID"].isin(loans["Book ID"])]
    elif not loans.empty:
        loans = loans[loans["Book ID"].isin(books["ID"])]
    return books, loans


def _metrics(books: pd.DataFrame, loans: pd.DataFrame) -> None:
    active = loans[loans["Returned Date"].isna()] if not loans.empty else loans
    returned = loans[loans["Returned Date"].notna()] if not loans.empty else loans
    overdue = loans[loans["Status"] == "Overdue"] if not loans.empty else loans
    favourites = books[books["Favourite"]]
    category_source = favourites if not favourites.empty else books
    favourite_category = category_source["Category"].mode().iat[0]
    cards = (
        (":material/menu_book: Total books", len(books)), (":material/payments: Total investment", f"₹{books['Price'].sum():,.2f}"),
        (":material/edit: Total authors", books["Author"].nunique()), (":material/sell: Categories", books["Category"].nunique()),
        (":material/import_contacts: Books lent", len(active)), (":material/assignment_turned_in: Returned books", len(returned)),
        (":material/warning: Overdue books", len(overdue)), (":material/favorite: Favourite category", favourite_category),
    )
    for group in (cards[:4], cards[4:]):
        columns = st.columns(4)
        for column, (label, value) in zip(columns, group):
            column.metric(label, value, border=True)


def _overview(books: pd.DataFrame) -> None:
    monthly = _period_frame(books, "Activity Date", "Price")
    categories = books.groupby("Category", as_index=False)["Price"].sum().sort_values("Price", ascending=False)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.line(monthly, x="Period", y="Price", markers=True, title="Spending trend", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.pie(categories, names="Category", values="Price", title="Investment by category", hole=0.5, color_discrete_sequence=CHART_COLORS).update_layout(**CHART_LAYOUT), width="stretch")


def _financials(books: pd.DataFrame) -> None:
    high, low = books.loc[books["Price"].idxmax()], books.loc[books["Price"].idxmin()]
    cards = st.columns(4)
    for column, label, value, detail in zip(cards, ("Average book price", "Most expensive", "Cheapest", "Collection value"), (f"₹{books['Price'].mean():,.2f}", f"₹{high['Price']:,.2f}", f"₹{low['Price']:,.2f}", f"₹{books['Price'].sum():,.2f}"), (None, high["Book Name"], low["Book Name"], None)):
        column.metric(label, value, detail, border=True)
    monthly = _period_frame(books, "Activity Date", "Price")
    categories = books.groupby("Category", as_index=False)["Price"].sum()
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(monthly, x="Period", y="Price", title="Monthly spending", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.pie(categories, names="Category", values="Price", title="Spending by category", hole=0.5, color_discrete_sequence=CHART_COLORS).update_layout(**CHART_LAYOUT), width="stretch")


def _growth(books: pd.DataFrame) -> None:
    monthly = _period_frame(books, "Added At")
    yearly = books.assign(Year=pd.to_datetime(books["Added At"]).dt.year).groupby("Year", as_index=False).size().rename(columns={"size": "Books"})
    author_growth = books.assign(Period=pd.to_datetime(books["Added At"]).dt.to_period("M").dt.to_timestamp()).groupby("Period")["Author"].nunique().reset_index(name="Authors")
    category_growth = books.assign(Period=pd.to_datetime(books["Added At"]).dt.to_period("M").dt.to_timestamp()).groupby("Period")["Category"].nunique().reset_index(name="Categories")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.line(monthly, x="Period", y="Books", markers=True, title="Library growth trend", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch")
        st.plotly_chart(px.bar(yearly, x="Year", y="Books", title="Books added per year", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.line(author_growth, x="Period", y="Authors", markers=True, title="Author growth trend", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")
        st.plotly_chart(px.line(category_growth, x="Period", y="Categories", markers=True, title="Category expansion trend", color_discrete_sequence=["#d05b36"]).update_layout(**CHART_LAYOUT), width="stretch")


def _authors_categories(books: pd.DataFrame) -> None:
    authors = books.groupby("Author", as_index=False).agg(Books=("Book Name", "count"), Investment=("Price", "sum")).sort_values("Books", ascending=False)
    categories = books.groupby("Category", as_index=False).agg(Books=("Book Name", "count"), Investment=("Price", "sum")).sort_values("Books", ascending=False)
    left, right = st.columns(2)
    with left:
        st.markdown("**Top authors**")
        st.plotly_chart(px.bar(authors.head(10).sort_values("Books"), x="Books", y="Author", orientation="h", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch")
        st.dataframe(authors.head(10), hide_index=True, width="stretch", column_config={"Investment": st.column_config.NumberColumn(format="₹%.2f")})
    with right:
        st.markdown("**Category ranking**")
        st.plotly_chart(px.pie(categories, names="Category", values="Books", hole=0.5, color_discrete_sequence=CHART_COLORS).update_layout(**CHART_LAYOUT), width="stretch")
        st.dataframe(categories, hide_index=True, width="stretch", column_config={"Investment": st.column_config.NumberColumn(format="₹%.2f")})


def _lending(loans: pd.DataFrame) -> None:
    if loans.empty:
        st.info("No loan history matches these filters.", icon=":material/import_contacts:")
        return
    returned = loans[loans["Returned Date"].notna()].copy()
    duration = (pd.to_datetime(returned["Returned Date"]) - pd.to_datetime(returned["Borrowed Date"])).dt.days.mean() if not returned.empty else 0
    cards = st.columns(4)
    for column, label, value in zip(cards, ("Total loans", "Currently lent", "Overdue", "Average loan duration"), (len(loans), int(loans["Returned Date"].isna().sum()), int((loans["Status"] == "Overdue").sum()), f"{duration:.0f} days")):
        column.metric(label, value, border=True)
    borrowers = loans.groupby("Borrower", as_index=False).size().rename(columns={"size": "Loans"}).sort_values("Loans", ascending=False)
    statuses = loans.groupby("Status", as_index=False).size().rename(columns={"size": "Loans"})
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(borrowers.head(10), x="Loans", y="Borrower", orientation="h", title="Frequent borrowers", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.pie(statuses, names="Status", values="Loans", title="Loan status", hole=0.5, color_discrete_sequence=CHART_COLORS).update_layout(**CHART_LAYOUT), width="stretch")


def _intelligence(books: pd.DataFrame) -> None:
    categories, authors = books["Category"].value_counts(), books["Author"].value_counts()
    this_month = int((books["Activity Date"].dt.to_period("M") == pd.Timestamp.today().to_period("M")).sum())
    insights = (("Largest collection category", categories.index[0], f"{categories.iloc[0]} books"), ("Total collection value", f"₹{books['Price'].sum():,.2f}", "Current selection"), ("Books added this month", this_month, "Purchased or catalogued"), ("Most purchased author", authors.index[0], f"{authors.iloc[0]} books"), ("Average book cost", f"₹{books['Price'].mean():,.2f}", "Current selection"), ("Collection growth score", f"{books['Category'].nunique() / len(books) * 100:.0f}%", "Category diversification"))
    for group in (insights[:3], insights[3:]):
        columns = st.columns(3)
        for column, (label, value, detail) in zip(columns, group):
            column.metric(label, value, detail, border=True)
    st.markdown("**Top 10 valuable books**")
    st.dataframe(books.nlargest(10, "Price")[["Book Name", "Author", "Category", "Price"]], hide_index=True, width="stretch", column_config={"Price": st.column_config.NumberColumn(format="₹%.2f")})


def _journey(books: pd.DataFrame) -> None:
    timeline = books.sort_values("Activity Date")
    first, latest = timeline.iloc[0], timeline.iloc[-1]
    yearly = timeline.assign(Year=timeline["Activity Date"].dt.year).groupby("Year", as_index=False).size().rename(columns={"size": "Books"})
    discoveries = timeline.groupby(timeline["Activity Date"].dt.to_period("M").dt.to_timestamp())["Author"].nunique().reset_index(name="Authors discovered").rename(columns={"Activity Date": "Period"})
    cards = st.columns(3)
    cards[0].metric("First book", first["Book Name"], str(first["Activity Date"].date()), border=True)
    cards[1].metric("Latest book", latest["Book Name"], str(latest["Activity Date"].date()), border=True)
    cards[2].metric("Category diversification", f"{books['Category'].nunique() / len(books) * 100:.0f}%", f"{books['Category'].nunique()} categories", border=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.area(yearly, x="Year", y="Books", title="Collection growth timeline", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.line(discoveries, x="Period", y="Authors discovered", markers=True, title="Author discovery timeline", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")


def _exports(books: pd.DataFrame, loans: pd.DataFrame) -> None:
    exporter = ExportService()
    left, right = st.columns(2)
    left.download_button("Export filtered report CSV", exporter.to_csv(books), "library_insights.csv", "text/csv", icon=":material/download:", width="stretch")
    if exporter.excel_available():
        right.download_button("Export filtered report Excel", exporter.to_excel({"Books": books, "Loans": loans}), "library_insights.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/table_view:", width="stretch")
    else:
        right.button("Export filtered report Excel", disabled=True, icon=":material/table_view:", width="stretch")
    st.caption("PDF, print, and native sharing require an optional platform-specific export module. Excel and CSV are available now.")


def render(session: Session) -> None:
    """Render the Library Insights and Analytics centre."""
    render_page_header("Library insights", "A clear view of your collection value, reading habits, growth, and lending activity.", "R")
    service = ReportService(session)
    books, loans = service.books_frame(), service.loans_frame()
    if books.empty:
        st.info("Add books before generating insights.", icon=":material/auto_stories:")
        return
    books, loans = _filters(books, loans)
    if books.empty:
        st.warning("No books match the selected report filters.", icon=":material/filter_alt_off:")
        return
    _metrics(books, loans)
    overview, financials, growth, analysis, lending, intelligence, journey, exports = st.tabs(["Overview", "Financials", "Collection growth", "Authors & categories", "Lending", "Library Intelligence", "Reading journey", "Export"])
    with overview:
        _overview(books)
    with financials:
        _financials(books)
    with growth:
        _growth(books)
    with analysis:
        _authors_categories(books)
    with lending:
        _lending(loans)
    with intelligence:
        _intelligence(books)
    with journey:
        _journey(books)
    with exports:
        _exports(books, loans)
