"""
Database Initialization Script for Transaction Aggregation Service

Creates all necessary database tables.

Usage:
    python backend/service/init_db.py
"""
from backend.service.database import init_db, check_connection


def main():
    """Initialize database tables"""
    print("=" * 60)
    print("Transaction Aggregation Service - Database Initialization")
    print("=" * 60)

    # Check database connection
    print("\n1. Checking database connection...")
    if not check_connection():
        print("✗ Database connection failed!")
        print("\nPlease check:")
        print("  - DATABASE_URL environment variable is set correctly")
        print("  - PostgreSQL server is running")
        print("  - Database credentials are correct")
        return 1

    print("✓ Database connection successful")

    # Create tables
    print("\n2. Creating database tables...")
    try:
        init_db()
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print("\nTables created:")
        print("  - multisig_transactions")
        print("\nIndexes created:")
        print("  - idx_account_address")
        print("  - idx_status")
        print("  - idx_account_status")
        print("  - uq_transaction_hash (unique)")
        return 0

    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
