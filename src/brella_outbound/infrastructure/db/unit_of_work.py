"""Unit of Work pattern for SQLAlchemy session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from brella_outbound.infrastructure.db.tables.metadata import metadata


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory.

    Args:
        database_url: SQLAlchemy database URL (e.g. sqlite:///brella.db).

    Returns:
        Configured sessionmaker instance.
    """
    engine = create_engine(database_url, echo=False)
    metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


class UnitOfWork:
    """Manages database transactions via context manager."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> "UnitOfWork":
        """Open a new session."""
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit on success, rollback on error, then close."""
        if self.session is None:
            return
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    def rollback(self) -> None:
        """Explicitly rollback the current transaction."""
        if self.session:
            self.session.rollback()
