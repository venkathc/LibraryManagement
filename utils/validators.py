"""Reusable validation for book data."""

from __future__ import annotations

from decimal import Decimal
import re

VALID_READING_STATUSES = {"Unread", "Reading", "Read"}
VALID_WISHLIST_PRIORITIES = {"Low", "Medium", "High"}
VALID_WISHLIST_STATUSES = {"Planned", "Ordered", "Purchased", "Cancelled"}


def validate_book_data(data: dict[str, object]) -> None:
    """Raise ValueError when a book payload violates core constraints."""
    if not str(data.get("book_name") or "").strip():
        raise ValueError("Book name is required.")
    if not str(data.get("author") or "").strip():
        raise ValueError("Author is required.")
    if Decimal(str(data.get("price", 0))) < 0:
        raise ValueError("Price cannot be negative.")
    rating = data.get("rating")
    if rating is not None and not 1 <= int(rating) <= 5:
        raise ValueError("Rating must be between 1 and 5.")
    if data.get("reading_status") not in VALID_READING_STATUSES:
        raise ValueError("Reading status must be Unread, Reading, or Read.")
    isbn = re.sub(r"[\s-]", "", str(data.get("isbn") or "")).upper()
    if isbn and not re.fullmatch(r"\d{13}|\d{9}[\dX]", isbn):
        raise ValueError("ISBN must be a valid 10-digit or 13-digit value when supplied.")


def validate_wishlist_data(data: dict[str, object]) -> None:
    """Raise ValueError when a wishlist payload violates core constraints."""
    if not str(data.get("book_name") or "").strip():
        raise ValueError("Book name is required.")
    expected_price = data.get("expected_price")
    if expected_price is not None and Decimal(str(expected_price)) < 0:
        raise ValueError("Expected price cannot be negative.")
    if data.get("priority") not in VALID_WISHLIST_PRIORITIES:
        raise ValueError("Priority must be Low, Medium, or High.")
    if data.get("status") not in VALID_WISHLIST_STATUSES:
        raise ValueError("Status must be Planned, Purchased, or Cancelled.")
