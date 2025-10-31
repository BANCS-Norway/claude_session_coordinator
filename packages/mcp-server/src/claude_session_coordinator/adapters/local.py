"""Local file storage adapter for Claude Session Coordinator.

This adapter stores data in JSON files on the local filesystem. Each scope
is stored as a separate JSON file in the configured directory (default: .claude/session-state/).
"""

import json
import os
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, cast

from .base import StorageAdapter, StorageError


class LocalFileAdapter(StorageAdapter):
    """Storage adapter that uses local JSON files.

    This adapter is ideal for single-machine use cases. Data is stored in
    JSON files, one file per scope. Scope names are converted to safe filenames
    by replacing `:` and `/` with `__`.

    Example:
        Scope: "laptop:BANCS-Norway/my-repo:session:claude_1"
        File: "laptop__BANCS-Norway__my-repo__session__claude_1.json"
    """

    def __init__(self, base_path: str = ".claude/session-state") -> None:
        """Initialize the local file adapter.

        Args:
            base_path: Directory where scope files will be stored
        """
        self.base_path = Path(base_path).resolve()
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the storage directory exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Failed to create storage directory: {e}") from e

    def _scope_to_filename(self, scope: str) -> str:
        """Convert a scope identifier to a safe filename.

        Args:
            scope: The scope identifier (e.g., "laptop:org/repo:session:id")

        Returns:
            Safe filename (e.g., "laptop__org__repo__session__id.json")
        """
        # Replace : and / with __
        safe_name = scope.replace(":", "__").replace("/", "__")
        return f"{safe_name}.json"

    def _filename_to_scope(self, filename: str) -> str:
        """Convert a filename back to a scope identifier.

        Args:
            filename: The filename (e.g., "laptop__org__repo__session__id.json")

        Returns:
            Scope identifier (e.g., "laptop:org/repo:session:id")
        """
        # Remove .json extension
        if filename.endswith(".json"):
            filename = filename[:-5]

        # This is a simplified conversion - we can't perfectly reconstruct
        # the original scope because we can't distinguish between : and /
        # For now, we'll convert __ back to : for all parts
        # This works for the standard scope format: machine:owner/repo:type:id
        parts = filename.split("__")

        # Reconstruct as machine:owner/repo:type:id
        if len(parts) >= 4:
            # Assume format: machine, owner, repo, type, id (and possibly more)
            machine = parts[0]
            owner = parts[1]
            repo = parts[2]
            rest = ":".join(parts[3:])
            return f"{machine}:{owner}/{repo}:{rest}"
        else:
            # Fallback: just join with :
            return ":".join(parts)

    def _get_scope_path(self, scope: str) -> Path:
        """Get the file path for a scope.

        Args:
            scope: The scope identifier

        Returns:
            Path to the scope file
        """
        return self.base_path / self._scope_to_filename(scope)

    def _load_scope_data(self, scope: str) -> dict[str, Any]:
        """Load data from a scope file.

        Args:
            scope: The scope identifier

        Returns:
            Dictionary containing the scope data, or empty dict if file doesn't exist
        """
        scope_path = self._get_scope_path(scope)
        if not scope_path.exists():
            return {}

        try:
            with open(scope_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cast(dict[str, Any], data)
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON in scope file {scope_path}: {e}") from e
        except OSError as e:
            raise StorageError(f"Failed to read scope file {scope_path}: {e}") from e

    def _save_scope_data(self, scope: str, data: dict[str, Any]) -> None:
        """Save data to a scope file.

        Args:
            scope: The scope identifier
            data: Dictionary to save

        Raises:
            StorageError: If save operation fails
        """
        scope_path = self._get_scope_path(scope)

        try:
            with open(scope_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except TypeError as e:
            raise StorageError(f"Value is not JSON-serializable: {e}") from e
        except OSError as e:
            raise StorageError(f"Failed to write scope file {scope_path}: {e}") from e

    def store(self, scope: str, key: str, value: Any) -> None:
        """Store a value in the specified scope and key."""
        # Load existing scope data
        scope_data = self._load_scope_data(scope)

        # Get current timestamp
        now = datetime.utcnow().isoformat()

        # Initialize data section if it doesn't exist
        if "data" not in scope_data:
            scope_data["data"] = {}

        # Initialize metadata section if it doesn't exist
        if "metadata" not in scope_data:
            scope_data["metadata"] = {}

        # Store the value
        scope_data["data"][key] = value

        # Update metadata
        if key not in scope_data["metadata"]:
            scope_data["metadata"][key] = {"created_at": now}
        scope_data["metadata"][key]["updated_at"] = now

        # Save the updated scope data
        self._save_scope_data(scope, scope_data)

    def retrieve(self, scope: str, key: str) -> Any | None:
        """Retrieve a value from the specified scope and key."""
        scope_data = self._load_scope_data(scope)
        return scope_data.get("data", {}).get(key)

    def delete(self, scope: str, key: str) -> bool:
        """Delete a specific key from a scope."""
        scope_data = self._load_scope_data(scope)

        # Check if key exists
        if "data" not in scope_data or key not in scope_data["data"]:
            return False

        # Delete the key and its metadata
        del scope_data["data"][key]
        if "metadata" in scope_data and key in scope_data["metadata"]:
            del scope_data["metadata"][key]

        # If scope is now empty, delete the file
        if not scope_data.get("data"):
            scope_path = self._get_scope_path(scope)
            try:
                scope_path.unlink(missing_ok=True)
            except OSError as e:
                raise StorageError(f"Failed to delete scope file {scope_path}: {e}") from e
        else:
            # Save the updated scope data
            self._save_scope_data(scope, scope_data)

        return True

    def list_keys(self, scope: str) -> list[str]:
        """List all keys in a scope."""
        scope_data = self._load_scope_data(scope)
        return list(scope_data.get("data", {}).keys())

    def list_scopes(self, pattern: str | None = None) -> list[str]:
        """List all scopes, optionally filtered by pattern."""
        try:
            # Get all .json files in the storage directory
            scope_files = [f.name for f in self.base_path.glob("*.json")]
        except OSError as e:
            raise StorageError(f"Failed to list scope files: {e}") from e

        # Convert filenames back to scope identifiers
        scopes = [self._filename_to_scope(f) for f in scope_files]

        # Filter by pattern if provided
        if pattern:
            scopes = [s for s in scopes if fnmatch(s, pattern)]

        return sorted(scopes)

    def delete_scope(self, scope: str) -> bool:
        """Delete an entire scope and all its keys."""
        scope_path = self._get_scope_path(scope)

        if not scope_path.exists():
            return False

        try:
            scope_path.unlink()
            return True
        except OSError as e:
            raise StorageError(f"Failed to delete scope file {scope_path}: {e}") from e

    def close(self) -> None:
        """Close the storage adapter and release resources.

        For the local file adapter, there are no persistent connections or
        resources to clean up, so this is a no-op.
        """
        pass
