"""Filterable library insights and analytics workspace."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from services.export_service import ExportService
from services.report_service import ReportService
from services.wishlist_service import WishlistService
from utils.page_ui import render_page_header


CHART_LAYOUT = {"height": 325, "margin": {"l": 18, "r": 18, "t": 46, "b": 18}, "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)", "font": {"family": "Poppins, sans-serif"}}
CHART_COLORS = ["#1c8a83", "#2d6f9e", "#f0a85b", "#79b6b0", "#d05b36", "#b18a38"]

REPORT_CATEGORIES = {
    "Book reports": ("All books", "Available books", "Borrowed books", "Lost books", "Damaged books", "Recently added books", "Books by category", "Books by author"),
    "Member reports": ("All members", "Active members", "Inactive members", "Top borrowers", "Members with overdue books"),
    "Loan reports": ("Current loans", "Loan history", "Due today", "Due this week", "Overdue loans", "Returned books"),
    "Analytics reports": ("Most borrowed books", "Popular categories", "Peak borrowing periods", "Library utilisation", "Growth statistics"),
    "Library reports": ("All libraries", "Library-wise book count", "Library-wise member list", "Library collection report", "Recently created libraries"),
    "Wishlist reports": ("Wishlist books", "Wishlist by category"),
    "Financial reports": ("All purchases", "Books purchased in date range", "Monthly purchase report", "Yearly purchase report", "Spending by category", "Spending by library"),
}

QUICK_REPORTS = (
    ("All books", ":material/menu_book:"),
    ("Currently loaned books", ":material/import_contacts:"),
    ("Wishlist books", ":material/favorite:"),
    ("All purchases", ":material/payments:"),
)


def _report_styles() -> None:
    """Add restrained, reports-specific visual hierarchy."""
    st.html(
        """
        <style>
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(135deg, rgba(247, 252, 251, 0.96), rgba(255, 255, 255, 0.98));
            box-shadow: 0 6px 18px rgba(18, 60, 85, 0.05);
        }
        [data-testid="stMainBlockContainer"] [data-testid="stMetric"] {
            background: #ffffff;
            border-radius: 8px;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stExpander"] {
            border: 1px solid rgba(28, 138, 131, 0.22);
            border-radius: 8px;
            overflow: hidden;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stSegmentedControl"] {
            background: rgba(28, 138, 131, 0.07);
            border-radius: 8px;
            padding: 3px;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stSegmentedControl"] button {
            border-radius: 6px;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stMetric"] label {
            color: #55717b;
            font-family: "Poppins", sans-serif;
            font-size: 0.76rem;
            font-weight: 600;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stMetricValue"] {
            color: #123c55;
            font-family: "Poppins", sans-serif;
        }
        .report-section-title {
            color: #123c55;
            font: 700 1rem/1.25 "Poppins", sans-serif;
            margin: 0;
        }
        .report-section-copy {
            color: #55717b;
            font: 400 0.78rem/1.45 "Poppins", sans-serif;
            margin: 0.2rem 0 0.8rem;
        }
        .report-result-title {
            color: #123c55;
            font: 700 1.15rem/1.25 "Poppins", sans-serif;
            margin: 0;
        }
        .report-result-meta {
            color: #55717b;
            font: 500 0.76rem/1.45 "Poppins", sans-serif;
            margin: 0.24rem 0 0;
        }
        </style>
        """
    )


def _change(current: int | float, previous: int | float) -> str | None:
    """Return a compact month-over-month trend label when comparison data exists."""
    if previous == 0:
        return None if current == 0 else "New this month"
    return f"{(current - previous) / previous * 100:+.0f}% vs last month"


def _report_overview(books: pd.DataFrame, loans: pd.DataFrame, libraries: pd.DataFrame, members: pd.DataFrame) -> None:
    """Render compact, data-backed reporting KPIs for the active scope."""
    today = pd.Timestamp(date.today())
    month_start = today.replace(day=1)
    prior_start = month_start - pd.DateOffset(months=1)
    prior_end = month_start - pd.Timedelta(days=1)
    active_loans = loans[loans["Returned Date"].isna()] if not loans.empty else loans
    overdue = loans[loans["Status"] == "Overdue"] if not loans.empty else loans
    borrowed_ids = set(active_loans["Book ID"]) if not active_loans.empty else set()
    added_at = pd.to_datetime(books["Added At"])
    added_month = int(added_at.ge(month_start).sum())
    added_prior = int(added_at.between(prior_start, prior_end).sum())
    borrowed_at = pd.to_datetime(loans["Borrowed Date"]) if not loans.empty else pd.Series(dtype="datetime64[ns]")
    borrowed_month = int(borrowed_at.ge(month_start).sum())
    borrowed_prior = int(borrowed_at.between(prior_start, prior_end).sum())
    available = int((~books["ID"].isin(borrowed_ids)).sum())
    borrow_rate = len(active_loans) / len(books) * 100 if len(books) else 0
    member_count = len(members) if not members.empty else 0
    cards = (
        ("Total books", len(books), _change(added_month, added_prior), ":material/menu_book:", "normal"),
        ("Total members", member_count, None, ":material/group:", "normal"),
        ("Total libraries", len(libraries), None, ":material/local_library:", "normal"),
        ("Active loans", len(active_loans), _change(borrowed_month, borrowed_prior), ":material/autorenew:", "normal"),
        ("Overdue books", len(overdue), None, ":material/warning:", "inverse"),
        ("Available books", available, None, ":material/check_circle:", "normal"),
        ("Added this month", added_month, _change(added_month, added_prior), ":material/trending_up:", "normal"),
        ("Borrow rate", f"{borrow_rate:.0f}%", _change(borrowed_month, borrowed_prior), ":material/query_stats:", "normal"),
    )
    for group in (cards[:4], cards[4:]):
        columns = st.columns(4)
        for column, (label, value, trend, icon, trend_color) in zip(columns, group):
            column.metric(f"{icon} {label}", value, trend, delta_color=trend_color, border=True)

def _insights(books: pd.DataFrame, loans: pd.DataFrame, users: pd.DataFrame) -> None:
    """Render optional collection and borrowing charts for the active scope."""
    st.html('<p class="report-section-title">Collection activity</p><p class="report-section-copy">Explore borrowing, collection mix, and growth across the current report scope.</p>')
    borrowing = _period_frame(loans, "Borrowed Date") if not loans.empty else pd.DataFrame(columns=["Period", "Books"])
    category_counts = books.groupby("Category", as_index=False).size().rename(columns={"size": "Books"})
    top_borrowed = loans.groupby("Book Name", as_index=False).size().rename(columns={"size": "Loans"}).sort_values("Loans", ascending=False).head(8) if not loans.empty else pd.DataFrame(columns=["Book Name", "Loans"])
    loan_status = loans.assign(Status=loans["Returned Date"].notna().map({True: "Returned", False: "Active"})).groupby("Status", as_index=False).size().rename(columns={"size": "Loans"}) if not loans.empty else pd.DataFrame(columns=["Status", "Loans"])
    chart_config = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "library_report"}}
    left, right = st.columns(2)
    with left:
        if borrowing.empty:
            st.info("Borrowing trends will appear after books are lent.", icon=":material/show_chart:")
        else:
            st.plotly_chart(px.line(borrowing, x="Period", y="Books", markers=True, title="Monthly borrowing trends", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch", config=chart_config)
        if top_borrowed.empty:
            st.info("Top borrowed books will appear after lending activity.", icon=":material/bar_chart:")
        else:
            st.plotly_chart(px.bar(top_borrowed.sort_values("Loans"), x="Loans", y="Book Name", orientation="h", title="Top borrowed books", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch", config=chart_config)
    with right:
        if category_counts.empty:
            st.info("Add books to see the category distribution.", icon=":material/donut_small:")
        else:
            st.plotly_chart(px.pie(category_counts, names="Category", values="Books", hole=0.55, title="Book category distribution", color_discrete_sequence=CHART_COLORS).update_layout(**CHART_LAYOUT), width="stretch", config=chart_config)
        if loan_status.empty:
            st.info("Loan status will appear after lending activity.", icon=":material/leaderboard:")
        else:
            st.plotly_chart(px.bar(loan_status, x="Status", y="Loans", title="Active vs returned loans", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch", config=chart_config)

    growth, registrations = st.columns(2)
    with growth:
        library_growth = _period_frame(books, "Added At")
        if not library_growth.empty:
            st.plotly_chart(px.area(library_growth, x="Period", y="Books", title="Library growth trends", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch", config=chart_config)
    with registrations:
        registration_frame = users.copy()
        if not registration_frame.empty:
            registration_frame["Created At"] = pd.to_datetime(registration_frame["Created At"])
            registrations_by_month = _period_frame(registration_frame, "Created At")
            if not registrations_by_month.empty:
                st.plotly_chart(px.bar(registrations_by_month, x="Period", y="Books", title="Member registration trends", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch", config=chart_config)


def _select_report_category() -> None:
    """Keep the report type valid when the user switches categories."""
    category = st.session_state.get("report_category") or "Book reports"
    if category not in REPORT_CATEGORIES:
        category = "Book reports"
    st.session_state.report_type = REPORT_CATEGORIES[category][0]


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
    with st.expander("Advanced filters", icon=":material/tune:"):
        row = st.columns(3)
        filter_dates = row[0].checkbox("Filter by date range", key="report_filter_dates")
        selected_dates = row[0].date_input("Date range", disabled=not filter_dates, key="report_date_range_optional")
        categories = row[1].multiselect("Categories", sorted(books["Category"].unique()), key="report_categories")
        authors = row[2].multiselect("Authors", sorted(books["Author"].unique(), key=str.casefold), key="report_authors")
        row = st.columns(4)
        minimum = row[0].number_input("Minimum price", min_value=0.0, value=float(books["Price"].min()), key="report_minimum_price")
        maximum = row[1].number_input("Maximum price", min_value=0.0, value=float(books["Price"].max()), key="report_maximum_price")
        tags = row[2].multiselect("Tags", _values(books, "Tags"), key="report_tags")
        collections = row[3].multiselect("Library / collection", _values(books, "Collections"), key="report_collections")
        row = st.columns(4)
        book_name = row[0].text_input("Book name", key="report_book_name")
        publishers = row[1].multiselect("Publishers", sorted(books["Publisher"].unique(), key=str.casefold), key="report_publishers")
        languages = row[2].multiselect("Languages", sorted(books["Language"].unique(), key=str.casefold), key="report_languages")
        formats = row[3].multiselect("Book formats", sorted(books["Format"].unique()), key="report_formats")
        row = st.columns(4)
        reading_statuses = row[0].multiselect("Reading status", sorted(books["Reading Status"].unique()), key="report_reading_statuses")
        ratings = row[1].multiselect("Ratings", sorted(books["Rating"].dropna().unique()), key="report_ratings")
        borrowers = row[2].multiselect("Borrowers", sorted(loans["Borrower"].unique(), key=str.casefold) if not loans.empty else [], key="report_borrowers")
        loan_statuses = row[3].multiselect("Loan status", sorted(loans["Status"].unique()) if not loans.empty else [], key="report_loan_statuses")
    if filter_dates and isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        books = books[books["Activity Date"].between(pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1]))]
    if categories:
        books = books[books["Category"].isin(categories)]
    if authors:
        books = books[books["Author"].isin(authors)]
    if book_name.strip():
        books = books[books["Book Name"].str.contains(book_name.strip(), case=False, regex=False, na=False)]
    if publishers:
        books = books[books["Publisher"].isin(publishers)]
    if languages:
        books = books[books["Language"].isin(languages)]
    if formats:
        books = books[books["Format"].isin(formats)]
    if reading_statuses:
        books = books[books["Reading Status"].isin(reading_statuses)]
    if ratings:
        books = books[books["Rating"].isin(ratings)]
    books = books.iloc[0:0] if minimum > maximum else books[books["Price"].between(minimum, maximum)]
    for tag in tags:
        books = books[books["Tags"].str.contains(tag, case=False, regex=False, na=False)]
    for collection in collections:
        books = books[books["Collections"].str.contains(collection, case=False, regex=False, na=False)]
    if borrowers:
        loans = loans[loans["Borrower"].isin(borrowers)]
    if loan_statuses:
        loans = loans[loans["Status"].isin(loan_statuses)]
    if borrowers or loan_statuses:
        books = books[books["ID"].isin(loans["Book ID"])]
    if not loans.empty:
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
    format_counts = books["Format"].value_counts()
    st.caption("Collection formats: " + " | ".join(f"{name}: {count}" for name, count in format_counts.items()))


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
    yearly = books.assign(Year=books["Activity Date"].dt.year).groupby("Year", as_index=False)["Price"].sum()
    categories = books.groupby("Category", as_index=False)["Price"].sum()
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(monthly, x="Period", y="Price", title="Monthly spending", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.pie(categories, names="Category", values="Price", title="Spending by category", hole=0.5, color_discrete_sequence=CHART_COLORS).update_layout(**CHART_LAYOUT), width="stretch")
    st.plotly_chart(px.bar(yearly, x="Year", y="Price", title="Yearly spending", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch")
    st.caption(f"Median book price: ₹{books['Price'].median():,.2f}")


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


def _purchase_trends(books: pd.DataFrame) -> None:
    purchases = books.dropna(subset=["Purchase Date"]).copy()
    if purchases.empty:
        st.info("Add purchase dates to see purchase trends.", icon=":material/calendar_month:")
        return
    purchases["Purchase Date"] = pd.to_datetime(purchases["Purchase Date"])
    purchases["Month"] = purchases["Purchase Date"].dt.to_period("M").dt.to_timestamp()
    purchases["Year"] = purchases["Purchase Date"].dt.year
    monthly = purchases.groupby("Month", as_index=False).agg(Books=("Book Name", "count"), Spending=("Price", "sum"))
    yearly = purchases.groupby("Year", as_index=False).agg(Books=("Book Name", "count"), Spending=("Price", "sum"))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(monthly, x="Month", y="Books", title="Books purchased by month", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch")
        st.plotly_chart(px.bar(yearly, x="Year", y="Books", title="Books purchased by year", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.line(monthly, x="Month", y="Spending", markers=True, title="Spending by month", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")
        st.plotly_chart(px.bar(yearly, x="Year", y="Spending", title="Spending by year", color_discrete_sequence=["#d05b36"]).update_layout(**CHART_LAYOUT), width="stretch")


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

    favourites = books[books["Favourite"]]
    favourite_author = favourites.groupby("Author")["Rating"].mean().sort_values(ascending=False).index[0] if not favourites.empty else authors.iloc[0]["Author"]
    recently_discovered = books.sort_values("Activity Date", ascending=False).drop_duplicates("Author").head(5)[["Author", "Activity Date"]]
    st.metric("Favourite author", favourite_author, "From favourites and ratings", border=True)
    st.markdown("**Recently discovered authors**")
    st.dataframe(recently_discovered, hide_index=True, width="stretch", column_config={"Activity Date": st.column_config.DateColumn(format="DD MMM YYYY")})


def _category_details(books: pd.DataFrame) -> None:
    categories = books.groupby("Category", as_index=False).agg(Books=("Book Name", "count"), Investment=("Price", "sum"), Average_Rating=("Rating", "mean"), Completion=("Reading Status", lambda values: (values == "Read").mean() * 100)).sort_values("Books", ascending=False)
    largest, smallest = categories.iloc[0], categories.iloc[-1]
    cards = st.columns(2)
    cards[0].metric("Largest category", largest["Category"], f"{largest['Books']} books", border=True)
    cards[1].metric("Smallest category", smallest["Category"], f"{smallest['Books']} books", border=True)
    st.dataframe(categories, hide_index=True, width="stretch", column_config={"Investment": st.column_config.NumberColumn(format="₹%.2f"), "Average_Rating": st.column_config.NumberColumn(format="%.1f"), "Completion": st.column_config.NumberColumn(format="%.0f%%")})
    dated = books.dropna(subset=["Added At"]).copy()
    if dated["Added At"].dt.to_period("M").nunique() >= 2:
        latest_period = dated["Added At"].dt.to_period("M").max()
        fastest = dated[dated["Added At"].dt.to_period("M") == latest_period]["Category"].value_counts()
        if not fastest.empty:
            st.metric("Fastest-growing category", fastest.index[0], f"{fastest.iloc[0]} books added in {latest_period.strftime('%b %Y')}", border=True)


def _ratings(books: pd.DataFrame) -> None:
    rated = books.dropna(subset=["Rating"])
    cards = st.columns(3)
    cards[0].metric("Top-rated books", int((books["Rating"] == 5).sum()), border=True)
    cards[1].metric("Favourite books", int(books["Favourite"].sum()), border=True)
    cards[2].metric("Books without ratings", int(books["Rating"].isna().sum()), border=True)
    if rated.empty:
        st.info("Rate books to see rating analytics.", icon=":material/star_outline:")
        return
    authors = rated.groupby("Author", as_index=False).agg(Average_Rating=("Rating", "mean"), Books=("Book Name", "count")).sort_values(["Average_Rating", "Books"], ascending=False)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.histogram(rated, x="Rating", title="Rating distribution", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.bar(authors.head(10).sort_values("Average_Rating"), x="Average_Rating", y="Author", orientation="h", title="Highest-rated authors", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch")
    st.dataframe(rated.nlargest(10, "Rating")[["Book Name", "Author", "Rating", "Favourite"]], hide_index=True, width="stretch")


def _reading(books: pd.DataFrame) -> None:
    statuses = books["Reading Status"].value_counts()
    read = int(statuses.get("Read", 0))
    cards = st.columns(4)
    for column, label, value in zip(cards, ("Read books", "Unread books", "Currently reading", "Reading completion"), (read, int(statuses.get("Unread", 0)), int(statuses.get("Reading", 0)), f"{read / len(books) * 100:.0f}%")):
        column.metric(label, value, border=True)
    category = books.groupby("Category", as_index=False).agg(Books=("Book Name", "count"), Read=("Reading Status", lambda values: (values == "Read").sum()))
    author = books.groupby("Author", as_index=False).agg(Books=("Book Name", "count"), Read=("Reading Status", lambda values: (values == "Read").sum())).sort_values("Read", ascending=False)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(category, x="Category", y="Read", title="Books read by category", color_discrete_sequence=["#1c8a83"]).update_layout(**CHART_LAYOUT), width="stretch")
    with right:
        st.plotly_chart(px.bar(author.head(10).sort_values("Read"), x="Read", y="Author", orientation="h", title="Books read by author", color_discrete_sequence=["#2d6f9e"]).update_layout(**CHART_LAYOUT), width="stretch")


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
    books = loans.groupby("Book Name", as_index=False).size().rename(columns={"size": "Loans"}).sort_values("Loans", ascending=False)
    timeline = _period_frame(loans, "Borrowed Date")
    st.markdown("**Most frequently lent books**")
    st.dataframe(books.head(10), hide_index=True, width="stretch")
    if not timeline.empty:
        st.plotly_chart(px.line(timeline, x="Period", y="Books", markers=True, title="Borrowing timeline", color_discrete_sequence=["#f0a85b"]).update_layout(**CHART_LAYOUT), width="stretch")
    upcoming = loans[(loans["Returned Date"].isna()) & loans["Expected Return"].notna()].sort_values("Expected Return")[["Book Name", "Borrower", "Expected Return", "Status"]]
    st.markdown("**Upcoming return dates**")
    st.dataframe(upcoming, hide_index=True, width="stretch", column_config={"Expected Return": st.column_config.DateColumn(format="DD MMM YYYY")})


def _custom_report(books: pd.DataFrame, loans: pd.DataFrame) -> None:
    st.dataframe(books, hide_index=True, width="stretch", column_config={"ID": None, "Price": st.column_config.NumberColumn(format="₹%.2f"), "Purchase Date": st.column_config.DateColumn(format="DD MMM YYYY"), "Added At": st.column_config.DatetimeColumn(format="DD MMM YYYY"), "Rating": st.column_config.NumberColumn(format="%d")})
    if not loans.empty:
        st.markdown("**Matching loan history**")
        st.dataframe(loans, hide_index=True, width="stretch", column_config={"Loan ID": None, "Book ID": None, "Borrowed Date": st.column_config.DateColumn(format="DD MMM YYYY"), "Expected Return": st.column_config.DateColumn(format="DD MMM YYYY"), "Returned Date": st.column_config.DateColumn(format="DD MMM YYYY")})


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


def _group(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    return frame.groupby(column, as_index=False).agg(Books=("Book Name", "count"), Investment=("Price", "sum")).sort_values("Books", ascending=False)


def _purchases_frame(books: pd.DataFrame) -> pd.DataFrame:
    """Use the catalogue timestamp when an explicit purchase date is unavailable."""
    purchases = books.copy()
    purchases["Transaction Date"] = pd.to_datetime(purchases["Purchase Date"]).fillna(
        pd.to_datetime(purchases["Added At"])
    )
    purchases["Date Source"] = purchases["Purchase Date"].notna().map(
        {True: "Purchase date", False: "Added date"}
    )
    return purchases


def _report_data(report_name: str, books: pd.DataFrame, loans: pd.DataFrame, wishlist: pd.DataFrame, libraries: pd.DataFrame, members: pd.DataFrame, users: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    today = pd.Timestamp(date.today())
    active_loans = loans[loans["Returned Date"].isna()] if not loans.empty else loans
    overdue = loans[loans["Status"] == "Overdue"] if not loans.empty else loans
    if report_name in {"All books", "Books added in date range"}:
        return report_name, books
    if report_name == "Available books":
        borrowed_ids = set(active_loans["Book ID"]) if not active_loans.empty else set()
        return report_name, books[~books["ID"].isin(borrowed_ids)]
    if report_name == "Borrowed books":
        return report_name, active_loans
    if report_name in {"Lost books", "Damaged books"}:
        return report_name, pd.DataFrame(columns=list(books.columns) + ["Report note"])
    if report_name == "Books by library":
        return report_name, _group(books, "Library")
    if report_name in {"Books by category", "Books by language", "Books by author", "Books by publisher", "Books by rating", "Books by reading status"}:
        columns = {
            "Books by category": "Category",
            "Books by language": "Language",
            "Books by author": "Author",
            "Books by publisher": "Publisher",
            "Books by rating": "Rating",
            "Books by reading status": "Reading Status",
        }
        return report_name, _group(books, columns[report_name])
    if report_name == "Recently added books":
        return report_name, books.sort_values("Added At", ascending=False).head(10)
    if report_name in {"All libraries", "Library-wise book count", "Recently created libraries"}:
        data = libraries.sort_values("Created At", ascending=False) if report_name == "Recently created libraries" else libraries
        return report_name, data.head(10) if report_name == "Recently created libraries" else data
    if report_name == "Library-wise member list":
        return report_name, members
    if report_name == "Library collection report":
        return report_name, books.groupby(["Library", "Category"], as_index=False).agg(Books=("Book Name", "count"), Investment=("Price", "sum")).sort_values(["Library", "Books"], ascending=[True, False])
    if report_name in {"All users", "All members"}:
        return report_name, users
    if report_name == "Active members":
        active_borrowers = set(loans["Borrower"]) if not loans.empty else set()
        return report_name, members[members["Username"].isin(active_borrowers)]
    if report_name == "Inactive members":
        active_borrowers = set(loans["Borrower"]) if not loans.empty else set()
        return report_name, members[~members["Username"].isin(active_borrowers)]
    if report_name == "Top borrowers":
        return report_name, loans.groupby("Borrower", as_index=False).size().rename(columns={"size": "Loans"}).sort_values("Loans", ascending=False) if not loans.empty else pd.DataFrame(columns=["Borrower", "Loans"])
    if report_name == "Members with overdue books":
        return report_name, overdue
    if report_name == "Users by library":
        return report_name, members.groupby("Library", as_index=False).agg(Users=("Username", "count"), Members=("Username", lambda names: ", ".join(sorted(names, key=str.casefold))))
    if report_name in {"Currently loaned books", "Current loans"}:
        return report_name, active_loans
    if report_name in {"Returned books", "Overdue books", "Overdue loans"}:
        statuses = {"Returned books": "Returned", "Overdue books": "Overdue", "Overdue loans": "Overdue"}
        return report_name, loans[loans["Status"] == statuses[report_name]]
    if report_name in {"Loan history", "Books loaned in date range"}:
        return report_name, loans
    if report_name == "Due today":
        return report_name, active_loans[pd.to_datetime(active_loans["Expected Return"]).eq(today)]
    if report_name == "Due this week":
        return report_name, active_loans[pd.to_datetime(active_loans["Expected Return"]).between(today, today + pd.Timedelta(days=7))]
    if report_name == "Most borrowed books":
        return report_name, loans.groupby("Book Name", as_index=False).size().rename(columns={"size": "Loans"}).sort_values("Loans", ascending=False) if not loans.empty else pd.DataFrame(columns=["Book Name", "Loans"])
    if report_name == "Popular categories":
        return report_name, books.groupby("Category", as_index=False).size().rename(columns={"size": "Books"}).sort_values("Books", ascending=False)
    if report_name == "Peak borrowing periods":
        return report_name, _period_frame(loans, "Borrowed Date") if not loans.empty else pd.DataFrame(columns=["Period", "Books"])
    if report_name == "Library utilisation":
        borrowed_ids = set(active_loans["Book ID"]) if not active_loans.empty else set()
        utilisation = books.groupby("Library", as_index=False).agg(Books=("Book Name", "count"), Active_loans=("ID", lambda ids: ids.isin(borrowed_ids).sum()))
        utilisation["Utilisation"] = utilisation["Active_loans"] / utilisation["Books"] * 100
        return report_name, utilisation
    if report_name == "Growth statistics":
        return report_name, _period_frame(books, "Added At")
    if report_name == "Wishlist books":
        return report_name, wishlist
    if report_name == "Wishlist by category":
        if wishlist.empty:
            return report_name, pd.DataFrame(columns=["Category", "Books"])
        return report_name, wishlist.groupby("Category", dropna=False).size().reset_index(name="Books").sort_values("Books", ascending=False)
    purchases = _purchases_frame(books)
    if report_name in {"All purchases", "Books purchased in date range"}:
        return report_name, purchases.sort_values("Transaction Date", ascending=False)
    if purchases.empty:
        return report_name, pd.DataFrame(columns=["Period", "Books", "Investment"])
    if report_name in {"Monthly purchase report", "Yearly purchase report"}:
        period = "Month" if report_name == "Monthly purchase report" else "Year"
        purchases["Period"] = purchases["Transaction Date"].dt.to_period("M").dt.to_timestamp() if period == "Month" else purchases["Transaction Date"].dt.year
        return report_name, purchases.groupby("Period", as_index=False).agg(Books=("Book Name", "count"), Investment=("Price", "sum"))
    if report_name == "Spending by category":
        return report_name, purchases.groupby("Category", as_index=False)["Price"].sum().rename(columns={"Price": "Investment"}).sort_values("Investment", ascending=False)
    return report_name, purchases.groupby("Library", as_index=False)["Price"].sum().rename(columns={"Price": "Investment"}).sort_values("Investment", ascending=False)


def _preview_report(title: str, frame: pd.DataFrame) -> None:
    with st.container(border=True):
        st.html(f'<p class="report-result-title">{title}</p><p class="report-result-meta">{len(frame):,} records ready to review or export</p>')
    if frame.empty:
        st.info("No records match this report and its filters.", icon=":material/filter_alt_off:")
        return
    searchable = frame.astype(str).fillna("")
    query = st.text_input("Search within report", key="report_result_search")
    if query.strip():
        frame = frame[searchable.apply(lambda row: row.str.contains(query.strip(), case=False, regex=False).any(), axis=1)]
    with st.container(border=True):
        sort_column, direction, view, page_size = st.columns((2, 2, 2, 1))
        sort_column = sort_column.selectbox("Sort by", list(frame.columns), key="report_result_sort")
        direction = direction.segmented_control(
            "Order",
            ["Newest first", "Oldest first"],
            default="Newest first",
            key="report_result_order",
        )
        view = view.segmented_control("View", ["Table", "List"], default="Table", key="report_result_view")
        page_size = page_size.selectbox("Rows", [10, 25, 50], key="report_result_page_size")
    frame = frame.sort_values(sort_column, ascending=direction == "Oldest first", na_position="last")
    pages = max(1, (len(frame) + page_size - 1) // page_size)
    page = min(int(st.session_state.get("report_result_page", 1)), pages)
    start = (page - 1) * page_size
    display = frame.iloc[start:start + page_size]
    if view == "List":
        preferred = [column for column in ("Book Name", "Author", "Category", "Status", "Price", "Investment") if column in display]
        display = display[preferred or list(display.columns)]
    st.dataframe(display, hide_index=True, width="stretch", column_config={"ID": None, "Loan ID": None, "Book ID": None, "Price": st.column_config.NumberColumn(format="₹%.2f"), "Investment": st.column_config.NumberColumn(format="₹%.2f")})
    previous, position, next_page = st.columns((1, 5, 1))
    if previous.button("Previous", icon=":material/chevron_left:", disabled=page == 1, key="report_previous_page"):
        st.session_state.report_result_page = page - 1
        st.rerun()
    position.caption(f"Showing {start + 1}-{start + len(display)} of {len(frame)} records · Page {page} of {pages}", text_alignment="center")
    if next_page.button("Next", icon=":material/chevron_right:", disabled=page == pages, key="report_next_page"):
        st.session_state.report_result_page = page + 1
        st.rerun()
    exporter = ExportService()
    left, right = st.columns(2)
    left.download_button("Download CSV", exporter.to_csv(frame), f"{title.lower().replace(' ', '_')}.csv", "text/csv", icon=":material/download:", width="stretch")
    if exporter.excel_available():
        summary = pd.DataFrame({"Report": [title], "Records": [len(frame)], "Generated": [pd.Timestamp.now().strftime("%d %b %Y %H:%M")]})
        right.download_button("Download Excel", exporter.to_excel({"Summary": summary, "Report": frame}), f"{title.lower().replace(' ', '_')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/table_view:", width="stretch")


def render(session: Session) -> None:
    """Render an on-demand library report generator."""
    render_page_header("Reports centre", "Choose a report, refine it with filters, then preview or export only the data you need.", "R")
    _report_styles()
    service = ReportService(session)
    selected_library_id = st.session_state.get("selected_library_id")
    all_books = service.books_frame()
    libraries, members, users = service.libraries_frame(), service.members_frame(), service.users_frame()
    is_administrator = st.session_state.get("authenticated_user", {}).get("role") == "Administrator"
    scope = "Current library"
    if is_administrator:
        scope = st.segmented_control("Report scope", ["Current library", "All libraries"], default="Current library", key="report_scope") or "Current library"
    use_all_libraries = scope == "All libraries"
    books = all_books if use_all_libraries else service.books_frame(selected_library_id)
    loans = service.loans_frame() if use_all_libraries else service.loans_frame(selected_library_id)
    if not use_all_libraries and not books.empty:
        library_names = set(books["Library"])
        libraries = libraries[libraries["Library"].isin(library_names)]
        members = members[members["Library"].isin(library_names)]
        users = users[users["Libraries"].apply(lambda names: bool(library_names.intersection(names.split(", "))))]
    wishlist = ExportService.wishlist_frame(WishlistService(session).list_items())
    view = st.segmented_control("Reports view", ["Report builder", "Overview", "Insights"], default=st.session_state.get("reports_view", "Report builder"), key="reports_view") or "Report builder"
    if view == "Overview":
        _report_overview(books, loans, libraries, members)
        return
    if view == "Insights":
        _insights(books, loans, users)
        return
    with st.container(border=True):
        st.html('<p class="report-section-title">Quick reports</p><p class="report-section-copy">Open the views you use most often.</p>')
        for column, (report_name, icon) in zip(st.columns(4), QUICK_REPORTS):
            if column.button(report_name, icon=icon, key=f"quick_{report_name.replace(' ', '_')}", width="stretch"):
                st.session_state.report_name = report_name
                st.session_state.report_generated = True
    with st.container(border=True):
        st.html('<p class="report-section-title">Build a tailored report</p><p class="report-section-copy">Choose a category, then narrow the data only when needed.</p>')
        category = st.segmented_control(
            "Report category",
            list(REPORT_CATEGORIES),
            default=st.session_state.get("report_category", "Book reports"),
            key="report_category",
            on_change=_select_report_category,
        ) or "Book reports"
        report_type, generate = st.columns((4, 1), vertical_alignment="bottom")
        selected = report_type.selectbox("Report type", REPORT_CATEGORIES[category], key="report_type")
        generated = generate.button("Generate", type="primary", icon=":material/analytics:", key="generate_report", width="stretch")
        filtered_books, filtered_loans = _filters(books, loans)
    if generated:
        st.session_state.report_name = selected
        st.session_state.report_generated = True
        history = st.session_state.setdefault("recent_reports", [])
        if selected not in history:
            history.insert(0, selected)
            del history[5:]
        st.toast(f"{selected} is ready.", icon=":material/check_circle:")
    if st.session_state.get("recent_reports"):
        history, favourites, templates = st.columns(3)
        with history:
            st.caption("Recent: " + " | ".join(st.session_state.recent_reports))
        with favourites:
            saved = st.session_state.setdefault("favourite_reports", [])
            if st.button("Favourite this report", icon=":material/star:", key="favourite_report") and selected not in saved:
                saved.append(selected)
                st.toast("Added to favourites.", icon=":material/star:")
        with templates:
            templates_saved = st.session_state.setdefault("report_templates", [])
            if st.button("Save template", icon=":material/bookmark_add:", key="save_report_template") and selected not in templates_saved:
                templates_saved.append(selected)
                st.toast("Template saved for this session.", icon=":material/bookmark_added:")
    saved_items = st.session_state.get("favourite_reports", []) + st.session_state.get("report_templates", [])
    if saved_items:
        st.caption("Saved: " + " | ".join(dict.fromkeys(saved_items)))
    if not st.session_state.get("report_generated"):
        st.info("Select a quick report or configure filters, then generate a report.", icon=":material/assessment:")
        return
    report_name = st.session_state.get("report_name", "All books")
    report_books = all_books if use_all_libraries and report_name in {"Books by library", "Library collection report", "Spending by library"} else filtered_books
    title, report_frame = _report_data(report_name, report_books, filtered_loans, wishlist, libraries, members, users)
    _preview_report(title, report_frame)
