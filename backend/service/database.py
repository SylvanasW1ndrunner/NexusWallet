"""
Database connection management for Transaction Aggregation Service

Provides SQLAlchemy engine and session management with connection pooling.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from backend.service.config import config
from backend.service.schema import Base


# Create database engine with connection pooling
engine = create_engine(
    config.database_url,
    poolclass=QueuePool,
    pool_size=config.db_pool_size,
    max_overflow=config.db_max_overflow,
    pool_timeout=config.db_pool_timeout,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """
    Initialize database - create all tables

    This should be called once during application startup
    """
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def drop_db():
    """
    Drop all database tables

    WARNING: This will delete all data!
    Use only for development/testing
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session context manager

    Usage:
        with get_db_session() as session:
            # Use session here
            transaction = session.query(MultisigTransaction).first()

    Yields:
        SQLAlchemy Session

    The session is automatically committed on success or rolled back on error.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Session:
    """
    Get database session (for dependency injection)

    Usage with FastAPI:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            # Use db here
            pass

    Returns:
        SQLAlchemy Session

    Note: Caller is responsible for closing the session
    """
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def check_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))

        return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False


# Statistics and monitoring
def get_pool_stats() -> dict:
    """
    Get connection pool statistics

    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool
    return {
        'size': pool.size(),
        'checked_in': pool.checkedin(),
        'overflow': pool.overflow(),
        'checked_out': pool.checkedout()
    }
