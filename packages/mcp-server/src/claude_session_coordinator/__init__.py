"""Claude Session Coordinator - MCP server for multi-session coordination.

This package provides an MCP server that enables multiple Claude AI sessions
to coordinate work across machines through flexible storage adapters.
"""

from .adapters import AdapterFactory, LocalFileAdapter, StorageAdapter, StorageError
from .config import get_default_config, load_config, save_config, validate_config
from .detection import detect_machine_id, detect_project_id

# from .server import app, initialize_server, main  # Temporarily disabled for issue #4 testing

__version__ = "0.1.0"

__all__ = [
    # Storage adapters
    "StorageAdapter",
    "LocalFileAdapter",
    "AdapterFactory",
    "StorageError",
    # Configuration
    "load_config",
    "get_default_config",
    "save_config",
    "validate_config",
    # Detection
    "detect_machine_id",
    "detect_project_id",
    # Server (temporarily disabled for issue #4 testing)
    # "app",
    # "initialize_server",
    # "main",
]
