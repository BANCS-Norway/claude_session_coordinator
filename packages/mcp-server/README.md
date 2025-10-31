# Claude Session Coordinator - MCP Server

Python MCP server enabling multiple Claude AI sessions to coordinate work through flexible storage adapters.

## Installation

### Development

```bash
pip install -e .
```

### With Redis Support

```bash
pip install -e ".[redis]"
```

## Quick Start

### 1. Configure Claude Code

Add to your MCP settings:

```json
{
  "mcpServers": {
    "session-coordinator": {
      "command": "python",
      "args": ["-m", "claude_session_coordinator"]
    }
  }
}
```

### 2. Start Claude Code

The coordinator will automatically:
- Detect your machine and project
- Show available instances
- Guide you through sign-on

### 3. Sign On

```python
# Claude will automatically prompt you, or you can call directly:
sign_on()  # Claims first available instance

# Returns:
# {
#   "machine": "laptop",
#   "project": "BANCS-Norway/my-repo",
#   "session_id": "claude_1",
#   "full_scope_prefix": "laptop:BANCS-Norway/my-repo"
# }
```

### 4. Work with State

```python
# Store data
store_data("session:claude_1", "current_issue", 15)
store_data("session:claude_1", "todos", [
    {"task": "Implement feature", "status": "in_progress"},
    {"task": "Write tests", "status": "pending"}
])

# Retrieve data
issue = retrieve_data("session:claude_1", "current_issue")  # → 15

# List what's available
keys = list_keys("session:claude_1")  # → ["current_issue", "todos"]
scopes = list_scopes()  # → ["session:claude_1", "session:claude_2", ...]

# Check other sessions
other_session = retrieve_data("session:claude_2", "current_issue")
```

### 5. Sign Off

```python
sign_off()  # Releases your instance
```

## Features

### Storage Adapters

Switch backends via configuration:

**Local Files (default):**
```json
{
  "storage": {
    "adapter": "local",
    "config": {
      "base_path": ".claude/session-state"
    }
  }
}
```

**Redis (future):**
```json
{
  "storage": {
    "adapter": "redis",
    "config": {
      "url": "redis://localhost:6379/0"
    }
  }
}
```

### MCP Resources

Read-only context provided automatically:

- `session://context` - Current machine, project, available instances
- `session://state/{id}` - Another session's state

### MCP Prompts

Guides Claude automatically:

- `startup` - Shows status and guides sign-on
- `sign-off` - Reminds about incomplete work

## Configuration

### Config File Locations (Priority Order)

1. `CLAUDE_SESSION_COORDINATOR_CONFIG` environment variable
2. `./.claude/session-coordinator-config.json` (project-local)
3. `~/.config/claude-session-coordinator/config.json` (user-global)
4. Built-in defaults

### Example Config

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

## Architecture

See [Architecture Overview](../../docs/architecture/overview.md) for detailed design.

### Scope Format

```
{machine}:{owner}/{repo}:{type}:{id}
```

Examples:
- `laptop:BANCS-Norway/project:session:claude_1`
- `desktop:BANCS-Norway/project:instances`
- `laptop:BANCS-Norway/project:issue:15`

### Storage Adapter Interface

All adapters implement:
- `store(scope, key, value)`
- `retrieve(scope, key) → value`
- `delete(scope, key) → bool`
- `list_keys(scope) → list[str]`
- `list_scopes(pattern) → list[str]`
- `delete_scope(scope) → bool`

## Development

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

## Documentation

- [Architecture](../../docs/architecture/)
- [Implementation Plan](../../docs/implementation/)
- [Use Cases](../../docs/use-cases/)

## License

MIT License - See [LICENSE](../../LICENSE)
