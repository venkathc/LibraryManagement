"""Database-backed report data for Phase 2."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from services.book_service import BookService


class ReportService:
    """Build tabular report data from the owned-book catalogue."""

    def __init__(self, session: Session) -> None:
        self.book_service = BookService(session)

    def books_frame(self) -> pd.DataFrame:
        books = self.book_service.search_books()
        return pd.DataFrame(
            [
                {
                    "Book Name": book.book_name,
                    "Author": book.author,
                    "Category": book.category or "Uncategorised",
                    "Price": float(book.price),
                    "Purchase Date": book.purchase_date,
                    "Rating": book.rating,
                    "Reading Status": book.reading_status,
                }
                for book in books
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
