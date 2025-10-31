# Claude Session Coordinator - Phase 1 Implementation Plan

## Prerequisites

- Python 3.10+
- MCP SDK: `pip install mcp`
- Project structure created

## Project Structure

```
claude-session-coordinator/
├── pyproject.toml              # Package metadata
├── README.md                   # User documentation
├── src/
│   └── claude_session_coordinator/
│       ├── __init__.py
│       ├── __main__.py         # Entry point
│       ├── server.py           # MCP server implementation
│       ├── config.py           # Configuration loading
│       ├── detection.py        # Machine/project detection
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py         # StorageAdapter interface
│       │   ├── local.py        # LocalFileAdapter
│       │   └── factory.py      # AdapterFactory
│       └── tools/
│           ├── __init__.py
│           ├── session.py      # sign_on, sign_off
│           ├── data.py         # store, retrieve, delete
│           └── discovery.py    # list_keys, list_scopes
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_adapters.py        # Adapter tests
│   ├── test_detection.py       # Detection logic tests
│   └── test_tools.py           # MCP tools tests
└── examples/
    ├── basic-usage.md
    ├── instance-coordination.md
    └── config.example.json
```

## Implementation Phases

### Phase 1.1: Core Storage Layer

**Tasks:**
1. Create project structure
2. Implement `StorageAdapter` base class
3. Implement `LocalFileAdapter`
4. Implement `AdapterFactory`
5. Write adapter tests

**Files to create:**
- `src/claude_session_coordinator/adapters/base.py`
- `src/claude_session_coordinator/adapters/local.py`
- `src/claude_session_coordinator/adapters/factory.py`
- `tests/test_adapters.py`

**Acceptance criteria:**
- All adapter methods work correctly
- Tests pass for local file adapter
- Can store, retrieve, delete data
- Can list keys and scopes
- Pattern matching works for `list_scopes()`

### Phase 1.2: Configuration & Detection

**Tasks:**
1. Implement configuration loader
2. Implement machine ID detection
3. Implement project detection (git)
4. Write detection tests

**Files to create:**
- `src/claude_session_coordinator/config.py`
- `src/claude_session_coordinator/detection.py`
- `tests/test_detection.py`

**Acceptance criteria:**
- Config loads from file or defaults
- Machine ID detected from hostname
- Project detected from git remote
- Fallback mechanisms work
- Tests cover all detection paths

### Phase 1.3: MCP Server & Tools

**Tasks:**
1. Implement MCP server initialization
2. Implement `sign_on()` tool
3. Implement data tools (`store_data`, `retrieve_data`, `delete_data`)
4. Implement discovery tools (`list_keys`, `list_scopes`)
5. Implement `sign_off()` tool
6. Implement MCP resources (`session://context`, `session://state/{id}`)
7. Implement MCP prompts (`startup`, `sign-off`)
8. Add rich tool descriptions
9. Write tool integration tests

**Files to create:**
- `src/claude_session_coordinator/server.py`
- `src/claude_session_coordinator/tools/session.py`
- `src/claude_session_coordinator/tools/data.py`
- `src/claude_session_coordinator/tools/discovery.py`
- `src/claude_session_coordinator/resources.py`
- `src/claude_session_coordinator/prompts.py`
- `tests/test_tools.py`
- `tests/test_resources.py`

**Acceptance criteria:**
- All 8 tools work via MCP
- `sign_on()` establishes session context
- Tools auto-prefix scopes with machine:project
- `sign_off()` releases session properly
- Resources provide current state (context, session states)
- Prompts guide Claude through startup and sign-off
- Tool descriptions explain usage clearly
- Claude can automatically understand workflow from server
- Tests cover all tool and resource functionality

### Phase 1.4: CLI & Entry Point

**Tasks:**
1. Create CLI entry point
2. Implement server startup
3. Add version command
4. Add config validation command

**Files to create:**
- `src/claude_session_coordinator/__main__.py`

**Acceptance criteria:**
- Can run: `python -m claude_session_coordinator`
- Server starts and listens
- Version info displays correctly
- Config validation works

### Phase 1.5: Documentation

**Tasks:**
1. Write comprehensive README
2. Write API reference
3. Write usage examples
4. Write troubleshooting guide
5. Document configuration options

**Files to create:**
- `README.md`
- `docs/API.md`
- `examples/basic-usage.md`
- `examples/instance-coordination.md`
- `examples/config.example.json`

**Acceptance criteria:**
- Installation instructions clear
- All tools documented with examples
- Configuration options explained
- Common use cases covered
- Troubleshooting section complete

### Phase 1.6: Packaging & Distribution

**Tasks:**
1. Configure pyproject.toml
2. Test installation locally
3. Test in fresh environment
4. Publish to PyPI (test first)
5. Verify pip installation works

**Files to create:**
- `pyproject.toml`
- `LICENSE`
- `.gitignore`

