"""Database models for the Phase 1 library catalogue."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


book_tags = Table(
    "book_tags",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

book_collections = Table(
    "book_collections",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("collection_id", ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
)


class Book(Base):
    """A book owned by the user."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    library_id: Mapped[int | None] = mapped_column(ForeignKey("libraries.id"), index=True)
    book_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(120))
    genre: Mapped[str | None] = mapped_column(String(120))
    book_format: Mapped[str] = mapped_column(String(20), nullable=False, default="Physical")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    publisher: Mapped[str | None] = mapped_column(String(255))
    isbn: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    language: Mapped[str | None] = mapped_column(String(80))
    rating: Mapped[int | None] = mapped_column(Integer)
    reading_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Unread")
    personal_review: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    cover_image_path: Mapped[str | None] = mapped_column(String(255))
    is_favourite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    tags: Mapped[list["Tag"]] = relationship(secondary=book_tags, back_populates="books")
    collections: Mapped[list["Collection"]] = relationship(
        secondary=book_collections, back_populates="books"
    )
    images: Mapped[list["BookImage"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="BookImage.position"
    )
    loans: Mapped[list["Loan"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    library: Mapped["Library | None"] = relationship(back_populates="books")


class Library(Base):
    """A separately managed book collection with its own members."""

    __tablename__ = "libraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    books: Mapped[list[Book]] = relationship(back_populates="library")
    memberships: Mapped[list["LibraryMembership"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )


class LibraryMembership(Base):
    """A user's role within a specific library."""

    __tablename__ = "library_memberships"

    library_id: Mapped[int] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="Member")
    library: Mapped[Library] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="library_memberships")


class BookImage(Base):
    """An image associated with a book, including front and back covers."""

    __tablename__ = "book_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    book: Mapped[Book] = relationship(back_populates="images")


class Tag(Base):
    """A reusable label assigned to one or more books."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#1C8A83")
    description: Mapped[str | None] = mapped_column(Text)
    books: Mapped[list[Book]] = relationship(secondary=book_tags, back_populates="tags")


class Collection(Base):
    """A named group of books."""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    books: Mapped[list[Book]] = relationship(secondary=book_collections, back_populates="collections")


class WishlistItem(Base):
    """A book the user plans to purchase."""

    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(120))
    expected_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="Medium")
    expected_purchase_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="Planned")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Loan(Base):
    """A historical record of a book lent to another person."""

    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    borrower_name: Mapped[str] = mapped_column(String(255), nullable=False)
    borrower_contact: Mapped[str | None] = mapped_column(String(255))
    borrowed_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_return_date: Mapped[date | None] = mapped_column(Date)
    actual_return_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="Lent")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    book: Mapped[Book] = relationship(back_populates="loans")
    extensions: Mapped[list["LoanExtension"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan", order_by="LoanExtension.created_at.desc()"
    )


class LoanExtension(Base):
    """An audit entry for a revised loan due date."""

    __tablename__ = "loan_extensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_return_date: Mapped[date | None] = mapped_column(Date)
    extended_return_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    loan: Mapped[Loan] = relationship(back_populates="extensions")


class User(Base):
    """An account that can access the personal library."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="User")
    default_library_id: Mapped[int | None] = mapped_column(ForeignKey("libraries.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    library_memberships: Mapped[list[LibraryMembership]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
