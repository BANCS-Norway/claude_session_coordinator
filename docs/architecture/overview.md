# Claude Session Coordinator - Architecture Design

## Overview

The Session Coordinator MCP server enables multiple Claude AI sessions to
share state and coordinate work across machines. It uses a **storage adapter
pattern** to support multiple backend implementations.

## Core Design Principles

1. **Storage Agnostic** - Swap backends without changing client code
2. **Future-Proof Scoping** - Include machine:project in data model from day one
3. **Simple Phase 1** - Start with local files, no external dependencies
4. **Clear Migration Path** - Easy upgrade to Redis/cloud storage later
5. **Self-Documenting** - MCP resources and prompts guide Claude automatically

## Storage Adapter Architecture

### Interface Design

All storage backends implement the same interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Optional, List

class StorageAdapter(ABC):
    """Base interface for all storage backends"""

    @abstractmethod
    def store(self, scope: str, key: str, value: Any) -> None:
        """Store a value in the given scope"""
        pass

    @abstractmethod
    def retrieve(self, scope: str, key: str) -> Optional[Any]:
        """Retrieve a value, returns None if not found"""
        pass

    @abstractmethod
    def delete(self, scope: str, key: str) -> bool:
        """Delete a key, returns True if existed"""
        pass

    @abstractmethod
    def list_keys(self, scope: str) -> List[str]:
        """List all keys in a scope"""
        pass

    @abstractmethod
    def list_scopes(self, pattern: Optional[str] = None) -> List[str]:
        """List all scopes, optionally filtered by pattern"""
        pass

    @abstractmethod
    def delete_scope(self, scope: str) -> bool:
        """Delete entire scope, returns True if existed"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Cleanup resources"""
        pass
