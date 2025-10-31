"""Base storage adapter interface for Claude Session Coordinator.

This module defines the abstract StorageAdapter interface that all storage
backends must implement. The adapter pattern allows seamless swapping between
different storage backends (local files, Redis, custom implementations) without
changing client code.
"""

from abc import ABC, abstractmethod
from typing import Any


class StorageAdapter(ABC):
    """Abstract base class for storage adapters.

    All storage adapters must implement this interface to ensure compatibility
    with the MCP server. The interface provides key-value storage with scope
    support for organizing data.

    Scopes follow the format: {machine}:{owner/repo}:{type}:{id}
    Example: laptop:BANCS-Norway/my-repo:session:claude_1
    """

    @abstractmethod
    def store(self, scope: str, key: str, value: Any) -> None:
        """Store a value in the specified scope and key.

        Args:
            scope: The scope identifier (e.g., "laptop:org/repo:session:claude_1")
            key: The key within the scope
            value: Any JSON-serializable value to store

        Raises:
            ValueError: If the value is not JSON-serializable
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def retrieve(self, scope: str, key: str) -> Any | None:
        """Retrieve a value from the specified scope and key.

        Args:
            scope: The scope identifier
            key: The key within the scope

        Returns:
            The stored value, or None if the key doesn't exist

        Raises:
            StorageError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def delete(self, scope: str, key: str) -> bool:
        """Delete a specific key from a scope.

        Args:
            scope: The scope identifier
            key: The key to delete

        Returns:
            True if the key was deleted, False if it didn't exist

        Raises:
            StorageError: If deletion operation fails
        """
        pass

    @abstractmethod
    def list_keys(self, scope: str) -> list[str]:
        """List all keys in a scope.

        Args:
            scope: The scope identifier

        Returns:
            List of key names in the scope (empty list if scope doesn't exist)

        Raises:
            StorageError: If listing operation fails
        """
        pass

    @abstractmethod
    def list_scopes(self, pattern: str | None = None) -> list[str]:
        """List all scopes, optionally filtered by pattern.

        Args:
            pattern: Optional glob-style pattern to filter scopes
                    (e.g., "laptop:*:session:*" or "*:BANCS-Norway/*:*:*")
                    If None, returns all scopes

        Returns:
            List of scope identifiers matching the pattern

        Raises:
            StorageError: If listing operation fails
        """
        pass

    @abstractmethod
    def delete_scope(self, scope: str) -> bool:
        """Delete an entire scope and all its keys.

        Args:
            scope: The scope identifier to delete

        Returns:
            True if the scope was deleted, False if it didn't exist

        Raises:
            StorageError: If deletion operation fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the storage adapter and release resources.

        This method should be called when the adapter is no longer needed.
        It should clean up connections, file handles, or other resources.
        """
        pass


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass
