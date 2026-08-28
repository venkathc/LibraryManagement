"""Business rules for the Phase 1 book catalogue."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re

from rapidfuzz import fuzz
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Book, BookImage
from repositories.book_repository import BookRepository
from repositories.catalog_repository import CatalogRepository
from utils.validators import validate_book_data


@dataclass(frozen=True)
class SearchResult:
    """A book matched by fuzzy search with its relevance score."""

    book: Book
    score: float


class BookService:
    """Coordinates validation and book persistence."""

    def __init__(self, session: Session) -> None:
        self.repository = BookRepository(session)

    def create_book(self, data: dict[str, object]) -> Book:
        clean_data = self._clean_data(data)
        tag_ids = clean_data.pop("tag_ids", [])
        collection_ids = clean_data.pop("collection_ids", [])
        image_paths = clean_data.pop("image_paths", [])
        validate_book_data(clean_data)
        isbn = clean_data.get("isbn")
        if isbn and self.repository.find_by_isbn(str(isbn)):
            raise ValueError("A book with this ISBN already exists.")
        try:
            catalog = CatalogRepository(self.repository.session)
            tags = catalog.get_tags(tag_ids)
            collections = catalog.get_collections(collection_ids)
            book = Book(**clean_data)
            book.tags = tags
            book.collections = collections
            book.images = [BookImage(image_path=path, position=index) for index, path in enumerate(image_paths)]
            return self.repository.add(book)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ValueError("Could not save the book. ISBN values must be unique.") from error

    def update_book(self, book_id: int, data: dict[str, object]) -> Book:
        book = self.repository.get(book_id)
        if book is None:
            raise ValueError("Book not found.")
        clean_data = self._clean_data(data)
        tag_ids = clean_data.pop("tag_ids", None)
        collection_ids = clean_data.pop("collection_ids", None)
        image_paths = clean_data.pop("image_paths", [])
        validate_book_data(clean_data)
        isbn = clean_data.get("isbn")
        existing = self.repository.find_by_isbn(str(isbn)) if isbn else None
        if existing and existing.id != book.id:
            raise ValueError("A book with this ISBN already exists.")
        for field, value in clean_data.items():
            setattr(book, field, value)
        catalog = CatalogRepository(self.repository.session)
        if tag_ids is not None:
            book.tags = catalog.get_tags(tag_ids)
        if collection_ids is not None:
            book.collections = catalog.get_collections(collection_ids)
        book.images.extend(
            BookImage(image_path=path, position=len(book.images) + index) for index, path in enumerate(image_paths)
        )
        try:
            return self.repository.update(book)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ValueError("Could not update the book.") from error

    def delete_book(self, book_id: int) -> None:
        book = self.repository.get(book_id)
        if book is None:
            raise ValueError("Book not found.")
        self.repository.delete(book)

    def get_book(self, book_id: int) -> Book | None:
        return self.repository.get(book_id)

    def search_books(self, query: str | None = None) -> list[Book]:
        return self.repository.list(query)

    def fuzzy_search_books(self, query: str, threshold: int = 70) -> list[SearchResult]:
        """Return ranked fuzzy matches across catalogued book metadata."""
        normalized_query = self._normalize_search_text(query)
        if not normalized_query:
            return []
        if not 0 <= threshold <= 100:
            raise ValueError("Similarity threshold must be between 0 and 100.")
        results: list[SearchResult] = []
        for book in self.repository.list():
            fields = [
                book.book_name,
                book.author,
                book.category,
                book.publisher,
                book.isbn,
                book.notes,
                book.personal_review,
                *(tag.name for tag in book.tags),
                *(collection.name for collection in book.collections),
            ]
            score = max(
                (fuzz.WRatio(normalized_query, self._normalize_search_text(field)) for field in fields if field),
                default=0.0,
            )
            if score >= threshold:
                results.append(SearchResult(book=book, score=score))
        return sorted(results, key=lambda result: (-result.score, result.book.book_name.casefold()))

    def metrics(self) -> dict[str, int | float]:
        return self.repository.dashboard_metrics()

    @staticmethod
    def _clean_data(data: dict[str, object]) -> dict[str, object]:
        clean_data = dict(data)
        for field in ("book_name", "author", "category", "publisher", "isbn", "language", "personal_review", "notes"):
            if isinstance(clean_data.get(field), str):
                clean_data[field] = clean_data[field].strip() or None
        if clean_data.get("isbn"):
            clean_data["isbn"] = re.sub(r"[\s-]", "", str(clean_data["isbn"])).upper()
        clean_data["book_name"] = clean_data.get("book_name") or ""
        clean_data["author"] = clean_data.get("author") or ""
        clean_data["price"] = Decimal(str(clean_data.get("price", "0")))
        if clean_data.get("purchase_date") == "":
            clean_data["purchase_date"] = None
        return clean_data

    @staticmethod
    def _normalize_search_text(value: object) -> str:
        """Normalize user-visible text for case-insensitive fuzzy matching."""
        return " ".join(str(value or "").split()).casefold()
