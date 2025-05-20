"""Tests for the UserProfileRepository class."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.application_settings import ApplicationSettings
from app.repositories.user_profile_repository import UserProfileRepository
from app.utils.exceptions import DatabaseError


class TestUserProfileRepository:
    """Test user profile repository functionality."""

    @pytest.fixture
    def create_profiles(self, db_session):
        """Create sample user profiles for testing."""
        repo = UserProfileRepository(db_session)

        profiles = [
            repo.create(
                label="profile1",
                name="User Profile 1",
                description="First test profile",
            ),
            repo.create(
                label="profile2",
                name="User Profile 2",
                description="Second test profile",
            ),
            repo.create(
                label="profile3",
                name="Special User",
                description="Third test profile with special keywords",
            ),
        ]

        db_session.commit()
        return profiles

    def test_get_by_label(self, db_session, create_profiles):
        """Test retrieving a user profile by label."""
        repo = UserProfileRepository(db_session)

        profile = repo.get_by_label("profile2")

        assert profile is not None
        assert profile.label == "profile2"
        assert profile.name == "User Profile 2"

    def test_get_by_label_not_found(self, db_session):
        """Test retrieving a non-existent user profile by label."""
        repo = UserProfileRepository(db_session)

        profile = repo.get_by_label("non_existent")

        assert profile is None

    def test_get_by_name(self, db_session, create_profiles):
        """Test finding user profiles by name."""
        repo = UserProfileRepository(db_session)

        # Exact match
        profiles = repo.get_by_name("User Profile 1")
        assert len(profiles) == 1
        assert profiles[0].label == "profile1"

        # Partial match
        profiles = repo.get_by_name("User Profile")
        assert len(profiles) == 2
        assert {p.label for p in profiles} == {"profile1", "profile2"}

        # Case insensitive
        profiles = repo.get_by_name("user PROFILE")
        assert len(profiles) == 2

        # No matches
        profiles = repo.get_by_name("Non-existent Profile")
        assert len(profiles) == 0

    def test_search(self, db_session, create_profiles):
        """Test searching user profiles by name or description."""
        repo = UserProfileRepository(db_session)

        # Search by name
        results = repo.search("Special User")
        assert len(results) == 1
        assert results[0].label == "profile3"

        # Search by description
        results = repo.search("special keywords")
        assert len(results) == 1
        assert results[0].label == "profile3"

        # Search with multiple matches
        results = repo.search("test profile")
        assert len(results) == 3

        # Search with no matches
        results = repo.search("no matches")
        assert len(results) == 0

    def test_get_default_profile(self, db_session, create_user_profile):
        """Test getting the default user profile."""
        repo = UserProfileRepository(db_session)

        # Create a user profile
        profile = create_user_profile(label="default_profile", name="Default Profile")
        db_session.add(profile)
        db_session.flush()

        # Create application settings with this profile as default
        settings = ApplicationSettings(default_user_profile_id=profile.id)
        db_session.add(settings)
        db_session.commit()

        # Get default profile
        default_profile = repo.get_default_profile()
        assert default_profile is not None
        assert default_profile.id == profile.id
        assert default_profile.label == "default_profile"

    def test_get_default_profile_not_found(self, db_session):
        """Test getting the default user profile when none is set."""
        repo = UserProfileRepository(db_session)

        # Get default profile without setting one
        default_profile = repo.get_default_profile()
        assert default_profile is None

    def test_database_error_in_get_default_profile(self, db_session):
        """Test handling of database errors in get_default_profile method."""
        repo = UserProfileRepository(db_session)

        # Mock session.query to raise SQLAlchemyError
        with patch.object(
            db_session, "query", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.get_default_profile()