**Acceptance criteria:**
- `pip install claude-session-coordinator` works
- Command available after install
- Works in Claude Code, VS Code, Cursor
- No missing dependencies

## Detailed Implementation Guide

### Step 1: Create base.py (StorageAdapter Interface)

```python
# src/claude_session_coordinator/adapters/base.py

from abc import ABC, abstractmethod
from typing import Any, Optional, List

class StorageAdapter(ABC):
    """Base interface for all storage backends"""

    @abstractmethod
    def store(self, scope: str, key: str, value: Any) -> None:
        """Store a value in the given scope

        Args:
            scope: The scope identifier (e.g., "machine:project:type:id")
            key: The key within the scope
            value: The value to store (must be JSON-serializable)
        """
        pass

    @abstractmethod
    def retrieve(self, scope: str, key: str) -> Optional[Any]:
        """Retrieve a value from a scope

        Args:
            scope: The scope identifier
            key: The key to retrieve

        Returns:
            The stored value, or None if not found
        """
        pass

    @abstractmethod
    def delete(self, scope: str, key: str) -> bool:
        """Delete a key from a scope

        Args:
            scope: The scope identifier
            key: The key to delete

        Returns:
            True if the key existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    def list_keys(self, scope: str) -> List[str]:
        """List all keys in a scope

        Args:
            scope: The scope identifier

        Returns:
            List of key names in the scope
        """
        pass

    @abstractmethod
    def list_scopes(self, pattern: Optional[str] = None) -> List[str]:
        """List all scopes, optionally filtered by pattern

        Args:
            pattern: Optional glob pattern (e.g., "machine:*/session:*")

        Returns:
            List of scope identifiers
        """
        pass

    @abstractmethod
    def delete_scope(self, scope: str) -> bool:
        """Delete an entire scope

        Args:
            scope: The scope identifier to delete

        Returns:
            True if the scope existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Cleanup resources (connections, file handles, etc.)"""
        pass
```

### Step 2: Create local.py (LocalFileAdapter)

See architecture document for full implementation. Key points:

- Store scopes as JSON files in `.claude/session-state/`
- Use `__` to replace `:` and `/` in filenames
- Include metadata (timestamps) in files
- Implement pattern matching for `list_scopes()`

### Step 3: Create factory.py (AdapterFactory)

```python
# src/claude_session_coordinator/adapters/factory.py

from typing import Dict, Any
from .base import StorageAdapter
from .local import LocalFileAdapter

class AdapterFactory:
    """Creates storage adapters based on configuration"""

    _adapters = {
        "local": LocalFileAdapter,
        # Future: "redis": RedisAdapter, etc.
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> StorageAdapter:
        """Create adapter from configuration

        Args:
            config: Full configuration dict

        Returns:
            Instantiated storage adapter

        Raises:
            ValueError: If adapter type is unknown
        """
        storage_config = config.get("storage", {})
        adapter_type = storage_config.get("adapter", "local")
        adapter_config = storage_config.get("config", {})

        if adapter_type not in cls._adapters:
            raise ValueError(
                f"Unknown adapter type: {adapter_type}. "
                f"Available: {list(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[adapter_type]
        return adapter_class(**adapter_config)

    @classmethod
    def register_adapter(cls, name: str, adapter_class: type):
        """Register a custom adapter

        Args:
            name: Adapter name for configuration
            adapter_class: Adapter class (must inherit from StorageAdapter)
        """
        if not issubclass(adapter_class, StorageAdapter):
            raise TypeError(f"{adapter_class} must inherit from StorageAdapter")
        cls._adapters[name] = adapter_class
```

### Step 4: Create config.py (Configuration Loader)

```python
# src/claude_session_coordinator/config.py

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG = {
    "storage": {
        "adapter": "local",
        "config": {
            "base_path": ".claude/session-state"
        }
    },
    "session": {
        "machine_id": "auto",
        "project_detection": "git"
    }
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or environment

    Priority order:
    1. Explicit config_path argument
    2. CLAUDE_SESSION_COORDINATOR_CONFIG environment variable
    3. ./.claude/session-coordinator-config.json (project-local)
    4. ~/.config/claude-session-coordinator/config.json (user-global)
    5. Built-in defaults

    Args:
        config_path: Optional explicit path to config file

    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    # Determine config file path
    if config_path:
        path = Path(config_path)
    elif "CLAUDE_SESSION_COORDINATOR_CONFIG" in os.environ:
        path = Path(os.environ["CLAUDE_SESSION_COORDINATOR_CONFIG"])
    else:
        # Check project-local first
        project_local = Path(".claude/session-coordinator-config.json")
        user_global = Path.home() / ".config" / "claude-session-coordinator" / "config.json"

        if project_local.exists():
            path = project_local
        elif user_global.exists():
            path = user_global
        else:
            # Use defaults
            return config

    # Load and merge with defaults
    if path.exists():
        with open(path) as f:
            user_config = json.load(f)
            config.update(user_config)

    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure

    Args:
        config: Configuration dictionary

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    if "storage" not in config:
        raise ValueError("Missing 'storage' section in config")

    if "adapter" not in config["storage"]:
        raise ValueError("Missing 'storage.adapter' in config")

    # Add more validation as needed

    return True
```

