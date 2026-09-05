"""Library dashboard with collection, lending, and reading insights."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.loan_service import LoanService
from utils.formatters import format_inr


CHART_LAYOUT = {
    "height": 310,
    "margin": {"l": 16, "r": 16, "t": 32, "b": 16},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Poppins, sans-serif"},
}


def _go_to(page: str) -> None:
    """Navigate through the application sidebar from a dashboard action."""
    st.session_state.navigation = page


def _render_styles() -> None:
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
        .dashboard-hero { align-items: center; background: linear-gradient(112deg, #123c55 0%, #146c72 58%, #1c8a83 100%); border: 1px solid rgba(255,255,255,.15); border-radius: 16px; box-shadow: 0 12px 28px rgba(12,58,78,.2); box-sizing: border-box; color: #fff; display: flex; justify-content: space-between; margin-bottom: 1rem; min-height: 174px; overflow: hidden; padding: 1.5rem; }
        .dashboard-hero-copy { max-width: 700px; }
        .dashboard-eyebrow { color: #f7d574; font: 600 .7rem "Poppins",sans-serif; letter-spacing: .08em; margin: 0 0 .35rem; text-transform: uppercase; }
        .dashboard-hero h2 { color: #fff; font: 700 1.8rem/1.2 "Poppins",sans-serif; letter-spacing: 0; margin: 0; }
        .dashboard-hero p { color: #d6f0ee; font: 400 .83rem/1.55 "Poppins",sans-serif; margin: .45rem 0 0; }
        .dashboard-library-illustration { align-items: end; display: flex; gap: 5px; height: 92px; margin: 0 1.4rem 0 1rem; }
        .dashboard-library-illustration span { border-radius: 4px 4px 1px 1px; box-shadow: 0 6px 12px rgba(6,47,57,.22); display: block; width: 16px; }
        .dashboard-library-illustration span:nth-child(1) { background: #f7d574; height: 62px; } .dashboard-library-illustration span:nth-child(2) { background: #d9f0e9; height: 82px; } .dashboard-library-illustration span:nth-child(3) { background: #f0a85b; height: 71px; } .dashboard-library-illustration span:nth-child(4) { background: #bdd7e7; height: 88px; } .dashboard-library-illustration span:nth-child(5) { background: #f7d574; height: 55px; }
        .dashboard-kpi-grid { display: grid; gap: .75rem; grid-template-columns: repeat(4,minmax(0,1fr)); margin: 0 0 1.2rem; }
        .dashboard-kpi-card { background: linear-gradient(145deg,#fff,#f2fbfa); border: 1px solid #d8ebe8; border-radius: 16px; box-shadow: 0 7px 18px rgba(15,75,86,.08); box-sizing: border-box; min-height: 142px; overflow: hidden; padding: 1rem; position: relative; transition: transform 160ms ease,box-shadow 160ms ease; }
        .dashboard-kpi-card:hover { box-shadow: 0 12px 24px rgba(15,75,86,.15); transform: translateY(-3px); }
        .dashboard-kpi-card::after { background: #1c8a83; bottom: 0; content: ""; height: 4px; left: 0; position: absolute; width: 100%; }
        .dashboard-kpi-card.is-loans { background: linear-gradient(145deg,#fffaf0,#fff3d6); border-color: #f2d497; } .dashboard-kpi-card.is-loans::after { background: #d18a1f; }
        .dashboard-kpi-card.is-alert { background: linear-gradient(145deg,#fff5f1,#ffe8df); border-color: #f4c2ae; } .dashboard-kpi-card.is-alert::after { background: #d05b36; }
        .dashboard-kpi-top { align-items: center; display: flex; justify-content: space-between; }
        .dashboard-kpi-icon { align-items: center; background: #d8f1ed; border-radius: 10px; color: #146c72; display: flex; font: 700 .6rem "Poppins",sans-serif; height: 35px; justify-content: center; width: 35px; }
        .is-loans .dashboard-kpi-icon { background: #ffe4a9; color: #9c6010; } .is-alert .dashboard-kpi-icon { background: #ffd4c4; color: #b74625; }
        .dashboard-kpi-label { color: #567179; font: 500 .72rem "Poppins",sans-serif; margin: .7rem 0 0; } .dashboard-kpi-value { color: #143f4e; font: 700 1.55rem/1.2 "Poppins",sans-serif; margin: .12rem 0 0; } .dashboard-kpi-note { color: #758d92; font: 400 .65rem "Poppins",sans-serif; margin: .4rem 0 0; }
        .dashboard-section-title { color: #264e59; font: 700 1rem "Poppins",sans-serif; margin: .35rem 0 .7rem; }
        .dashboard-insight { background: linear-gradient(145deg,#f5fbfa,#fff); border: 1px solid #d8ebe8; border-radius: 12px; box-shadow: 0 5px 14px rgba(15,75,86,.06); box-sizing: border-box; min-height: 102px; padding: .85rem; }
        .dashboard-insight-label { color: #6a8389; font: 600 .66rem "Poppins",sans-serif; margin: 0; text-transform: uppercase; } .dashboard-insight-value { color: #184c5b; font: 700 .9rem/1.35 "Poppins",sans-serif; margin: .35rem 0 0; overflow-wrap: anywhere; }
        .dashboard-activity-item { border-bottom: 1px solid #e5efee; padding: .68rem 0; } .dashboard-activity-item:last-child { border-bottom: 0; padding-bottom: 0; } .dashboard-activity-title { color: #244b56; font: 600 .76rem "Poppins",sans-serif; margin: 0; } .dashboard-activity-meta { color: #71888e; font: 400 .66rem "Poppins",sans-serif; margin: .15rem 0 0; }
        @media (prefers-color-scheme: dark) { .dashboard-kpi-card,.dashboard-insight { background: #173f4a; border-color: #34636b; } .dashboard-kpi-card.is-loans { background: #513d1d; border-color: #80652f; } .dashboard-kpi-card.is-alert { background: #542f29; border-color: #845147; } .dashboard-kpi-label,.dashboard-kpi-note,.dashboard-insight-label,.dashboard-activity-meta { color: #b7d0d2; } .dashboard-kpi-value,.dashboard-insight-value,.dashboard-section-title,.dashboard-activity-title { color: #f3fbfb; } .dashboard-activity-item { border-color: #34636b; } }
        @media (max-width: 950px) { .dashboard-kpi-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }
        @media (max-width: 640px) { .dashboard-hero { min-height: 0; padding: 1.1rem; } .dashboard-hero h2 { font-size: 1.35rem; } .dashboard-library-illustration { display: none; } .dashboard-kpi-grid { gap: .55rem; } .dashboard-kpi-card { min-height: 130px; padding: .8rem; } .dashboard-kpi-value { font-size: 1.28rem; } }
        </style>
        """
    )


