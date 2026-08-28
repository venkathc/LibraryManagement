"""Persistence operations for books."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from models import Book, Collection, Tag


class BookRepository:
    """Encapsulate book queries and mutations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, book: Book) -> Book:
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def get(self, book_id: int) -> Book | None:
        return self.session.get(Book, book_id)

    def list(self, query: str | None = None) -> list[Book]:
        statement: Select[tuple[Book]] = select(Book).options(
            selectinload(Book.tags), selectinload(Book.collections)
        ).order_by(Book.created_at.desc())
        if query and (normalised_query := query.strip()):
            pattern = f"%{normalised_query}%"
            statement = statement.where(
                or_(
                    Book.book_name.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.category.ilike(pattern),
                    Book.publisher.ilike(pattern),
                    Book.isbn.ilike(pattern),
                    Book.notes.ilike(pattern),
                    Book.personal_review.ilike(pattern),
                    Book.tags.any(Tag.name.ilike(pattern)),
                    Book.collections.any(Collection.name.ilike(pattern)),
                )
            )
        return list(self.session.scalars(statement))

    def find_by_isbn(self, isbn: str) -> Book | None:
        return self.session.scalar(select(Book).where(Book.isbn == isbn))

    def update(self, book: Book) -> Book:
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        self.session.delete(book)
        self.session.commit()

    def dashboard_metrics(self) -> dict[str, int | float]:
        total_books = self.session.scalar(select(func.count(Book.id))) or 0
        total_investment = self.session.scalar(select(func.coalesce(func.sum(Book.price), 0))) or 0
        unique_authors = self.session.scalar(select(func.count(func.distinct(Book.author)))) or 0
        unique_categories = self.session.scalar(
            select(func.count(func.distinct(Book.category))).where(Book.category.is_not(None))
        ) or 0
        return {
            "total_books": total_books,
            "total_investment": float(total_investment),
            "unique_authors": unique_authors,
            "unique_categories": unique_categories,
        }
