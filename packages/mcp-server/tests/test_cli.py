"""Tests for the CLI entry point."""

import pytest
from unittest.mock import patch, MagicMock
from claude_session_coordinator.__main__ import (
    create_parser,
    validate_config,
    cli_main,
)


class TestCLIParser:
    """Tests for the argument parser."""

    def test_parser_creation(self):
        """Test that the parser is created correctly."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "claude-session-coordinator"

    def test_parser_help(self):
        """Test that --help works."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_parser_version(self):
        """Test that --version works."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_parser_validate_config(self):
        """Test that --validate-config flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["--validate-config"])
        assert args.validate_config is True

    def test_parser_verbose(self):
        """Test that -v/--verbose flag is recognized."""
        parser = create_parser()

        # Test short form
        args = parser.parse_args(["-v"])
        assert args.verbose is True

        # Test long form
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_parser_defaults(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.validate_config is False
        assert args.verbose is False


class TestValidateConfig:
    """Tests for configuration validation."""

    def test_validate_config_with_defaults(self, monkeypatch):
        """Test validating default configuration."""
        # Mock load_config to return default config
        from claude_session_coordinator.config import get_default_config

        mock_config = get_default_config()
        monkeypatch.setattr(
            "claude_session_coordinator.__main__.load_config",
            lambda: mock_config
        )

        # Should succeed with default config
        result = validate_config()
        assert result == 0

    def test_validate_config_missing_storage(self, monkeypatch):
        """Test validation fails with missing storage section."""
        # Mock load_config to return invalid config
        mock_config = {"session": {}}
        monkeypatch.setattr(
            "claude_session_coordinator.__main__.load_config",
            lambda: mock_config
        )

        result = validate_config()
        assert result == 1

    def test_validate_config_missing_adapter(self, monkeypatch):
        """Test validation fails with missing adapter specification."""
        mock_config = {"storage": {}}
        monkeypatch.setattr(
            "claude_session_coordinator.__main__.load_config",
            lambda: mock_config
        )

        result = validate_config()
        assert result == 1

    def test_validate_config_file_not_found(self, monkeypatch):
        """Test validation handles missing config file gracefully."""
        def raise_not_found():
            raise FileNotFoundError("Config not found")

        monkeypatch.setattr(
            "claude_session_coordinator.__main__.load_config",
            raise_not_found
        )

        # Should return 0 (uses defaults) when config file not found
        result = validate_config()
        assert result == 0

    def test_validate_config_with_session_settings(self, monkeypatch):
        """Test validation includes session configuration."""
        from claude_session_coordinator.config import get_default_config

        mock_config = get_default_config()
        mock_config["session"] = {
            "machine_id": "test-machine",
            "project_detection": "directory"
        }

        monkeypatch.setattr(
            "claude_session_coordinator.__main__.load_config",
            lambda: mock_config
        )

        result = validate_config()
        assert result == 0


class TestCLIMain:
    """Tests for the main CLI entry point."""

    def test_cli_main_validate_config(self, monkeypatch):
        """Test CLI with --validate-config argument."""
        # Mock validate_config to return success
        monkeypatch.setattr(
            "claude_session_coordinator.__main__.validate_config",
            lambda: 0
        )

        result = cli_main(["--validate-config"])
        assert result == 0

    def test_cli_main_version(self):
        """Test CLI with --version argument."""
        with pytest.raises(SystemExit) as exc_info:
            cli_main(["--version"])
        assert exc_info.value.code == 0

    @patch("claude_session_coordinator.__main__.asyncio.run")
    def test_cli_main_run_server(self, mock_asyncio_run):
        """Test CLI runs server by default."""
        mock_asyncio_run.return_value = None

        result = cli_main([])

        assert result == 0
        mock_asyncio_run.assert_called_once()

    @patch("claude_session_coordinator.__main__.asyncio.run")
    def test_cli_main_verbose(self, mock_asyncio_run, capsys):
        """Test CLI with verbose flag."""
        mock_asyncio_run.return_value = None

        result = cli_main(["--verbose"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Starting Claude Session Coordinator" in captured.err

    @patch("claude_session_coordinator.__main__.asyncio.run")
    def test_cli_main_keyboard_interrupt(self, mock_asyncio_run, capsys):
        """Test CLI handles KeyboardInterrupt gracefully."""
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        result = cli_main([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Shutting down" in captured.err

    @patch("claude_session_coordinator.__main__.asyncio.run")
    def test_cli_main_exception(self, mock_asyncio_run, capsys):
        """Test CLI handles exceptions."""
        mock_asyncio_run.side_effect = RuntimeError("Test error")

        result = cli_main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("claude_session_coordinator.__main__.asyncio.run")
    def test_cli_main_exception_verbose(self, mock_asyncio_run, capsys):
        """Test CLI shows traceback with verbose flag."""
        mock_asyncio_run.side_effect = RuntimeError("Test error")

        result = cli_main(["--verbose"])

        assert result == 1
        captured = capsys.readouterr()
        assert "Traceback" in captured.err or "RuntimeError" in captured.err
