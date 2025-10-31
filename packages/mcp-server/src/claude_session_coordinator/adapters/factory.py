"""Factory for creating storage adapters from configuration.

This module provides a factory pattern for creating storage adapters based on
configuration. It supports built-in adapters (local, redis) and allows users
to register custom adapter implementations.
"""

from collections.abc import Callable
from typing import Any

from .base import StorageAdapter, StorageError
from .local import LocalFileAdapter

# Type alias for adapter constructor functions
AdapterConstructor = Callable[[dict[str, Any]], StorageAdapter]


class AdapterFactory:
    """Factory for creating storage adapters.

    The factory maintains a registry of adapter types and creates instances
    based on configuration. Users can register custom adapters to extend
    functionality beyond the built-in adapters.

    Example:
        >>> factory = AdapterFactory()
        >>> config = {"adapter": "local", "config": {"base_path": ".claude/session-state"}}
        >>> adapter = factory.create_adapter(config)
    """

    # Built-in adapter registry
    _adapters: dict[str, AdapterConstructor] = {}

    @classmethod
    def register_adapter(cls, name: str, constructor: AdapterConstructor) -> None:
        """Register a custom adapter type.

        Args:
            name: The adapter type name (e.g., "local", "redis", "s3")
            constructor: Function that takes config dict and returns StorageAdapter instance

        Example:
            >>> def create_custom_adapter(config: dict) -> StorageAdapter:
            ...     return CustomAdapter(**config)
            >>> AdapterFactory.register_adapter("custom", create_custom_adapter)
        """
        cls._adapters[name] = constructor

    @classmethod
    def create_adapter(cls, config: dict[str, Any]) -> StorageAdapter:
        """Create a storage adapter from configuration.

        Args:
            config: Configuration dictionary containing:
                - adapter: Adapter type name (e.g., "local", "redis")
                - config: Adapter-specific configuration dictionary

        Returns:
            Configured StorageAdapter instance

        Raises:
            StorageError: If adapter type is unknown or creation fails

        Example:
            >>> config = {
            ...     "adapter": "local",
            ...     "config": {"base_path": ".claude/session-state"}
            ... }
            >>> adapter = AdapterFactory.create_adapter(config)
        """
        adapter_type = config.get("adapter")
        if not adapter_type:
            raise StorageError("Adapter type not specified in configuration")

        adapter_config = config.get("config", {})

        # Check registered adapters
        if adapter_type in cls._adapters:
            try:
                return cls._adapters[adapter_type](adapter_config)
            except Exception as e:
                raise StorageError(f"Failed to create adapter of type '{adapter_type}': {e}") from e

        # Unknown adapter type
        raise StorageError(
            f"Unknown adapter type: '{adapter_type}'. "
            f"Available types: {', '.join(cls._adapters.keys())}"
        )


# Register built-in adapters
def _create_local_adapter(config: dict[str, Any]) -> LocalFileAdapter:
    """Create a LocalFileAdapter from configuration."""
    base_path = config.get("base_path", ".claude/session-state")
    return LocalFileAdapter(base_path=base_path)


# Register the local adapter
AdapterFactory.register_adapter("local", _create_local_adapter)
