"""
SQLAlchemy engine + session factory.
Usage: from common.db import get_db
       with get_db() as db: ...
"""
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from common.config import settings


def _normalize_db_url(url: str) -> str:
    """Ensure explicit PostgreSQL driver selection so SQLAlchemy never fails
    with ambiguous driver import fallbacks.
    """
    if url.startswith("postgresql://"):
        try:
            import psycopg2  # noqa: F401
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            try:
                import psycopg  # noqa: F401
                return url.replace("postgresql://", "postgresql+psycopg://", 1)
            except ImportError:
                pass
    return url


engine = create_engine(
    _normalize_db_url(settings.DATABASE_URL),
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
