"""Business rules for lending and returning books."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from models import Loan, LoanExtension
from repositories.book_repository import BookRepository
from repositories.loan_repository import LoanRepository


class LoanService:
    """Create and close loan records while retaining their history."""

    def __init__(self, session: Session) -> None:
        self.repository = LoanRepository(session)
        self.books = BookRepository(session)

    def lend_book(self, data: dict[str, object]) -> Loan:
        book_id = int(data.get("book_id") or 0)
        borrower_name = str(data.get("borrower_name") or "").strip()
        borrowed_date = data.get("borrowed_date")
        expected_return_date = data.get("expected_return_date")
        if self.books.get(book_id) is None:
            raise ValueError("Book not found.")
        if not borrower_name:
            raise ValueError("Borrower name is required.")
        if not isinstance(borrowed_date, date):
            raise ValueError("Borrowed date is required.")
        if expected_return_date is not None and not isinstance(expected_return_date, date):
            raise ValueError("Expected return date is invalid.")
        if expected_return_date and expected_return_date < borrowed_date:
            raise ValueError("Expected return date cannot be earlier than the borrowed date.")
        if self.repository.active_for_book(book_id):
            raise ValueError("This book already has an active loan.")
        loan = Loan(
            book_id=book_id,
            borrower_name=borrower_name,
            borrower_contact=str(data.get("borrower_contact") or "").strip() or None,
            borrowed_date=borrowed_date,
            expected_return_date=expected_return_date,
            notes=str(data.get("notes") or "").strip() or None,
            status="Lent",
        )
        return self.repository.add(loan)

    def mark_returned(self, loan_id: int, actual_return_date: date) -> Loan:
        loan = self.repository.get(loan_id)
        if loan is None:
            raise ValueError("Loan not found.")
        if loan.actual_return_date is not None:
            raise ValueError("This loan has already been returned.")
        if actual_return_date < loan.borrowed_date:
            raise ValueError("Actual return date cannot be earlier than the borrowed date.")
        loan.actual_return_date = actual_return_date
        loan.status = "Returned"
        return self.repository.update(loan)

    def extend_loan(self, loan_id: int, expected_return_date: date) -> Loan:
        """Revise an active loan due date and retain its extension audit trail."""
        loan = self.repository.get(loan_id)
        if loan is None:
            raise ValueError("Loan not found.")
        if loan.actual_return_date is not None:
            raise ValueError("Returned loans cannot be extended.")
        if expected_return_date <= (loan.expected_return_date or loan.borrowed_date):
            raise ValueError("The extended return date must be later than the current due date.")
        self.repository.add_extension(
            LoanExtension(
                loan_id=loan.id,
                previous_return_date=loan.expected_return_date,
                extended_return_date=expected_return_date,
            )
        )
        loan.expected_return_date = expected_return_date
        return self.repository.update(loan)

    def list_loans(self, library_id: int | None = None) -> list[Loan]:
        loans = self.repository.list(library_id)
        today = date.today()
        for loan in loans:
            if loan.actual_return_date is None and loan.expected_return_date and loan.expected_return_date < today:
                loan.status = "Overdue"
            elif loan.actual_return_date is None:
                loan.status = "Lent"
        self.repository.session.commit()
        return loans

    def metrics(self, library_id: int | None = None) -> dict[str, int]:
        loans = self.list_loans(library_id)
        today = date.today()
        return {
            "active": sum(loan.actual_return_date is None for loan in loans),
            "overdue": sum(loan.status == "Overdue" for loan in loans),
            "due_soon": sum(
                loan.actual_return_date is None
                and loan.expected_return_date is not None
                and today <= loan.expected_return_date <= today + timedelta(days=7)
                for loan in loans
            ),
        }
