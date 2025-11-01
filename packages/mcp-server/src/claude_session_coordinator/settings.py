"""Project-local settings management for adaptive storage selection.

This module handles .claude/settings.local.json which stores user preferences
for storage adapter selection on a per-project basis. These settings are
gitignored and override global configuration.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

# Type aliases for better type hints
AdapterType = Literal["local", "redis"]
CoordinationScope = Literal["single-machine", "multi-machine", "team"]


class Settings:
    """Manages project-local storage settings.

    Settings are stored in .claude/settings.local.json and include:
    - storage_adapter: Which adapter to use ("local" or "redis")
    - coordination_scope: User's coordination needs
    - decided_at: When the user made this choice
    - notes: Optional user notes about the decision
    """

    def __init__(self, settings_path: str | Path = ".claude/settings.local.json"):
        """Initialize settings manager.

        Args:
            settings_path: Path to settings file (default: .claude/settings.local.json)
        """
        self.settings_path = Path(settings_path)

    def exists(self) -> bool:
        """Check if settings file exists (first-run detection).

        Returns:
            True if settings file exists, False if this is first run
        """
        return self.settings_path.exists()

    def load(self) -> dict[str, Any] | None:
        """Load settings from file.

        Returns:
            Settings dictionary if file exists, None otherwise
        """
        if not self.exists():
            return None

        with open(self.settings_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result

    def save(
        self,
        storage_adapter: AdapterType,
        coordination_scope: CoordinationScope,
        notes: str = "",
    ) -> None:
        """Save settings to file.

        Args:
            storage_adapter: Adapter type ("local" or "redis")
            coordination_scope: User's coordination needs
            notes: Optional notes about the decision
        """
        # Ensure .claude directory exists
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        settings = {
            "storage_adapter": storage_adapter,
            "coordination_scope": coordination_scope,
            "decided_at": datetime.utcnow().isoformat() + "Z",
            "notes": notes,
        }

        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def update(
        self,
        storage_adapter: AdapterType | None = None,
        coordination_scope: CoordinationScope | None = None,
        notes: str | None = None,
    ) -> None:
        """Update existing settings (partial update).

        Args:
            storage_adapter: New adapter type (if changing)
            coordination_scope: New coordination scope (if changing)
            notes: New notes (if changing)

        Raises:
            FileNotFoundError: If settings file doesn't exist
        """
        current = self.load()
        if current is None:
            raise FileNotFoundError(
                "Settings file does not exist. Use save() for first-time setup."
            )

        # Update only provided fields
        if storage_adapter is not None:
            current["storage_adapter"] = storage_adapter
        if coordination_scope is not None:
            current["coordination_scope"] = coordination_scope
        if notes is not None:
            current["notes"] = notes

        # Update timestamp
        current["decided_at"] = datetime.utcnow().isoformat() + "Z"

        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)

    def get_adapter(self) -> AdapterType | None:
        """Get the configured storage adapter.

        Returns:
            Adapter type string, or None if not configured
        """
        settings = self.load()
        return settings.get("storage_adapter") if settings else None

    def get_coordination_scope(self) -> CoordinationScope | None:
        """Get the configured coordination scope.

        Returns:
            Coordination scope string, or None if not configured
        """
        settings = self.load()
        return settings.get("coordination_scope") if settings else None


def get_scope_description(scope: CoordinationScope) -> dict[str, Any]:
    """Get human-readable description of a coordination scope.

    Args:
        scope: The coordination scope type

    Returns:
        Dictionary with 'description' and 'best_for' keys
    """
    descriptions = {
        "single-machine": {
            "description": "Just you, working on this machine",
            "best_for": "Solo development on one computer",
            "adapter": "local",
            "setup_required": False,
        },
        "multi-machine": {
            "description": "You working across multiple machines (laptop + desktop)",
            "best_for": "Working from multiple locations",
            "adapter": "redis",
            "setup_required": True,
        },
        "team": {
            "description": "Multiple developers working together",
            "best_for": "Team projects with parallel work",
            "adapter": "redis",
            "setup_required": True,
        },
    }
    return descriptions[scope]


def get_adapter_info(adapter: AdapterType, config: dict[str, Any]) -> dict[str, Any]:
    """Get information about a storage adapter's availability and requirements.

    Args:
        adapter: The adapter type
        config: Current configuration from config.py

    Returns:
        Dictionary with adapter information including readiness status
    """
    if adapter == "local":
        return {
            "name": "local",
            "display_name": "Local File Storage",
            "ready": True,
            "capabilities": "Single-machine coordination only",
            "setup_required": False,
            "setup_instructions": None,
        }
    elif adapter == "redis":
        # Check if Redis is configured
        redis_config = config.get("storage", {}).get("config", {})
        redis_url = redis_config.get("redis_url") or redis_config.get("url")

        return {
            "name": "redis",
            "display_name": "Redis Storage",
            "ready": bool(redis_url),
            "capabilities": "Multi-machine + team coordination",
            "setup_required": not bool(redis_url),
            "setup_instructions": (
                "Configure REDIS_URL in config or environment variable" if not redis_url else None
            ),
        }
    else:
        return {
            "name": adapter,
            "display_name": adapter.title(),
            "ready": False,
            "capabilities": "Unknown",
            "setup_required": True,
            "setup_instructions": "Unknown adapter type",
        }


def recommend_adapter(scope: CoordinationScope) -> AdapterType:
    """Recommend an adapter based on coordination scope.

    Args:
        scope: User's coordination needs

    Returns:
        Recommended adapter type
    """
    if scope == "single-machine":
        return "local"
    else:  # multi-machine or team
        return "redis"
