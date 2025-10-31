"""Configuration loading for Claude Session Coordinator."""

import json
import os
from pathlib import Path
from typing import Any, cast


def load_config() -> dict[str, Any]:
    """Load configuration from file or use defaults.

    Priority order:
    1. CLAUDE_SESSION_COORDINATOR_CONFIG environment variable (path to config file)
    2. ./.claude/session-coordinator-config.json (project-local)
    3. ~/.config/claude-session-coordinator/config.json (user-global)
    4. Built-in defaults

    Returns:
        Configuration dictionary with structure:
        {
            "storage": {
                "adapter": "local",
                "config": {"base_path": ".claude/session-state"}
            },
            "session": {
                "machine_id": "auto",
                "project_detection": "git"
            }
        }
    """
    # Try environment variable first
    env_config_path = os.environ.get("CLAUDE_SESSION_COORDINATOR_CONFIG")
    if env_config_path:
        config_file = Path(env_config_path)
        if config_file.exists():
            return _load_config_file(config_file)

    # Try project-local config
    project_config = Path(".claude/session-coordinator-config.json")
    if project_config.exists():
        return _load_config_file(project_config)

    # Try user-global config
    user_config = Path.home() / ".config" / "claude-session-coordinator" / "config.json"
    if user_config.exists():
        return _load_config_file(user_config)

    # Use built-in defaults
    return get_default_config()


def _load_config_file(config_path: Path) -> dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    with open(config_path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def get_default_config() -> dict[str, Any]:
    """Get the default configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        "storage": {"adapter": "local", "config": {"base_path": ".claude/session-state"}},
        "session": {
            "machine_id": "auto",  # "auto" = use hostname, or specify custom value
            "project_detection": "git",  # "git" or "directory"
        },
    }


def validate_config(config: dict[str, Any]) -> bool:
    """Validate configuration structure.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    if "storage" not in config:
        raise ValueError("Missing 'storage' section in config")

    if "adapter" not in config["storage"]:
        raise ValueError("Missing 'storage.adapter' in config")

    if "config" not in config["storage"]:
        raise ValueError("Missing 'storage.config' in config")

    # Validate adapter type is known
    valid_adapters = ["local", "redis"]  # Extend as new adapters are added
    adapter_type = config["storage"]["adapter"]
    if adapter_type not in valid_adapters:
        raise ValueError(
            f"Unknown adapter type: {adapter_type}. " f"Valid options: {', '.join(valid_adapters)}"
        )

    return True


def save_config(config: dict[str, Any], location: str = "project") -> None:
    """Save configuration to a file.

    Args:
        config: Configuration dictionary to save
        location: Where to save ("project" or "user")

    Raises:
        ValueError: If location is invalid or config is invalid
    """
    # Validate config before saving
    validate_config(config)

    if location == "project":
        config_dir = Path(".claude")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "session-coordinator-config.json"
    elif location == "user":
        config_dir = Path.home() / ".config" / "claude-session-coordinator"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
    else:
        raise ValueError(f"Invalid location: {location}. Must be 'project' or 'user'")

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
