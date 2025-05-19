"""Database initialization script.

This script initializes the database using SQLAlchemy models.
It creates all tables defined in the models and optionally loads sample data.
"""
import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the app package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.base import Base  # noqa
from app.utils.db import engine  # noqa


def init_db(load_sample_data: bool = False) -> None:
    """Initialize the database.

    Args:
        load_sample_data: Whether to load sample data after initialization.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    if load_sample_data:
        # Sample data loading will be implemented later
        # from scripts.generate_test_data import load_sample_data
        # load_sample_data()
        print("Sample data would be loaded here (not yet implemented).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Load sample data after initialization",
    )
    args = parser.parse_args()

    init_db(load_sample_data=args.sample_data)