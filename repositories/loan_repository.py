"""Persistence operations for book loans."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Book, Loan, LoanExtension


class LoanRepository:
    """Encapsulate loan queries and mutations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, loan: Loan) -> Loan:
        self.session.add(loan)
        self.session.commit()
        self.session.refresh(loan)
        return loan

    def get(self, loan_id: int) -> Loan | None:
        return self.session.get(Loan, loan_id)

    def list(self, library_id: int | None = None) -> list[Loan]:
        statement = select(Loan).options(selectinload(Loan.book)).order_by(Loan.borrowed_date.desc())
        if library_id is not None:
            statement = statement.join(Loan.book).where(Book.library_id == library_id)
        return list(self.session.scalars(statement))

    def active_for_book(self, book_id: int) -> Loan | None:
        statement = select(Loan).where(Loan.book_id == book_id, Loan.actual_return_date.is_(None))
        return self.session.scalar(statement)

    def update(self, loan: Loan) -> Loan:
        self.session.commit()
        self.session.refresh(loan)
        return loan

    def add_extension(self, extension: LoanExtension) -> LoanExtension:
        self.session.add(extension)
        self.session.commit()
        self.session.refresh(extension)
        return extension
