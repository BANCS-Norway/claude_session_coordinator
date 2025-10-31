"""Comprehensive tests for configuration and detection modules."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from claude_session_coordinator.config import (
    get_default_config,
    load_config,
    save_config,
    validate_config,
)
from claude_session_coordinator.detection import (
    detect_machine_id,
    detect_project_id,
)


class TestConfigLoading:
    """Tests for configuration loading."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_home(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a temporary home directory for testing."""
        home_dir = temp_dir / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))
        return home_dir

    def test_get_default_config(self) -> None:
        """Test that default config has correct structure."""
        config = get_default_config()

        assert "storage" in config
        assert config["storage"]["adapter"] == "local"
        assert "base_path" in config["storage"]["config"]
        assert config["storage"]["config"]["base_path"] == ".claude/session-state"

        assert "session" in config
        assert config["session"]["machine_id"] == "auto"
        assert config["session"]["project_detection"] == "git"

    def test_load_config_returns_defaults_when_no_files(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that load_config returns defaults when no config files exist."""
        # Change to temp directory and clear env var
        monkeypatch.chdir(temp_dir)
        monkeypatch.delenv("CLAUDE_SESSION_COORDINATOR_CONFIG", raising=False)

        config = load_config()
        default = get_default_config()

        assert config == default

    def test_load_config_from_environment_variable(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading config from CLAUDE_SESSION_COORDINATOR_CONFIG env var."""
        config_file = temp_dir / "custom-config.json"
        custom_config = {
            "storage": {"adapter": "redis", "config": {"host": "localhost"}},
            "session": {"machine_id": "test-machine", "project_detection": "directory"},
        }

        config_file.write_text(json.dumps(custom_config))
        monkeypatch.setenv("CLAUDE_SESSION_COORDINATOR_CONFIG", str(config_file))

        config = load_config()

        assert config["storage"]["adapter"] == "redis"
        assert config["storage"]["config"]["host"] == "localhost"
        assert config["session"]["machine_id"] == "test-machine"
        assert config["session"]["project_detection"] == "directory"

    def test_load_config_from_project_local(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading config from .claude/session-coordinator-config.json."""
        monkeypatch.chdir(temp_dir)
        monkeypatch.delenv("CLAUDE_SESSION_COORDINATOR_CONFIG", raising=False)

        # Create project-local config
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        config_file = claude_dir / "session-coordinator-config.json"

        custom_config = {
            "storage": {"adapter": "local", "config": {"base_path": "/custom/path"}},
            "session": {"machine_id": "project-machine", "project_detection": "git"},
        }

        config_file.write_text(json.dumps(custom_config))

        config = load_config()

        assert config["storage"]["config"]["base_path"] == "/custom/path"
        assert config["session"]["machine_id"] == "project-machine"

    def test_load_config_from_user_global(
        self, temp_home: Path, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading config from ~/.config/claude-session-coordinator/config.json."""
        monkeypatch.chdir(temp_dir)
        monkeypatch.delenv("CLAUDE_SESSION_COORDINATOR_CONFIG", raising=False)

        # Create user-global config
        config_dir = temp_home / ".config" / "claude-session-coordinator"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"

        custom_config = {
            "storage": {"adapter": "local", "config": {"base_path": "~/sessions"}},
            "session": {"machine_id": "user-machine", "project_detection": "directory"},
        }

        config_file.write_text(json.dumps(custom_config))

        config = load_config()

        assert config["storage"]["config"]["base_path"] == "~/sessions"
        assert config["session"]["machine_id"] == "user-machine"

    def test_config_priority_env_over_project(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that env var config takes priority over project-local."""
        monkeypatch.chdir(temp_dir)

        # Create project-local config
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        project_config = claude_dir / "session-coordinator-config.json"
        project_config.write_text(
            json.dumps({"session": {"machine_id": "project-machine"}})
        )

        # Create env var config
        env_config_file = temp_dir / "env-config.json"
        env_config_file.write_text(json.dumps({"session": {"machine_id": "env-machine"}}))
        monkeypatch.setenv("CLAUDE_SESSION_COORDINATOR_CONFIG", str(env_config_file))

        config = load_config()

        # Env var should win
        assert config["session"]["machine_id"] == "env-machine"

    def test_config_priority_project_over_user(
        self, temp_home: Path, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that project-local config takes priority over user-global."""
        monkeypatch.chdir(temp_dir)
        monkeypatch.delenv("CLAUDE_SESSION_COORDINATOR_CONFIG", raising=False)

        # Create user-global config
        user_config_dir = temp_home / ".config" / "claude-session-coordinator"
        user_config_dir.mkdir(parents=True)
        user_config = user_config_dir / "config.json"
        user_config.write_text(json.dumps({"session": {"machine_id": "user-machine"}}))

        # Create project-local config
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        project_config = claude_dir / "session-coordinator-config.json"
        project_config.write_text(
            json.dumps({"session": {"machine_id": "project-machine"}})
        )

        config = load_config()

        # Project should win
        assert config["session"]["machine_id"] == "project-machine"

    def test_save_config_to_project(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test saving config to project-local location."""
        monkeypatch.chdir(temp_dir)

        custom_config = {
            "storage": {"adapter": "local", "config": {"base_path": "/test/path"}},
            "session": {"machine_id": "test-machine", "project_detection": "git"},
        }

        save_config(custom_config, location="project")

        # Verify file was created
        config_file = temp_dir / ".claude" / "session-coordinator-config.json"
        assert config_file.exists()

        # Verify contents
        saved_config = json.loads(config_file.read_text())
        assert saved_config == custom_config

    def test_save_config_to_user(
        self, temp_home: Path, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test saving config to user-global location."""
        monkeypatch.chdir(temp_dir)

        custom_config = {
            "storage": {"adapter": "redis", "config": {"host": "localhost"}},
            "session": {"machine_id": "my-machine", "project_detection": "directory"},
        }

        save_config(custom_config, location="user")

        # Verify file was created
        config_file = temp_home / ".config" / "claude-session-coordinator" / "config.json"
        assert config_file.exists()

        # Verify contents
        saved_config = json.loads(config_file.read_text())
        assert saved_config == custom_config

    def test_save_config_invalid_location(self) -> None:
        """Test that save_config raises ValueError for invalid location."""
        # First create a valid config for the invalid location test
        config = get_default_config()
        with pytest.raises(ValueError, match="Invalid location"):
            save_config(config, location="invalid")

    def test_validate_config_valid(self) -> None:
        """Test that validate_config accepts valid configuration."""
        config = get_default_config()
        assert validate_config(config) is True

    def test_validate_config_missing_storage(self) -> None:
        """Test that validate_config rejects config without storage section."""
        config: Dict[str, Any] = {"session": {}}
        with pytest.raises(ValueError, match="Missing 'storage' section"):
            validate_config(config)

    def test_validate_config_missing_adapter(self) -> None:
        """Test that validate_config rejects config without adapter."""
        config = {"storage": {"config": {}}}
        with pytest.raises(ValueError, match="Missing 'storage.adapter'"):
            validate_config(config)

    def test_validate_config_missing_storage_config(self) -> None:
        """Test that validate_config rejects config without storage.config."""
        config = {"storage": {"adapter": "local"}}
        with pytest.raises(ValueError, match="Missing 'storage.config'"):
            validate_config(config)

    def test_validate_config_invalid_adapter_type(self) -> None:
        """Test that validate_config rejects unknown adapter types."""
        config = {
            "storage": {
                "adapter": "unknown_adapter",
                "config": {}
            }
        }
        with pytest.raises(ValueError, match="Unknown adapter type"):
            validate_config(config)

    def test_save_config_validates_before_saving(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that save_config validates configuration before saving."""
        monkeypatch.chdir(temp_dir)

        invalid_config: Dict[str, Any] = {"invalid": "config"}

        with pytest.raises(ValueError, match="Missing 'storage' section"):
            save_config(invalid_config, location="project")


class TestMachineDetection:
    """Tests for machine ID detection."""

    def test_detect_machine_id_auto_uses_hostname(self) -> None:
        """Test that 'auto' setting uses socket.gethostname()."""
        config = {"session": {"machine_id": "auto"}}

        with patch("claude_session_coordinator.detection.socket.gethostname") as mock_hostname:
            mock_hostname.return_value = "test-laptop"
            machine_id = detect_machine_id(config)

        assert machine_id == "test-laptop"
        mock_hostname.assert_called_once()

    def test_detect_machine_id_custom_value(self) -> None:
        """Test that custom machine_id value is used."""
        config = {"session": {"machine_id": "my-custom-machine"}}

        machine_id = detect_machine_id(config)

        assert machine_id == "my-custom-machine"

    def test_detect_machine_id_missing_config_defaults_to_auto(self) -> None:
        """Test that missing machine_id config defaults to auto detection."""
        config: Dict[str, Any] = {}

        with patch("claude_session_coordinator.detection.socket.gethostname") as mock_hostname:
            mock_hostname.return_value = "default-machine"
            machine_id = detect_machine_id(config)

        assert machine_id == "default-machine"


class TestProjectDetection:
    """Tests for project ID detection."""

    def test_detect_project_from_git_ssh_format(self) -> None:
        """Test parsing project from SSH git remote URL."""
        config = {"session": {"project_detection": "git"}}
        git_output = "git@github.com:BANCS-Norway/claude_session_coordinator.git\n"

        with patch("claude_session_coordinator.detection.subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            project_id = detect_project_id(config)

        assert project_id == "BANCS-Norway/claude_session_coordinator"

    def test_detect_project_from_git_https_format(self) -> None:
        """Test parsing project from HTTPS git remote URL."""
        config = {"session": {"project_detection": "git"}}
        git_output = "https://github.com/BANCS-Norway/claude_session_coordinator.git\n"

        with patch("claude_session_coordinator.detection.subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            project_id = detect_project_id(config)

        assert project_id == "BANCS-Norway/claude_session_coordinator"

    def test_detect_project_from_git_http_format(self) -> None:
        """Test parsing project from HTTP git remote URL."""
        config = {"session": {"project_detection": "git"}}
        git_output = "http://github.com/owner/repo.git\n"

        with patch("claude_session_coordinator.detection.subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            project_id = detect_project_id(config)

        assert project_id == "owner/repo"

    def test_detect_project_from_git_without_dotgit(self) -> None:
        """Test parsing project URL without .git suffix."""
        config = {"session": {"project_detection": "git"}}
        git_output = "https://github.com/owner/repo\n"

        with patch("claude_session_coordinator.detection.subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            project_id = detect_project_id(config)

        assert project_id == "owner/repo"

    def test_detect_project_git_fallback_to_directory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that git detection falls back to directory name on failure."""
        config = {"session": {"project_detection": "git"}}

        with patch(
            "claude_session_coordinator.detection.subprocess.run"
        ) as mock_run, patch(
            "claude_session_coordinator.detection.Path.cwd"
        ) as mock_cwd:
            # Simulate git command failure
            from subprocess import CalledProcessError

            mock_run.side_effect = CalledProcessError(1, ["git"])
            mock_cwd.return_value = Path("/test/my-project")

            project_id = detect_project_id(config)

        assert project_id == "my-project"

    def test_detect_project_git_timeout_fallback(self) -> None:
        """Test that git timeout falls back to directory name."""
        config = {"session": {"project_detection": "git"}}

        with patch(
            "claude_session_coordinator.detection.subprocess.run"
        ) as mock_run, patch(
            "claude_session_coordinator.detection.Path.cwd"
        ) as mock_cwd:
            # Simulate git command timeout
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired(["git"], 5)
            mock_cwd.return_value = Path("/workspace/test-project")

            project_id = detect_project_id(config)

        assert project_id == "test-project"

    def test_detect_project_from_directory(self) -> None:
        """Test project detection from directory name."""
        config = {"session": {"project_detection": "directory"}}

        with patch("claude_session_coordinator.detection.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/home/user/my-awesome-project")
            project_id = detect_project_id(config)

        assert project_id == "my-awesome-project"

    def test_detect_project_invalid_detection_method(self) -> None:
        """Test that invalid detection method raises ValueError."""
        config = {"session": {"project_detection": "invalid-method"}}

        with pytest.raises(ValueError, match="Unknown project detection method"):
            detect_project_id(config)

    def test_detect_project_missing_config_defaults_to_git(self) -> None:
        """Test that missing project_detection defaults to git method."""
        config: Dict[str, Any] = {}
        git_output = "git@github.com:owner/repo.git\n"

        with patch("claude_session_coordinator.detection.subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            project_id = detect_project_id(config)

        assert project_id == "owner/repo"

    def test_detect_project_git_unparseable_url_fallback(self) -> None:
        """Test that unparseable git URL falls back to directory."""
        config = {"session": {"project_detection": "git"}}
        git_output = "weird://format/url\n"

        with patch(
            "claude_session_coordinator.detection.subprocess.run"
        ) as mock_run, patch(
            "claude_session_coordinator.detection.Path.cwd"
        ) as mock_cwd:
            mock_run.return_value.stdout = git_output
            mock_cwd.return_value = Path("/fallback/project-name")

            project_id = detect_project_id(config)

        assert project_id == "project-name"


class TestConfigDetectionIntegration:
    """Integration tests combining config and detection."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_full_workflow_with_defaults(self) -> None:
        """Test complete workflow using default configuration."""
        config = load_config()

        with patch("claude_session_coordinator.detection.socket.gethostname") as mock_hostname, patch(
            "claude_session_coordinator.detection.subprocess.run"
        ) as mock_git:
            mock_hostname.return_value = "my-laptop"
            mock_git.return_value.stdout = "git@github.com:org/repo.git\n"

            machine_id = detect_machine_id(config)
            project_id = detect_project_id(config)

        assert machine_id == "my-laptop"
        assert project_id == "org/repo"

    def test_full_workflow_with_custom_config(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test complete workflow with custom configuration."""
        monkeypatch.chdir(temp_dir)

        # Create custom config
        custom_config = {
            "storage": {"adapter": "local", "config": {"base_path": "/custom"}},
            "session": {"machine_id": "build-server", "project_detection": "directory"},
        }
        save_config(custom_config, location="project")

        # Load and use config
        config = load_config()

        with patch("claude_session_coordinator.detection.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/workspace/my-project")

            machine_id = detect_machine_id(config)
            project_id = detect_project_id(config)

        assert machine_id == "build-server"
        assert project_id == "my-project"
