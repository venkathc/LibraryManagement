"""Database-backed report data for Phase 2."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Library, User
from services.book_service import BookService
from services.loan_service import LoanService


BOOK_COLUMNS = [
    "ID",
    "Library",
    "Book Name",
    "Author",
    "Category",
    "Genre",
    "Format",
    "Price",
    "Purchase Date",
    "Added At",
    "Publisher",
    "Language",
    "Rating",
    "Reading Status",
    "Favourite",
    "Tags",
    "Collections",
]

LOAN_COLUMNS = [
    "Loan ID",
    "Book ID",
    "Book Name",
    "Borrower",
    "Borrowed Date",
    "Expected Return",
    "Returned Date",
    "Status",
]


class ReportService:
    """Build tabular report data from the owned-book catalogue."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.book_service = BookService(session)
        self.loan_service = LoanService(session)

    def books_frame(self, library_id: int | None = None) -> pd.DataFrame:
        books = self.book_service.search_books(library_id=library_id)
        frame = pd.DataFrame(
            [
                {
                    "ID": book.id,
                    "Library": book.library.name if book.library else "Unassigned",
                    "Book Name": book.book_name,
                    "Author": book.author,
                    "Category": book.category or "Uncategorised",
                    "Genre": book.genre or "Unspecified",
                    "Format": book.book_format,
                    "Price": float(book.price),
                    "Purchase Date": book.purchase_date,
                    "Added At": book.created_at,
                    "Publisher": book.publisher or "Unspecified",
                    "Language": book.language or "Unspecified",
                    "Rating": book.rating,
                    "Reading Status": book.reading_status,
                    "Favourite": book.is_favourite,
                    "Tags": ", ".join(tag.name for tag in book.tags),
                    "Collections": ", ".join(collection.name for collection in book.collections),
                }
                for book in books
            ],
            columns=BOOK_COLUMNS,
        )
        frame["Rating"] = pd.to_numeric(frame["Rating"], errors="coerce").astype("Int64")
        return frame

    def loans_frame(self, library_id: int | None = None) -> pd.DataFrame:
        """Return loan history without borrower contact details."""
        loans = self.loan_service.list_loans(library_id)
        return pd.DataFrame(
            [
                {
                    "Loan ID": loan.id,
                    "Book ID": loan.book_id,
                    "Book Name": loan.book.book_name,
                    "Borrower": loan.borrower_name,
                    "Borrowed Date": loan.borrowed_date,
                    "Expected Return": loan.expected_return_date,
                    "Returned Date": loan.actual_return_date,
                    "Status": loan.status,
                }
                for loan in loans
            ],
            columns=LOAN_COLUMNS,
        )

    def libraries_frame(self) -> pd.DataFrame:
        """Return library names, creation dates, and data-backed membership counts."""
        libraries = self.session.scalars(select(Library).order_by(Library.name)).all()
        return pd.DataFrame(
            [
                {
                    "Library": library.name,
                    "Books": len(library.books),
                    "Members": len(library.memberships),
                    "Created At": library.created_at,
                }
                for library in libraries
            ],
            columns=["Library", "Books", "Members", "Created At"],
        )

    def members_frame(self) -> pd.DataFrame:
        """Return library memberships without exposing account credentials."""
        libraries = self.session.scalars(select(Library).order_by(Library.name)).all()
        return pd.DataFrame(
            [
                {"Library": library.name, "Username": membership.user.username, "Role": membership.role}
                for library in libraries
                for membership in library.memberships
            ],
            columns=["Library", "Username", "Role"],
        )

    def users_frame(self) -> pd.DataFrame:
        """Return user accounts and their current library memberships."""
        users = self.session.scalars(select(User).order_by(User.username)).all()
        return pd.DataFrame(
            [
                {
                    "Username": user.username,
                    "Display Name": user.display_name or "",
                    "Role": user.role,
                    "Libraries": ", ".join(sorted(membership.library.name for membership in user.library_memberships)),
                    "Created At": user.created_at,
                }
                for user in users
            ],
            columns=["Username", "Display Name", "Role", "Libraries", "Created At"],
        )

    def author_report(self) -> pd.DataFrame:
        frame = self.books_frame()
        if frame.empty:
            return frame
        return frame.groupby("Author", dropna=False).agg(
            **{"Book Names": ("Book Name", lambda names: ", ".join(sorted(names, key=str.casefold)))},
            Books=("Book Name", "count"),
            Investment=("Price", "sum"),
            Average_Price=("Price", "mean"),
            Average_Rating=("Rating", "mean"),
            Read_Percentage=("Reading Status", lambda values: (values == "Read").mean() * 100),
        ).reset_index()

    def category_report(self) -> pd.DataFrame:
        frame = self.books_frame()
        if frame.empty:
            return frame
        return frame.groupby("Category", dropna=False).agg(
            **{"Book Names": ("Book Name", lambda names: ", ".join(sorted(names, key=str.casefold)))},
            Books=("Book Name", "count"),
            Investment=("Price", "sum"),
            Average_Rating=("Rating", "mean"),
        ).reset_index()
