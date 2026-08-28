"""Business rules for wishlist records."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from models import Book, WishlistItem
from repositories.wishlist_repository import WishlistRepository
from utils.validators import validate_wishlist_data


class WishlistService:
    """Create, search, update, and purchase wishlist items."""

    def __init__(self, session: Session) -> None:
        self.repository = WishlistRepository(session)

    def list_items(self, query: str | None = None, priority: str | None = None, status: str | None = None) -> list[WishlistItem]:
        return self.repository.list(query, priority, status)

    def create_item(self, data: dict[str, object]) -> WishlistItem:
        clean_data = self._clean_data(data)
        validate_wishlist_data(clean_data)
        return self.repository.add(WishlistItem(**clean_data))

    def update_item(self, item_id: int, data: dict[str, object]) -> WishlistItem:
        item = self.repository.get(item_id)
        if item is None:
            raise ValueError("Wishlist item not found.")
        clean_data = self._clean_data(data)
        validate_wishlist_data(clean_data)
        for field, value in clean_data.items():
            setattr(item, field, value)
        return self.repository.update(item)

    def delete_item(self, item_id: int) -> None:
        item = self.repository.get(item_id)
        if item is None:
            raise ValueError("Wishlist item not found.")
        self.repository.delete(item)

    def mark_purchased(self, item_id: int, book_data: dict[str, object]) -> Book:
        item = self.repository.get(item_id)
        if item is None:
            raise ValueError("Wishlist item not found.")
        if item.status == "Purchased":
            raise ValueError("This wishlist item has already been purchased.")
        from services.book_service import BookService

        service = BookService(self.repository.session)
        clean_book_data = service._clean_data(book_data)
        from utils.validators import validate_book_data

        validate_book_data(clean_book_data)
        if clean_book_data.get("isbn") and service.repository.find_by_isbn(str(clean_book_data["isbn"])):
            raise ValueError("A book with this ISBN already exists.")
        try:
            book = Book(**clean_book_data)
            item.status = "Purchased"
            self.repository.session.add(book)
            self.repository.session.add(item)
            self.repository.session.commit()
            self.repository.session.refresh(book)
            return book
        except Exception:
            self.repository.session.rollback()
            raise

    @staticmethod
    def _clean_data(data: dict[str, object]) -> dict[str, object]:
        clean_data = dict(data)
        for field in ("book_name", "author", "category", "notes"):
            if isinstance(clean_data.get(field), str):
                clean_data[field] = clean_data[field].strip() or None
        clean_data["book_name"] = clean_data.get("book_name") or ""
        expected_price = clean_data.get("expected_price")
        clean_data["expected_price"] = Decimal(str(expected_price)) if expected_price not in (None, "") else None
        return clean_data