```

### Configuration Format

**config.json:**

```json
{
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
```

**For Redis (future):**

```json
{
  "storage": {
    "adapter": "redis",
    "config": {
      "url": "redis://localhost:6379/0",
      "prefix": "claude-sessions:",
      "ttl": 86400
    }
  },
  "session": {
    "machine_id": "auto",
    "project_detection": "git"
  }
}
```

**For S3 (future):**

```json
{
  "storage": {
    "adapter": "s3",
    "config": {
      "bucket": "my-claude-sessions",
      "region": "us-east-1",
      "prefix": "sessions/"
    }
  }
}
```

## Scope Format

All scopes follow the pattern:

```text
{machine}:{owner}/{repo}:{scope_type}:{scope_id}
```

**Examples:**

```text
my-laptop:BANCS-Norway/claude_session_cordinator:session:claude_1
my-laptop:BANCS-Norway/claude_session_cordinator:instances
desktop:BANCS-Norway/claude_session_cordinator:issue:15
aws-vm-1:nxtl/project:session:claude_2
```

**Components:**

- `machine` - Hostname or configured machine identifier
- `owner/repo` - From git remote URL (e.g.,
  `BANCS-Norway/claude_session_cordinator`)
- `scope_type` - Logical grouping (session, issue, instances, etc.)
- `scope_id` - Specific identifier (optional for global scopes like
  "instances")

**Benefits:**

- Phase 1: All scopes on same machine, works locally
- Future: Multiple machines coordinate via shared storage (Redis)
- Easy filtering: `list_scopes("my-laptop:*")` or
  `list_scopes("*:BANCS-Norway/*:session:*")`

## Phase 1: Local File Adapter

### Implementation

**File structure:**

```text
.claude/session-state/
  my-laptop__BANCS-Norway__claude_session_cordinator__session__claude_1.json
  my-laptop__BANCS-Norway__claude_session_cordinator__session__claude_2.json
  my-laptop__BANCS-Norway__claude_session_cordinator__instances.json
```

**File naming:**

- Scope separators (`:`, `/`) replaced with `__` for filesystem safety
- One JSON file per scope
- File contains: `{"data": {key: value, ...}, "metadata": {...}}`

**Example file content:**

```json
{
  "scope": "my-laptop:BANCS-Norway/claude_session_cordinator:session:claude_1",
  "data": {
    "current_issue": 15,
    "status": "in_progress",
    "todos": [
      {"task": "Implement storage adapter", "status": "in_progress"},
      {"task": "Write tests", "status": "pending"}
    ]
  },
  "metadata": {
    "created_at": "2025-10-31T09:00:00Z",
    "updated_at": "2025-10-31T10:23:45Z"
  }
}
```

### LocalFileAdapter Implementation

```python
import json
import os
from pathlib import Path
from typing import Any, Optional, List
from datetime import datetime
import fnmatch

class LocalFileAdapter(StorageAdapter):
    def __init__(self, base_path: str = ".claude/session-state"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _scope_to_filename(self, scope: str) -> Path:
        """Convert scope to safe filename"""
        safe_name = scope.replace(":", "__").replace("/", "__")
        return self.base_path / f"{safe_name}.json"

    def _filename_to_scope(self, filepath: Path) -> str:
        """Convert filename back to scope"""
        name = filepath.stem  # Remove .json
        return name.replace("__", ":")

    def _read_scope_file(self, scope: str) -> dict:
        """Read entire scope file"""
        filepath = self._scope_to_filename(scope)
        if not filepath.exists():
            return {"scope": scope, "data": {}, "metadata": {}}

        with open(filepath, 'r') as f:
            return json.load(f)

    def _write_scope_file(self, scope: str, data: dict,
                          update_timestamp: bool = True):
        """Write entire scope file"""
        filepath = self._scope_to_filename(scope)

        scope_data = self._read_scope_file(scope)
        scope_data["data"] = data

        if update_timestamp:
            now = datetime.utcnow().isoformat() + "Z"
            scope_data["metadata"]["updated_at"] = now
            if "created_at" not in scope_data["metadata"]:
                scope_data["metadata"]["created_at"] = \
                    scope_data["metadata"]["updated_at"]

        with open(filepath, 'w') as f:
            json.dump(scope_data, f, indent=2)

    def store(self, scope: str, key: str, value: Any) -> None:
        scope_file = self._read_scope_file(scope)
        scope_file["data"][key] = value
        self._write_scope_file(scope, scope_file["data"])

    def retrieve(self, scope: str, key: str) -> Optional[Any]:
        scope_file = self._read_scope_file(scope)
        return scope_file["data"].get(key)

    def delete(self, scope: str, key: str) -> bool:
        scope_file = self._read_scope_file(scope)
        if key in scope_file["data"]:
            del scope_file["data"][key]
            self._write_scope_file(scope, scope_file["data"])
            return True
        return False

    def list_keys(self, scope: str) -> List[str]:
        scope_file = self._read_scope_file(scope)
        return list(scope_file["data"].keys())

    def list_scopes(self, pattern: Optional[str] = None) -> List[str]:
        scopes = []
        for filepath in self.base_path.glob("*.json"):
            scope = self._filename_to_scope(filepath)
            if pattern is None or fnmatch.fnmatch(scope, pattern):
                scopes.append(scope)
        return sorted(scopes)

    def delete_scope(self, scope: str) -> bool:
        filepath = self._scope_to_filename(scope)
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def close(self) -> None:
        pass  # No cleanup needed for files
```

### Characteristics

**Pros:**

- ✅ No external dependencies
- ✅ Easy to inspect/debug (just open JSON files)
- ✅ Works offline
- ✅ Simple setup

**Cons:**

- ❌ Local only (can't coordinate across machines)
- ❌ No atomic operations
- ❌ No built-in TTL/expiry

**Concurrency:**

- Same-machine: Safe (each session writes to own scope file)
- Cross-machine: Not applicable (files are local)

## Future: Redis Adapter

### Implementation Sketch

```python
import redis
import json
from typing import Any, Optional, List
import fnmatch

class RedisAdapter(StorageAdapter):
    def __init__(self, url: str, prefix: str = "claude:", ttl: Optional[int] = None):
        self.client = redis.from_url(url)
        self.prefix = prefix
        self.ttl = ttl  # Default TTL in seconds

    def _make_key(self, scope: str, key: str) -> str:
        return f"{self.prefix}{scope}:{key}"

    def _make_scope_key(self, scope: str) -> str:
        return f"{self.prefix}{scope}:*"

    def store(self, scope: str, key: str, value: Any) -> None:
        redis_key = self._make_key(scope, key)
        serialized = json.dumps(value)
        if self.ttl:
            self.client.setex(redis_key, self.ttl, serialized)
        else:
            self.client.set(redis_key, serialized)

    def retrieve(self, scope: str, key: str) -> Optional[Any]:
        redis_key = self._make_key(scope, key)
        value = self.client.get(redis_key)
        return json.loads(value) if value else None

    def delete(self, scope: str, key: str) -> bool:
        redis_key = self._make_key(scope, key)
        return self.client.delete(redis_key) > 0

    def list_keys(self, scope: str) -> List[str]:
        pattern = self._make_scope_key(scope)
        keys = self.client.keys(pattern)
        # Extract key names (remove prefix and scope)
        prefix_len = len(f"{self.prefix}{scope}:")
        return [k.decode('utf-8')[prefix_len:] for k in keys]

    def list_scopes(self, pattern: Optional[str] = None) -> List[str]:
        all_keys = self.client.keys(f"{self.prefix}*")
        scopes = set()

        for key in all_keys:
            key_str = key.decode('utf-8')
            # Extract scope (everything between prefix and last :)
            without_prefix = key_str[len(self.prefix):]
            scope = ":".join(without_prefix.split(":")[:-1])
            scopes.add(scope)

        if pattern:
            scopes = {s for s in scopes if fnmatch.fnmatch(s, pattern)}

        return sorted(scopes)

    def delete_scope(self, scope: str) -> bool:
        pattern = self._make_scope_key(scope)
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
            return True
        return False

    def close(self) -> None:
        self.client.close()
```

### Redis Adapter Characteristics

**Pros:**

- ✅ Cross-machine coordination
- ✅ Fast operations (in-memory)
- ✅ Atomic operations available (SETNX, INCR)
- ✅ Built-in TTL (auto-cleanup orphaned sessions)
- ✅ Pub/Sub for real-time notifications

**Cons:**

- ❌ Requires Redis server
- ❌ Network dependency
- ❌ Costs (if using cloud Redis)

**Concurrency:**

- Thread-safe
- Cross-machine safe
- Atomic operations for locking

## Adapter Factory

```python
from typing import Dict, Any

class AdapterFactory:
    """Creates storage adapters based on configuration"""

    _adapters = {
        "local": LocalFileAdapter,
        "redis": RedisAdapter,
        # Future: "s3": S3Adapter, "postgres": PostgresAdapter, etc.
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> StorageAdapter:
        adapter_type = config["storage"]["adapter"]
        adapter_config = config["storage"]["config"]

        if adapter_type not in cls._adapters:
            raise ValueError(f"Unknown adapter type: {adapter_type}")

        adapter_class = cls._adapters[adapter_type]
        return adapter_class(**adapter_config)

    @classmethod
    def register_adapter(cls, name: str, adapter_class: type):
        """Allow users to register custom adapters"""
        cls._adapters[name] = adapter_class
```

## MCP Server Integration

### Initialization

```python
from mcp.server import Server
import json

app = Server("claude-session-coordinator")

# Load config
with open("config.json") as f:
    config = json.load(f)

# Create storage adapter
storage = AdapterFactory.create(config)

# Detect machine and project
machine_id = detect_machine_id(config)
project_id = detect_project_id(config)

# Current session context (set during sign_on)
current_session = None
```

### Tool Implementations

```python
@app.tool()
def sign_on(session_id: Optional[str] = None) -> dict:
    """Sign on to a session, establishing identity"""
    global current_session

    # Auto-detect or assign session
    if not session_id:
        # Find first available
        instances_scope = f"{machine_id}:{project_id}:instances"
        instances = storage.retrieve(instances_scope, "registry") or {}
        session_id = next((k for k, v in instances.items()
                          if v == "available"), "claude_1")

    # Mark as taken
    instances_scope = f"{machine_id}:{project_id}:instances"
    instances = storage.retrieve(instances_scope, "registry") or {}
    instances[session_id] = "taken"
    storage.store(instances_scope, "registry", instances)

    # Set current session context
    current_session = {
        "machine": machine_id,
        "project": project_id,
        "session_id": session_id,
        "full_scope_prefix": f"{machine_id}:{project_id}"
    }

    return current_session

@app.tool()
def store_data(scope: str, key: str, value: Any) -> None:
    """Store data in a scope"""
    if not current_session:
        raise Exception("Must call sign_on() first")

    # Auto-prefix with session context
    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    storage.store(full_scope, key, value)

@app.tool()
def retrieve_data(scope: str, key: str) -> Any:
    """Retrieve data from a scope"""
    if not current_session:
        raise Exception("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.retrieve(full_scope, key)

@app.tool()
def list_keys(scope: str) -> List[str]:
    """List all keys in a scope"""
    if not current_session:
        raise Exception("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.list_keys(full_scope)

@app.tool()
def list_scopes(pattern: Optional[str] = None) -> List[str]:
    """List all scopes, optionally filtered by pattern"""
    if not current_session:
        raise Exception("Must call sign_on() first")

    # Auto-prefix pattern with current context
    if pattern:
        full_pattern = f"{current_session['full_scope_prefix']}:{pattern}"
    else:
        full_pattern = f"{current_session['full_scope_prefix']}:*"

    scopes = storage.list_scopes(full_pattern)

    # Strip prefix for cleaner output
    prefix = f"{current_session['full_scope_prefix']}:"
    return [s.replace(prefix, "", 1) for s in scopes]

@app.tool()
def delete_data(scope: str, key: str) -> bool:
    """Delete a key from a scope"""
    if not current_session:
        raise Exception("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.delete(full_scope, key)

@app.tool()
def delete_scope(scope: str) -> bool:
    """Delete an entire scope"""
    if not current_session:
        raise Exception("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.delete_scope(full_scope)

@app.tool()
def sign_off() -> dict:
    """Sign off from current session"""
    global current_session

    if not current_session:
        return {"status": "no active session"}

    # Mark instance as available
    instances_scope = f"{current_session['full_scope_prefix']}:instances"
    instances = storage.retrieve(instances_scope, "registry") or {}
    instances[current_session["session_id"]] = "available"
    storage.store(instances_scope, "registry", instances)

    result = {"status": "signed off", "session": current_session}
    current_session = None

    return result
```

### MCP Resources & Prompts (Self-Documenting Server)

The MCP server provides resources and prompts that automatically guide
Claude through the workflow, eliminating the need for Claude to memorize
sign-on procedures.

#### Resource: Session Context

```python
@app.resource("session://context")
def get_session_context() -> dict:
    """Provides current session context and guidance

    Claude can read this resource to understand:
    - What machine it's on, what project it's in
    - Which instances are available, what it needs to do next
    """
    # Get current state
    instances_scope = f"{machine_id}:{project_id}:instances"
    instances = storage.retrieve(instances_scope, "registry") or {
        "claude_1": "available",
        "claude_2": "available",
        "claude_3": "available",
        "claude_4": "available"
    }

    # Find active sessions
    active_sessions = []
    for instance_id, status in instances.items():
        session_scope = f"{machine_id}:{project_id}:session:{instance_id}"
        if storage.list_keys(session_scope):
            current_issue = storage.retrieve(session_scope, "current_issue")
            todos = storage.retrieve(session_scope, "todos") or []
            active_sessions.append({
                "instance": instance_id,
                "status": status,
                "current_issue": current_issue,
                "todo_count": len(todos)
            })

    return {
        "machine": machine_id,
        "project": project_id,
        "instances": instances,
        "active_sessions": active_sessions,
        "first_available": next((k for k, v in instances.items()
                                 if v == "available"), None),
        "instructions": {
            "if_not_signed_on": "Call sign_on() to claim an instance",
            "if_signed_on": "Use store_data/retrieve_data to work with session state",
            "when_done": "Call sign_off() to release your instance"
        }
    }
```

**Usage by Claude:**

```python
# Claude automatically reads this resource when starting
context = read_resource("session://context")

# Claude knows:
# - I'm on machine "laptop"
# - Working on "BANCS-Norway/claude_session_cordinator"
# - claude_1 is available
# - I should call sign_on() next
```

#### Resource: Session State

```python
@app.resource("session://state/{instance_id}")
def get_session_state(instance_id: str) -> dict:
    """Read another session's state (read-only coordination)

    Allows sessions to see what others are working on
    """
    session_scope = f"{machine_id}:{project_id}:session:{instance_id}"

    if not storage.list_keys(session_scope):
        return {"error": "Session not found or not active"}

    return {
        "instance": instance_id,
        "current_issue": storage.retrieve(session_scope, "current_issue"),
        "status": storage.retrieve(session_scope, "status"),
        "todos": storage.retrieve(session_scope, "todos"),
        "last_updated": storage.retrieve(session_scope, "last_updated")
    }
```

**Usage:**

```python
# Claude checks what claude_1 is doing
state = read_resource("session://state/claude_1")
# → {"instance": "claude_1", "current_issue": 15, "status": "in_progress", ...}
```

#### Prompt: Startup

```python
@app.prompt("startup")
def startup_prompt() -> str:
    """Guides Claude through session startup

    This prompt is automatically shown when Claude connects
    """
    context = get_session_context()

    if context["first_available"] is None:
        return f"""
        ⚠️ All instances are currently taken in {context['project']}.

        Active sessions:
        {format_active_sessions(context['active_sessions'])}

        Please wait for an instance to become available, or ask the
        user which instance to use.
        """

    return f"""
    # Session Coordinator Startup

    You are starting a new session in: **{context['project']}**
    Machine: {context['machine']}

    ## Current Status

    Available instances: {[k for k, v in context['instances'].items()
                          if v == 'available']}
    Active sessions: {len([s for s in context['active_sessions']
                          if s['status'] == 'taken'])}

    ## Next Steps

    1. **Sign on**: Call `sign_on()` to claim instance
       `{context['first_available']}`
    2. **Check coordination**: Read other sessions' state to see what's
       being worked on
    3. **Start work**: Use `store_data()` to track your progress
    4. **Sign off**: When done, call `sign_off()` to release your
       instance

    Would you like me to sign on now?
    """

def format_active_sessions(sessions: list) -> str:
    """Format active sessions for display"""
    lines = []
    for session in sessions:
        if session['status'] == 'taken':
            issue = session.get('current_issue', 'N/A')
            todos = session.get('todo_count', 0)
            lines.append(f"  - {session['instance']}: Issue #{issue} ({todos} todos)")
    return "\n".join(lines) if lines else "  (none)"
```

**Claude automatically sees this when connecting to the server!**

#### Prompt: Sign-off

```python
@app.prompt("sign-off")
def sign_off_prompt() -> str:
    """Guides Claude through proper sign-off procedure"""

    if not current_session:
        return "No active session to sign off from."

    # Get current work state
    session_scope = f"{current_session['full_scope_prefix']}:session:{current_session['session_id']}"
    current_issue = storage.retrieve(session_scope, "current_issue")
    todos = storage.retrieve(session_scope, "todos") or []
    incomplete = [t for t in todos if t.get('status') != 'completed']

    if incomplete:
        return f"""
        # Sign-off Checklist

        You have {len(incomplete)} incomplete tasks:
        {format_todos(incomplete)}

        Before signing off:
        1. Save current progress to session state
        2. Ensure all important work is committed
        3. Call `sign_off()` to release instance {current_session['session_id']}

        Are you ready to sign off?
        """

    return f"""
    # Ready to Sign Off

    All tasks complete for issue #{current_issue}!

    Call `sign_off()` to release instance {current_session['session_id']}.
    """
```

#### Tool Descriptions (Auto-Guidance)

Rich tool descriptions guide Claude without requiring external documentation:

```python
@app.tool(
    description="""
    **Sign on to claim an instance and establish session identity.**

    🔹 REQUIRED FIRST STEP: Call this before any other operations.

    What it does:
    - Auto-detects machine (from hostname)
    - Auto-detects project (from git remote)
    - Claims first available instance (or use session_id parameter)
    - Returns your session context

    Parameters:
    - session_id (optional): Specific instance to claim (e.g., "claude_1")
      If omitted, automatically assigns first available.

    Returns:
    {
      "machine": "laptop",
      "project": "BANCS-Norway/claude_session_cordinator",
      "session_id": "claude_1",
      "full_scope_prefix": "laptop:BANCS-Norway/claude_session_cordinator"
    }

    After signing on, all other tools will work with your session context automatically.
    """
)
def sign_on(session_id: Optional[str] = None) -> dict:
    # ... implementation
```

### Benefits of Self-Documenting Design

**Without resources/prompts (manual):**

```text
User: "Start working on issue 15"
Claude: "Let me check what I need to do... I should probably sign on
first..."
Claude: "How do I sign on? What parameters do I need?"
User: "Just call sign_on()"
Claude: "Ok, calling sign_on()..."
```

**With resources/prompts (automatic):**

```text
[Claude connects to MCP server]
[Server sends startup prompt]
Claude: "I can see I'm on laptop working in
BANCS-Norway/claude_session_cordinator.
        Instance claude_1 is available. Let me sign on."
Claude: [Calls sign_on() automatically]
Claude: "Signed on as claude_1. Ready to work on issue 15!"
User: "Great!"
```

**Key advantages:**

- ✅ Claude doesn't need to memorize workflow
- ✅ Server provides current state automatically
- ✅ Prompts guide through each step
- ✅ Tool descriptions explain usage inline
- ✅ New users onboard instantly
- ✅ No external documentation needed

## Machine & Project Detection

```python
import socket
import subprocess
import os
from pathlib import Path

def detect_machine_id(config: dict) -> str:
    """Detect machine identifier"""
    machine_id_setting = config.get("session", {}).get("machine_id", "auto")

    if machine_id_setting == "auto":
        # Use hostname
        return socket.gethostname()
    else:
        # Use configured value
        return machine_id_setting

def detect_project_id(config: dict) -> str:
    """Detect project from git"""
    detection_method = config.get("session", {}).get("project_detection", "git")

    if detection_method == "git":
        try:
            # Get git remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()

            # Parse owner/repo from URL
            # git@github.com:BANCS-Norway/claude_session_cordinator.git
            # or https://github.com/BANCS-Norway/claude_session_cordinator.git

            if remote_url.startswith("git@"):
                # SSH format
                parts = remote_url.split(":")
                owner_repo = parts[1].replace(".git", "")
            else:
                # HTTPS format
                parts = remote_url.split("/")
                owner_repo = f"{parts[-2]}/{parts[-1].replace('.git', '')}"

            return owner_repo

        except Exception as e:
            # Fallback to directory name
            return Path.cwd().name

    elif detection_method == "directory":
        return Path.cwd().name

    else:
        raise ValueError(f"Unknown project detection method: {detection_method}")
```

## Configuration File Location

**Priority order:**

1. `CLAUDE_SESSION_COORDINATOR_CONFIG` environment variable
2. `./.claude/session-coordinator-config.json` (project-local)
3. `~/.config/claude-session-coordinator/config.json` (user-global)
4. Built-in defaults (local file storage)

## Migration Path

**Phase 1 → Phase 2 (Redis):**

1. Change config:

   ```json
   {"storage": {"adapter": "redis", "config": {...}}}
   ```

2. Optionally migrate data:

   ```bash
   claude-session-coordinator migrate \
     --from local \
     --to redis://localhost:6379
   ```

3. All existing client code works unchanged (adapter pattern!)

## Testing Strategy

```python
# test_storage_adapters.py
import pytest
from adapters import LocalFileAdapter, RedisAdapter

@pytest.fixture(params=["local", "redis"])
def storage(request):
    """Test all adapters with same test suite"""
    if request.param == "local":
        return LocalFileAdapter("./test-storage")
    elif request.param == "redis":
        return RedisAdapter("redis://localhost:6379/15")  # Use test DB

def test_store_and_retrieve(storage):
    storage.store("test-scope", "key1", "value1")
    assert storage.retrieve("test-scope", "key1") == "value1"

def test_list_keys(storage):
    storage.store("test-scope", "key1", "value1")
    storage.store("test-scope", "key2", "value2")
    keys = storage.list_keys("test-scope")
    assert set(keys) == {"key1", "key2"}

# ... more tests that run against ALL adapters
```

## Summary

**Phase 1 Deliverables:**

- ✅ Storage adapter interface
- ✅ Local file adapter implementation
- ✅ Configuration system
- ✅ Adapter factory
- ✅ MCP server with 8 tools (6 core + sign_on + sign_off)
- ✅ Machine/project detection
- ✅ Scope format that supports future multi-machine use

**Future Phases:**

- Redis adapter for cross-machine coordination
- S3/cloud storage adapter for global teams
- PostgreSQL adapter for enterprise deployments
- Pub/sub notifications
- Atomic operations (compare-and-swap, increment)
- TTL/expiry for auto-cleanup
- Admin dashboard/CLI

**Key Benefit:**

Users can start simple (local files) and upgrade to distributed
coordination (Redis) without changing any client code!
