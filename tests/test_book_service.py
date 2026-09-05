"""Behaviour tests for Phase 1 book CRUD."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from services.book_service import BookService
from services.catalog_service import CatalogService
from services.export_service import ExportService
from services.wishlist_service import WishlistService
from services.image_service import ImageService
from services.loan_service import LoanService
from services.auth_service import AuthService
from services.library_service import LibraryService
from services.report_service import ReportService
from pages.reports import _report_data


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def book_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "book_name": "Clean Code",
        "author": "Robert C. Martin",
        "category": "Technology",
        "price": Decimal("499.00"),
        "purchase_date": None,
        "publisher": "Prentice Hall",
        "isbn": "9780132350884",
        "language": "English",
        "rating": 5,
        "reading_status": "Read",
        "personal_review": "Useful reference.",
        "notes": "",
        "is_favourite": True,
    }
    data.update(overrides)
    return data


def test_create_update_search_and_delete_book(session: Session) -> None:
    service = BookService(session)
    book = service.create_book(book_data())

    assert book.id is not None
    assert service.search_books("clean")[0].id == book.id

    updated = service.update_book(book.id, book_data(book_name="Clean Architecture", isbn="9780134494166"))
    assert updated.book_name == "Clean Architecture"

    service.delete_book(book.id)
    assert service.get_book(book.id) is None


def test_active_loan_can_be_extended_with_audit_history(session: Session) -> None:
    book = BookService(session).create_book(book_data())
    service = LoanService(session)
    loan = service.lend_book(
        {
            "book_id": book.id,
            "borrower_name": "Sam",
            "borrowed_date": date(2026, 9, 1),
            "expected_return_date": date(2026, 9, 8),
        }
    )

    updated = service.extend_loan(loan.id, date(2026, 9, 15))

    assert updated.expected_return_date == date(2026, 9, 15)
    assert len(updated.extensions) == 1
    assert updated.extensions[0].previous_return_date == date(2026, 9, 8)


def test_book_can_be_archived_trashed_restored_and_expired(session: Session) -> None:
    service = BookService(session)
    book = service.create_book(book_data())

    service.archive_books([book.id])
    assert not service.search_books()
    assert service.search_books(visibility="archived")[0].id == book.id

    service.restore_books([book.id])
    service.move_to_trash([book.id])
    assert service.search_books(visibility="trash")[0].id == book.id

    book.deleted_at = datetime.now() - timedelta(days=31)
    session.commit()
    assert service.purge_expired_trash() == 1
    assert service.get_book(book.id) is None


def test_duplicate_isbn_is_rejected(session: Session) -> None:
    service = BookService(session)
    service.create_book(book_data())

    with pytest.raises(ValueError, match="ISBN"):
        service.create_book(book_data(book_name="Another Book"))


def test_formatted_isbn_is_normalised_when_updating(session: Session) -> None:
    service = BookService(session)
    book = service.create_book(book_data())

    updated = service.update_book(book.id, book_data(isbn="0-8044 2957-X"))

    assert updated.isbn == "080442957X"


def test_fuzzy_search_ranks_typo_matches_above_threshold(session: Session) -> None:
    service = BookService(session)
    expected = service.create_book(book_data(book_name="Pulakeshi", isbn="9780134494166"))
    service.create_book(book_data(book_name="Clean Architecture", isbn="9780134757599"))

    results = service.fuzzy_search_books("  Pulkesi  ", threshold=60)

    assert results[0].book.id == expected.id
    assert results[0].score >= 60
    with pytest.raises(ValueError, match="threshold"):
        service.fuzzy_search_books("Pulkesi", threshold=101)


def test_negative_price_is_rejected(session: Session) -> None:
    with pytest.raises(ValueError, match="Price"):
        BookService(session).create_book(book_data(price=Decimal("-1")))


def test_book_can_be_assigned_tags_and_collections(session: Session) -> None:
    catalog = CatalogService(session)
    tag = catalog.create_tag("Technology")
    collection = catalog.create_collection("Engineering", "Software books")

    book = BookService(session).create_book(book_data(tag_ids=[tag.id], collection_ids=[collection.id]))

    assert [item.name for item in book.tags] == ["Technology"]
    assert [item.name for item in book.collections] == ["Engineering"]
    assert BookService(session).search_books("Technology")[0].id == book.id


def test_wishlist_purchase_conversion_and_exports(session: Session) -> None:
    wishlist = WishlistService(session)
    item = wishlist.create_item({"book_name": "Domain-Driven Design", "author": "Eric Evans", "category": "Technology", "expected_price": Decimal("650"), "priority": "High", "expected_purchase_date": None, "notes": "Read next", "status": "Planned"})

    book = wishlist.mark_purchased(item.id, book_data(book_name=item.book_name, author=item.author, isbn=""))
    frame = ExportService.books_frame([book])

    assert wishlist.repository.get(item.id).status == "Purchased"
    assert ExportService.to_csv(frame).startswith(b"ID,Book Name")
    assert ExportService.to_excel({"Books": frame}).startswith(b"PK")


def test_loan_lifecycle_and_overdue_rule(session: Session) -> None:
    book = BookService(session).create_book(book_data())
    service = LoanService(session)
    loan = service.lend_book({"book_id": book.id, "borrower_name": "Asha", "borrowed_date": date.today() - timedelta(days=10), "expected_return_date": date.today() - timedelta(days=1), "notes": ""})

    assert service.list_loans()[0].status == "Overdue"
    with pytest.raises(ValueError, match="active loan"):
        service.lend_book({"book_id": book.id, "borrower_name": "Ravi", "borrowed_date": date.today(), "expected_return_date": None})

    returned = service.mark_returned(loan.id, date.today())
    assert returned.status == "Returned"
    assert service.metrics()["active"] == 0


def test_cover_validation_rejects_non_image() -> None:
    class Upload:
        size = 4

        @staticmethod
        def getvalue() -> bytes:
            return b"nope"

    with pytest.raises(ValueError, match="valid PNG"):
        ImageService.save_cover(Upload())


def test_book_can_store_multiple_images(session: Session) -> None:
    book = BookService(session).create_book(
        book_data(cover_image_path="uploads/book_covers/front.jpg", image_paths=[
            "uploads/book_covers/front.jpg",
            "uploads/book_covers/back.jpg",
        ])
    )

    assert [image.image_path for image in book.images] == [
        "uploads/book_covers/front.jpg",
        "uploads/book_covers/back.jpg",
    ]


def test_author_report_includes_book_names(session: Session) -> None:
    service = BookService(session)
    service.create_book(book_data(book_name="Clean Code", isbn="9780132350884"))
    service.create_book(book_data(book_name="Clean Architecture", isbn="9780134494166"))

    report = ReportService(session).author_report()

    assert report.loc[0, "Book Names"] == "Clean Architecture, Clean Code"


def test_report_frames_include_custom_filter_fields_and_empty_schemas(session: Session) -> None:
    service = BookService(session)
    service.create_book(book_data(publisher="Prentice Hall", language="English"))
    reports = ReportService(session)

    frame = reports.books_frame()

    assert frame.loc[0, "Publisher"] == "Prentice Hall"
    assert frame.loc[0, "Language"] == "English"
    assert list(ReportService(session).loans_frame().columns) == [
        "Loan ID", "Book ID", "Book Name", "Borrower", "Borrowed Date", "Expected Return", "Returned Date", "Status"
    ]


def test_all_purchases_uses_added_date_when_purchase_date_is_missing(session: Session) -> None:
    reports = ReportService(session)
    BookService(session).create_book(book_data(purchase_date=None))

    title, purchases = _report_data(
        "All purchases",
        reports.books_frame(),
        reports.loans_frame(),
        ExportService.wishlist_frame([]),
        reports.libraries_frame(),
        reports.members_frame(),
        reports.users_frame(),
    )

    assert title == "All purchases"
    assert len(purchases) == 1
    assert purchases.loc[0, "Date Source"] == "Added date"
    assert purchases.loc[0, "Transaction Date"] is not None


def test_books_are_scoped_to_the_selected_library(session: Session) -> None:
    auth_service = AuthService(session)
    auth_service.ensure_admin()
    auth_service.create_user("asha", "Asha", "password", "User")
    library_service = LibraryService(session)
    personal = library_service.create_library("Personal", "admin")
    work = library_service.create_library("Work", "admin")
    library_service.add_member(work.id, "asha", "Member")
    book_service = BookService(session)
    personal_book = book_service.create_book(book_data(isbn="9780134494166"), personal.id)
    work_book = book_service.create_book(book_data(book_name="Work Book", isbn="9780134757599"), work.id)

    assert [book.id for book in book_service.search_books(library_id=personal.id)] == [personal_book.id]
    assert [book.id for book in book_service.search_books(library_id=work.id)] == [work_book.id]
    assert [library.name for library in library_service.list_libraries("asha")] == ["Work"]


def test_dashboard_metrics_and_loans_are_scoped_to_the_selected_library(session: Session) -> None:
    auth_service = AuthService(session)
    auth_service.ensure_admin()
    library_service = LibraryService(session)
    personal = library_service.create_library("Personal", "admin")
    work = library_service.create_library("Work", "admin")
    book_service = BookService(session)
    book_service.create_book(book_data(isbn="9780134494166", price=Decimal("100")), personal.id)
    work_book = book_service.create_book(
        book_data(book_name="Work Book", isbn="9780134757599", price=Decimal("900")), work.id
    )
    loan_service = LoanService(session)
    loan_service.lend_book({"book_id": work_book.id, "borrower_name": "Asha", "borrowed_date": date.today(), "expected_return_date": None})

    assert book_service.metrics(personal.id) == {
        "total_books": 1,
        "total_investment": 100.0,
        "unique_authors": 1,
        "unique_categories": 1,
    }
    assert loan_service.list_loans(personal.id) == []
    assert loan_service.metrics(personal.id)["active"] == 0
    assert loan_service.metrics(work.id)["active"] == 1
