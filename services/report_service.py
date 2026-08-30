"""Database-backed report data for Phase 2."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from services.book_service import BookService
from services.loan_service import LoanService


class ReportService:
    """Build tabular report data from the owned-book catalogue."""

    def __init__(self, session: Session) -> None:
        self.book_service = BookService(session)
        self.loan_service = LoanService(session)

    def books_frame(self) -> pd.DataFrame:
        books = self.book_service.search_books()
        return pd.DataFrame(
            [
                {
                    "ID": book.id,
                    "Book Name": book.book_name,
                    "Author": book.author,
                    "Category": book.category or "Uncategorised",
                    "Price": float(book.price),
                    "Purchase Date": book.purchase_date,
                    "Added At": book.created_at,
                    "Rating": book.rating,
                    "Reading Status": book.reading_status,
                    "Favourite": book.is_favourite,
                    "Tags": ", ".join(tag.name for tag in book.tags),
                    "Collections": ", ".join(collection.name for collection in book.collections),
                }
                for book in books
            ]
        )

    def loans_frame(self) -> pd.DataFrame:
        """Return loan history without borrower contact details."""
        loans = self.loan_service.list_loans()
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
            ]
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
