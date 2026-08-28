"""Business rules for tags and collections."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Collection, Tag
from repositories.catalog_repository import CatalogRepository


class CatalogService:
    """Manage reusable book tags and collections."""

    def __init__(self, session: Session) -> None:
        self.repository = CatalogRepository(session)

    def list_tags(self) -> list[Tag]:
        return self.repository.list_tags()

    def list_collections(self) -> list[Collection]:
        return self.repository.list_collections()

    def create_tag(self, name: str) -> Tag:
        return self._create(self.repository.add_tag, name)

    def create_collection(self, name: str, description: str | None = None) -> Collection:
        clean_name = self._clean_name(name, "Collection")
        try:
            return self.repository.add_collection(clean_name, (description or "").strip() or None)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ValueError("A collection with this name already exists.") from error

    def delete_tag(self, tag_id: int) -> None:
        tag = next((item for item in self.list_tags() if item.id == tag_id), None)
        if tag is None:
            raise ValueError("Tag not found.")
        if tag.books:
            raise ValueError("Remove this tag from all books before deleting it.")
        self.repository.delete_tag(tag)

    def delete_collection(self, collection_id: int) -> None:
        collection = next((item for item in self.list_collections() if item.id == collection_id), None)
        if collection is None:
            raise ValueError("Collection not found.")
        if collection.books:
            raise ValueError("Remove this collection from all books before deleting it.")
        self.repository.delete_collection(collection)

    def _create(self, creator: object, name: str) -> Tag:
        clean_name = self._clean_name(name, "Tag")
        try:
            return creator(clean_name)  # type: ignore[operator]
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ValueError("A tag with this name already exists.") from error

    @staticmethod
    def _clean_name(value: str, label: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            raise ValueError(f"{label} name is required.")
        return clean_value
