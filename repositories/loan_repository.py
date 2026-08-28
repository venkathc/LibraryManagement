"""Persistence operations for book loans."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Loan


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

    def list(self) -> list[Loan]:
        statement = select(Loan).options(selectinload(Loan.book)).order_by(Loan.borrowed_date.desc())
        return list(self.session.scalars(statement))

    def active_for_book(self, book_id: int) -> Loan | None:
        statement = select(Loan).where(Loan.book_id == book_id, Loan.actual_return_date.is_(None))
        return self.session.scalar(statement)

    def update(self, loan: Loan) -> Loan:
        self.session.commit()
        self.session.refresh(loan)
        return loan
