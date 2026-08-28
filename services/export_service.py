"""CSV and Excel exports for Phase 2 records."""

from __future__ import annotations

from copy import copy
from io import BytesIO

import pandas as pd

from models import Book, WishlistItem


class ExportService:
    """Convert application records into downloadable data files."""

    @staticmethod
    def excel_available() -> bool:
        """Return whether the Excel writer dependency is installed."""
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            return False
        return True

    @staticmethod
    def books_frame(books: list[Book]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "ID": book.id,
                    "Book Name": book.book_name,
                    "Author": book.author,
                    "Category": book.category,
                    "Price": float(book.price),
                    "Purchase Date": book.purchase_date,
                    "Publisher": book.publisher,
                    "ISBN": book.isbn,
                    "Language": book.language,
                    "Rating": book.rating,
                    "Reading Status": book.reading_status,
                    "Favourite": book.is_favourite,
                    "Tags": ", ".join(tag.name for tag in book.tags),
                    "Collections": ", ".join(collection.name for collection in book.collections),
                }
                for book in books
            ]
        )

    @staticmethod
    def wishlist_frame(items: list[WishlistItem]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "ID": item.id,
                    "Book Name": item.book_name,
                    "Author": item.author,
                    "Category": item.category,
                    "Expected Price": float(item.expected_price) if item.expected_price is not None else None,
                    "Priority": item.priority,
                    "Expected Purchase Date": item.expected_purchase_date,
                    "Status": item.status,
                    "Notes": item.notes,
                }
                for item in items
            ]
        )

    @staticmethod
    def to_csv(data_frame: pd.DataFrame) -> bytes:
        return data_frame.to_csv(index=False).encode("utf-8")

    @staticmethod
    def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
        if not ExportService.excel_available():
            raise RuntimeError("Excel export requires the openpyxl package.")
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for sheet_name, data_frame in sheets.items():
                data_frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                worksheet = writer.book[sheet_name[:31]]
                for cell in worksheet[1]:
                    header_font = copy(cell.font)
                    header_font.bold = True
                    cell.font = header_font
                for column_cells in worksheet.columns:
                    width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 50)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = width
        return output.getvalue()
