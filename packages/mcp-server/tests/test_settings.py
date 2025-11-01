"""Tests for the settings module."""

import pytest

from claude_session_coordinator.settings import (
    Settings,
    get_adapter_info,
    get_scope_description,
    recommend_adapter,
)


@pytest.fixture
def temp_settings_file(tmp_path):
    """Create a temporary settings file path."""
    settings_file = tmp_path / ".claude" / "settings.local.json"
    return settings_file


@pytest.fixture
def settings_manager(temp_settings_file):
    """Create a Settings instance with a temporary file."""
    return Settings(temp_settings_file)


class TestSettings:
    """Tests for the Settings class."""

    def test_exists_returns_false_when_file_missing(self, settings_manager):
        """Test that exists() returns False when settings file doesn't exist."""
        assert not settings_manager.exists()

    def test_exists_returns_true_when_file_present(self, settings_manager):
        """Test that exists() returns True when settings file exists."""
        settings_manager.save(
            storage_adapter="local",
            coordination_scope="single-machine",
            notes="Test settings",
        )
        assert settings_manager.exists()

    def test_load_returns_none_when_file_missing(self, settings_manager):
        """Test that load() returns None when settings file doesn't exist."""
        assert settings_manager.load() is None

    def test_save_creates_directory(self, temp_settings_file, settings_manager):
        """Test that save() creates the .claude directory if it doesn't exist."""
        assert not temp_settings_file.parent.exists()

        settings_manager.save(
            storage_adapter="local",
            coordination_scope="single-machine",
            notes="Test",
        )

        assert temp_settings_file.parent.exists()

    def test_save_creates_valid_json(self, settings_manager):
        """Test that save() creates valid JSON with expected structure."""
        settings_manager.save(
            storage_adapter="redis",
            coordination_scope="team",
            notes="Team collaboration project",
        )

        settings = settings_manager.load()
        assert settings is not None
        assert settings["storage_adapter"] == "redis"
        assert settings["coordination_scope"] == "team"
        assert settings["notes"] == "Team collaboration project"
        assert "decided_at" in settings
        assert settings["decided_at"].endswith("Z")  # ISO format with UTC

    def test_update_changes_existing_settings(self, settings_manager):
        """Test that update() modifies existing settings."""
        # Create initial settings
        settings_manager.save(
            storage_adapter="local",
            coordination_scope="single-machine",
            notes="Initial",
        )

        # Update to different adapter
        settings_manager.update(
            storage_adapter="redis",
            coordination_scope="multi-machine",
        )

        settings = settings_manager.load()
        assert settings["storage_adapter"] == "redis"
        assert settings["coordination_scope"] == "multi-machine"
        assert settings["notes"] == "Initial"  # Notes unchanged

    def test_update_partial_changes(self, settings_manager):
        """Test that update() allows partial updates."""
        settings_manager.save(
            storage_adapter="local",
            coordination_scope="single-machine",
            notes="Initial",
        )

        # Update only notes
        settings_manager.update(notes="Updated notes")

        settings = settings_manager.load()
        assert settings["storage_adapter"] == "local"  # Unchanged
        assert settings["coordination_scope"] == "single-machine"  # Unchanged
        assert settings["notes"] == "Updated notes"  # Changed

    def test_update_raises_when_file_missing(self, settings_manager):
        """Test that update() raises FileNotFoundError when settings don't exist."""
        with pytest.raises(FileNotFoundError, match="Settings file does not exist"):
            settings_manager.update(storage_adapter="redis")

    def test_get_adapter(self, settings_manager):
        """Test get_adapter() returns the configured adapter."""
        settings_manager.save(
            storage_adapter="redis",
            coordination_scope="multi-machine",
        )

        assert settings_manager.get_adapter() == "redis"

    def test_get_adapter_returns_none_when_no_settings(self, settings_manager):
        """Test get_adapter() returns None when settings don't exist."""
        assert settings_manager.get_adapter() is None

    def test_get_coordination_scope(self, settings_manager):
        """Test get_coordination_scope() returns the configured scope."""
        settings_manager.save(
            storage_adapter="local",
            coordination_scope="single-machine",
        )

        assert settings_manager.get_coordination_scope() == "single-machine"

    def test_get_coordination_scope_returns_none_when_no_settings(self, settings_manager):
        """Test get_coordination_scope() returns None when settings don't exist."""
        assert settings_manager.get_coordination_scope() is None


class TestHelperFunctions:
    """Tests for helper functions in settings module."""

    def test_get_scope_description_single_machine(self):
        """Test get_scope_description() for single-machine."""
        desc = get_scope_description("single-machine")

        assert desc["adapter"] == "local"
        assert desc["setup_required"] is False
        assert "solo" in desc["best_for"].lower() or "one computer" in desc["best_for"].lower()

    def test_get_scope_description_multi_machine(self):
        """Test get_scope_description() for multi-machine."""
        desc = get_scope_description("multi-machine")

        assert desc["adapter"] == "redis"
        assert desc["setup_required"] is True
        assert "multiple machines" in desc["description"].lower()

    def test_get_scope_description_team(self):
        """Test get_scope_description() for team."""
        desc = get_scope_description("team")

        assert desc["adapter"] == "redis"
        assert desc["setup_required"] is True
        assert (
            "team" in desc["description"].lower()
            or "multiple developers" in desc["description"].lower()
        )

    def test_recommend_adapter_single_machine(self):
        """Test recommend_adapter() suggests local for single-machine."""
        assert recommend_adapter("single-machine") == "local"

    def test_recommend_adapter_multi_machine(self):
        """Test recommend_adapter() suggests redis for multi-machine."""
        assert recommend_adapter("multi-machine") == "redis"

    def test_recommend_adapter_team(self):
        """Test recommend_adapter() suggests redis for team."""
        assert recommend_adapter("team") == "redis"

    def test_get_adapter_info_local(self):
        """Test get_adapter_info() for local adapter."""
        config = {"storage": {"adapter": "local", "config": {"base_path": ".claude/session-state"}}}
        info = get_adapter_info("local", config)

        assert info["name"] == "local"
        assert info["ready"] is True
        assert info["setup_required"] is False
        assert "single-machine" in info["capabilities"].lower()

    def test_get_adapter_info_redis_configured(self):
        """Test get_adapter_info() for redis when configured."""
        config = {
            "storage": {"adapter": "redis", "config": {"redis_url": "redis://localhost:6379"}}
        }
        info = get_adapter_info("redis", config)

        assert info["name"] == "redis"
        assert info["ready"] is True
        assert info["setup_required"] is False
        assert (
            "multi-machine" in info["capabilities"].lower()
            or "team" in info["capabilities"].lower()
        )

    def test_get_adapter_info_redis_not_configured(self):
        """Test get_adapter_info() for redis when not configured."""
        config = {"storage": {"adapter": "local", "config": {}}}
        info = get_adapter_info("redis", config)

        assert info["name"] == "redis"
        assert info["ready"] is False
        assert info["setup_required"] is True
        assert info["setup_instructions"] is not None

    def test_get_adapter_info_unknown_adapter(self):
        """Test get_adapter_info() for unknown adapter type."""
        config = {"storage": {"adapter": "local", "config": {}}}
        info = get_adapter_info("unknown", config)  # type: ignore

        assert info["name"] == "unknown"
        assert info["ready"] is False
        assert "unknown" in info["capabilities"].lower()
