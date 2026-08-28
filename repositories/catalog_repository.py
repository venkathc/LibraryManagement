"""Persistence operations for tags and collections."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Collection, Tag


class CatalogRepository:
    """Encapsulate reusable tag and collection access."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tags(self) -> list[Tag]:
        return list(self.session.scalars(select(Tag).order_by(Tag.name)))

    def list_collections(self) -> list[Collection]:
        return list(self.session.scalars(select(Collection).order_by(Collection.name)))

    def get_tags(self, tag_ids: list[int]) -> list[Tag]:
        return list(self.session.scalars(select(Tag).where(Tag.id.in_(tag_ids)))) if tag_ids else []

    def get_collections(self, collection_ids: list[int]) -> list[Collection]:
        return (
            list(self.session.scalars(select(Collection).where(Collection.id.in_(collection_ids))))
            if collection_ids
            else []
        )

    def add_tag(self, name: str) -> Tag:
        tag = Tag(name=name)
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def add_collection(self, name: str, description: str | None) -> Collection:
        collection = Collection(name=name, description=description)
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return collection

    def delete_tag(self, tag: Tag) -> None:
        self.session.delete(tag)
        self.session.commit()

    def delete_collection(self, collection: Collection) -> None:
        self.session.delete(collection)
        self.session.commit()
