"""Library and membership management rules."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from models import Library, LibraryMembership, User


class LibraryService:
    """Manage separately scoped libraries and their member roles."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_libraries(self, username: str, is_administrator: bool = False) -> list[Library]:
        statement = select(Library).options(selectinload(Library.memberships).selectinload(LibraryMembership.user))
        if not is_administrator:
            statement = statement.join(Library.memberships).join(LibraryMembership.user).where(User.username == username)
        return list(self.session.scalars(statement.order_by(Library.name)))

    def create_library(self, name: str, owner_username: str) -> Library:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Library name is required.")
        owner = self.session.scalar(select(User).where(User.username == owner_username))
        if owner is None:
            raise ValueError("Owner account was not found.")
        library = Library(name=normalized_name)
        library.memberships.append(LibraryMembership(user=owner, role="Owner"))
        try:
            self.session.add(library)
            self.session.commit()
            self.session.refresh(library)
            return library
        except IntegrityError as error:
            self.session.rollback()
            raise ValueError("A library with that name already exists.") from error

    def add_member(self, library_id: int, username: str, role: str) -> None:
        if role not in {"Admin", "Member"}:
            raise ValueError("Select Admin or Member.")
        user = self.session.scalar(select(User).where(User.username == username))
        if user is None:
            raise ValueError("User account was not found.")
        membership = self.session.get(LibraryMembership, (library_id, user.id))
        if membership is None:
            self.session.add(LibraryMembership(library_id=library_id, user_id=user.id, role=role))
        elif membership.role != "Owner":
            membership.role = role
        self.session.commit()