### Step 5: Create detection.py (Machine/Project Detection)

See architecture document for full implementation. Key points:

- Machine ID from hostname or config
- Project from git remote URL parsing
- Fallbacks for non-git projects
- Test coverage for edge cases

### Step 6: Create MCP Server & Tools

```python
# src/claude_session_coordinator/server.py

from mcp.server import Server
from mcp.types import Tool
from .config import load_config
from .adapters.factory import AdapterFactory
from .detection import detect_machine_id, detect_project_id
from .tools.session import create_session_tools
from .tools.data import create_data_tools
from .tools.discovery import create_discovery_tools

def create_server() -> Server:
    """Create and configure the MCP server"""

    # Initialize server
    app = Server("claude-session-coordinator")

    # Load configuration
    config = load_config()

    # Create storage adapter
    storage = AdapterFactory.create(config)

    # Detect machine and project
    machine_id = detect_machine_id(config)
    project_id = detect_project_id(config)

    # Session state (global to this server instance)
    session_state = {
        "current_session": None,
        "machine_id": machine_id,
        "project_id": project_id,
        "storage": storage
    }

    # Register all tools
    create_session_tools(app, session_state)
    create_data_tools(app, session_state)
    create_discovery_tools(app, session_state)

    return app
```

### Step 7: Testing Strategy

```python
# tests/conftest.py

import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def local_adapter(temp_dir):
    """Local file adapter for testing"""
    from claude_session_coordinator.adapters.local import LocalFileAdapter
    return LocalFileAdapter(str(temp_dir / "session-state"))

# tests/test_adapters.py

def test_store_and_retrieve(local_adapter):
    local_adapter.store("test:scope", "key1", "value1")
    assert local_adapter.retrieve("test:scope", "key1") == "value1"

def test_store_complex_types(local_adapter):
    data = {"nested": {"array": [1, 2, 3]}, "bool": True}
    local_adapter.store("test:scope", "complex", data)
    retrieved = local_adapter.retrieve("test:scope", "complex")
    assert retrieved == data

def test_list_keys(local_adapter):
    local_adapter.store("test:scope", "key1", "val1")
    local_adapter.store("test:scope", "key2", "val2")
    keys = local_adapter.list_keys("test:scope")
    assert set(keys) == {"key1", "key2"}

def test_list_scopes_with_pattern(local_adapter):
    local_adapter.store("machine1:project:session:1", "k", "v")
    local_adapter.store("machine2:project:session:2", "k", "v")
    local_adapter.store("machine1:other:session:3", "k", "v")

    all_scopes = local_adapter.list_scopes()
    assert len(all_scopes) == 3

    filtered = local_adapter.list_scopes("machine1:*")
    assert len(filtered) == 2
```

## Timeline Estimate

**Phase 1.1** - Core Storage: 2-3 days
**Phase 1.2** - Config & Detection: 1-2 days
**Phase 1.3** - MCP Server, Tools, Resources & Prompts: 4-5 days
**Phase 1.4** - CLI & Entry Point: 1 day
**Phase 1.5** - Documentation: 2-3 days
**Phase 1.6** - Packaging: 1-2 days

**Total:** 11-16 days for complete Phase 1

## Success Criteria

- [ ] All 8 MCP tools implemented and tested
- [ ] MCP resources provide session context and state
- [ ] MCP prompts guide Claude through startup and sign-off
- [ ] Tool descriptions are comprehensive and helpful
- [ ] Claude can self-discover workflow from server
- [ ] LocalFileAdapter works correctly
- [ ] Configuration system works (file, env var, defaults)
- [ ] Machine and project detection works
- [ ] Can install via `pip install claude-session-coordinator`
- [ ] Works in Claude Code, VS Code, and Cursor
- [ ] Comprehensive documentation
- [ ] Example use cases provided
- [ ] All tests pass (>90% coverage)
- [ ] No external dependencies beyond MCP SDK

## Next Steps

After Phase 1 is complete and stable:

**Phase 2 - Redis Adapter:**
- Implement RedisAdapter
- Add atomic operations
- Add TTL support
- Add pub/sub notifications

**Phase 3 - Advanced Features:**
- S3 adapter for cloud storage
- Admin CLI for diagnostics
- Migration tool between adapters
- Performance optimizations

**Phase 4 - Enterprise:**
- PostgreSQL adapter
- Multi-tenancy support
- Audit logging
- Web dashboard
