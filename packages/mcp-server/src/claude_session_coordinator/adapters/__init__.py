"""Storage adapters for Claude Session Coordinator."""

from .base import StorageAdapter, StorageError
from .factory import AdapterFactory
from .local import LocalFileAdapter

__all__ = ["StorageAdapter", "StorageError", "AdapterFactory", "LocalFileAdapter"]