def _render_kpis(metrics: dict[str, int | float], loan_metrics: dict[str, int]) -> None:
    cards = (
        ("books", "Books", metrics["total_books"], "In your personal collection"),
        ("investment", "Investment", format_inr(metrics["total_investment"]), "Value of your library"),
        ("authors", "Authors", metrics["unique_authors"], "Writers in your catalogue"),
        ("categories", "Categories", metrics["unique_categories"], "Ways to explore your library"),
        ("loans", "Lent", loan_metrics["active"], "Books currently with readers"),
        ("alert", "Overdue", loan_metrics["overdue"], "Needs a follow-up"),
        ("loans", "Due soon", loan_metrics["due_soon"], "Expected within seven days"),
    )
    icons = {"books": "&#128218;", "investment": "&#128176;", "authors": "&#9997;&#65039;", "categories": "&#127991;&#65039;", "loans": "&#128214;", "alert": "&#9888;&#65039;", "due": "&#9200;"}
    card_styles = ("books", "investment", "authors", "categories", "loans", "alert", "due")
    card_html = "".join(
        f'<article class="dashboard-kpi-card is-{card_style}"><div class="dashboard-kpi-top"><span class="dashboard-kpi-icon">{icons[card_style]}</span></div><p class="dashboard-kpi-label">{label}</p><p class="dashboard-kpi-value">{value}</p><p class="dashboard-kpi-note">{note}</p></article>'
        for card_style, (_, label, value, note) in zip(card_styles, cards)
    )
    st.html(f'<section class="dashboard-kpi-grid" aria-label="Library metrics">{card_html}</section>')


def _activity_html(title: str, items: list[tuple[str, str]]) -> str:
    body = "".join(
        f'<div class="dashboard-activity-item"><p class="dashboard-activity-title">{escape(item_title)}</p><p class="dashboard-activity-meta">{escape(item_meta)}</p></div>'
        for item_title, item_meta in items
    ) or '<p class="dashboard-activity-meta">No activity yet.</p>'
    return f'<section><h3 class="dashboard-section-title">{escape(title)}</h3>{body}</section>'


def render(session: Session) -> None:
    """Render a data-driven overview of the personal library."""
    book_service = BookService(session)
    loan_service = LoanService(session)
    selected_library_id = st.session_state.get("selected_library_id")
    books = book_service.search_books(library_id=selected_library_id)
    loans = loan_service.list_loans(selected_library_id)
    metrics = book_service.metrics(selected_library_id)
    loan_metrics = loan_service.metrics(selected_library_id)

    _render_styles()
    today = datetime.now().strftime("%A, %d %B %Y")
    authenticated_user = st.session_state.get("authenticated_user") or {}
    display_name = escape(str(authenticated_user.get("display_name") or authenticated_user.get("username") or "there"))
    st.html(
        f'''<section class="dashboard-hero"><div class="dashboard-hero-copy"><p class="dashboard-eyebrow">{today}</p><h2>Welcome back, {display_name}</h2><p>Your library holds {metrics["total_books"]} books across {metrics["unique_categories"]} categories. Pick up where your reading journey left off.</p></div><div class="dashboard-library-illustration" aria-label="Book collection illustration"><span></span><span></span><span></span><span></span><span></span></div></section>'''
    )
    _render_kpis(metrics, loan_metrics)

    st.html('<h3 class="dashboard-section-title">Quick actions</h3>')
    action_columns = st.columns(3)
    actions = (("Add book", "Add Book", "add"), ("Lend book", "Borrowed/Lent Books", "menu_book"), ("Return book", "Borrowed/Lent Books", "assignment_return"), ("Browse books", "View Books", "library_books"), ("Manage tags", "Tags and Collections", "sell"), ("Generate reports", "Reports", "analytics"))
    for column, (label, destination, icon) in zip(action_columns * 2, actions):
        with column:
            st.button(
                label,
                icon=f":material/{icon}:",
                key=f"dashboard_{label.replace(' ', '_')}",
                on_click=_go_to,
                args=(destination,),
                width="stretch",
            )

    if not books:
        st.info("Your library is empty. Add a book to start building your collection.", icon=":material/library_add:")
        return

    categories = Counter(book.category or "Uncategorised" for book in books)
    authors = Counter(book.author for book in books)
    borrowing = Counter(loan.borrowed_date.strftime("%b %Y") for loan in loans if loan.borrowed_date)
    loan_health = Counter("Returned" if loan.actual_return_date else "Active" for loan in loans)
    investments: dict[str, float] = {}
    for book in books:
        if book.purchase_date:
            period = book.purchase_date.strftime("%b %Y")
            investments[period] = investments.get(period, 0) + float(book.price)

    st.html('<h3 class="dashboard-section-title">Library at a glance</h3>')
    category_chart, activity_chart, loan_chart = st.columns(3)
    with category_chart:
        with st.container(border=True):
            st.markdown("**Books by category**")
            category_data = pd.DataFrame(categories.items(), columns=["Category", "Books"])
            figure = px.pie(category_data, names="Category", values="Books", color_discrete_sequence=["#1c8a83", "#f0a85b", "#2d6f9e", "#79b6b0", "#d05b36", "#b18a38"])
            figure.update_layout(**CHART_LAYOUT, showlegend=True)
            st.plotly_chart(figure, width="stretch", key="category_chart")
    with activity_chart:
        with st.container(border=True):
            st.markdown("**Borrowing activity**")
            if borrowing:
                borrowing_data = pd.DataFrame(borrowing.items(), columns=["Month", "Loans"])
                figure = px.bar(borrowing_data, x="Month", y="Loans", color_discrete_sequence=["#2d6f9e"])
                figure.update_layout(**CHART_LAYOUT)
                st.plotly_chart(figure, width="stretch", key="borrowing_chart")
            else:
                st.info("Borrowing activity will appear after a book is lent.", icon=":material/show_chart:")
    with loan_chart:
        with st.container(border=True):
            st.markdown("**Loan health**")
            if loan_health:
                loan_data = pd.DataFrame(loan_health.items(), columns=["Status", "Loans"])
                figure = px.bar(loan_data, x="Status", y="Loans", color_discrete_sequence=["#f0a85b"])
                figure.update_layout(**CHART_LAYOUT)
                st.plotly_chart(figure, width="stretch", key="loan_health_chart")
            else:
                st.info("Loan health will appear after lending activity.", icon=":material/leaderboard:")

    if st.toggle("Show collection insights", value=False, key="dashboard_collection_insights"):
        st.html('<h3 class="dashboard-section-title">Collection insights</h3>')
        chart_left, chart_right = st.columns(2)
        with chart_left:
            with st.container(border=True):
                st.markdown("**Top authors**")
                author_data = pd.DataFrame(authors.most_common(6), columns=["Author", "Books"])
                figure = px.bar(author_data.sort_values("Books"), x="Books", y="Author", orientation="h", color_discrete_sequence=["#2d6f9e"])
                figure.update_layout(**CHART_LAYOUT)
                st.plotly_chart(figure, width="stretch", key="author_chart")
        with chart_right:
            with st.container(border=True):
                st.markdown("**Investment trend**")
                investment_data = pd.DataFrame(investments.items(), columns=["Month", "Investment"])
                if investment_data.empty:
                    st.info("Add purchase dates to see investment trends.", icon=":material/trending_up:")
                else:
                    figure = px.line(investment_data, x="Month", y="Investment", markers=True, color_discrete_sequence=["#d18a1f"])
                    figure.update_layout(**CHART_LAYOUT)
                    st.plotly_chart(figure, width="stretch", key="investment_chart")

    most_expensive = max(books, key=lambda book: book.price)
    unread_count = sum(book.reading_status == "Unread" for book in books)
    insight_columns = st.columns(4)
    insights = (("Most expensive book", f"{most_expensive.book_name} ({format_inr(most_expensive.price)})"), ("Favourite author", authors.most_common(1)[0][0]), ("Most read category", categories.most_common(1)[0][0]), ("Waiting to be read", f"{unread_count} unread book{'s' if unread_count != 1 else ''}"))
    for column, (label, value) in zip(insight_columns, insights):
        with column:
            st.html(f'<article class="dashboard-insight"><p class="dashboard-insight-label">{escape(label)}</p><p class="dashboard-insight-value">{escape(value)}</p></article>')

    activity_columns = st.columns(3)
    recently_added = [(book.book_name, f"Added {book.created_at.strftime('%d %b %Y') if book.created_at else 'recently'}") for book in books[:4]]
    recently_lent = [(loan.book.book_name, f"Lent to {loan.borrower_name} on {loan.borrowed_date.strftime('%d %b %Y')}") for loan in loans if loan.actual_return_date is None][:4]
    recent_returns = [(loan.book.book_name, f"Returned {loan.actual_return_date.strftime('%d %b %Y')}") for loan in loans if loan.actual_return_date][:4]
    for column, (title, items) in zip(activity_columns, (("Recently added", recently_added), ("Recently lent", recently_lent), ("Recent returns", recent_returns))):
        with column:
            with st.container(border=True):
                st.html(_activity_html(title, items))
