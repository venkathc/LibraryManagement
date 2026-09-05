"""Behaviour tests for account management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from services.auth_service import AuthService


def test_display_name_is_saved_and_updated() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        service = AuthService(session)
        service.create_user("reader", "Asha Kumar", "secure-password", "User")

        user = service.find_user("reader")
        assert user is not None
        assert user.display_name == "Asha Kumar"

        service.update_user("reader", "reader", "Asha Rao", "User")
        assert service.find_user("reader").display_name == "Asha Rao"


def test_default_library_is_saved_for_a_user() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        service = AuthService(session)
        service.create_user("reader", "Asha Kumar", "secure-password", "User")

        service.set_default_library("reader", 12)

        assert service.find_user("reader").default_library_id == 12
