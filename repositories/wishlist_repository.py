"""Persistence operations for wishlist items."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models import WishlistItem


class WishlistRepository:
    """Encapsulate wishlist queries and mutations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, query: str | None = None, priority: str | None = None, status: str | None = None) -> list[WishlistItem]:
        statement = select(WishlistItem).order_by(WishlistItem.created_at.desc())
        if query and (term := query.strip()):
            pattern = f"%{term}%"
            statement = statement.where(or_(WishlistItem.book_name.ilike(pattern), WishlistItem.author.ilike(pattern)))
        if priority:
            statement = statement.where(WishlistItem.priority == priority)
        if status:
            statement = statement.where(WishlistItem.status == status)
        return list(self.session.scalars(statement))

    def get(self, item_id: int) -> WishlistItem | None:
        return self.session.get(WishlistItem, item_id)

    def add(self, item: WishlistItem) -> WishlistItem:
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(self, item: WishlistItem) -> WishlistItem:
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, item: WishlistItem) -> None:
        self.session.delete(item)
        self.session.commit()
