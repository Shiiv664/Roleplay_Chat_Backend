"""Tests for the UserProfileRepository class."""

import pytest

from app.repositories.user_profile_repository import UserProfileRepository


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
