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

### Adaptive Storage Selection

**NEW:** Claude can now help you choose and configure the right storage adapter for your needs!

On first run, Claude will ask about your coordination needs:
- **Single-machine**: Just you, working on one computer → Uses local file storage
- **Multi-machine**: You working across multiple machines → Uses Redis
- **Team collaboration**: Multiple people working together → Uses Redis

Your choice is saved to `.claude/settings.local.json` (gitignored) and used automatically in future sessions.

**To configure or change settings:**

```python
update_storage_settings(
    adapter="local",  # or "redis"
    scope="single-machine",  # or "multi-machine" or "team"
    reason="Solo development on this laptop"
)
```

**To check current settings:**

Read the `session://storage-config` resource to see:
- Current storage adapter and coordination scope
- Available adapters and their readiness status
- Recommendations if your adapter doesn't match your scope

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

**Redis:**
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

**Configuration Hierarchy:**
1. **Project settings** (`.claude/settings.local.json`) - Per-project user preferences ← NEW
2. **Global config** (config file or environment) - Available adapters and credentials
3. **Built-in defaults** - Fallback configuration

### MCP Resources

Read-only context provided automatically:

- `session://context` - Current machine, project, available instances
- `session://state/{id}` - Another session's state
- `session://storage-config` - Storage adapter settings and recommendations ← NEW

### MCP Prompts

Guides Claude automatically:

- `startup` - Shows status and guides sign-on (detects first-run for storage setup) ← ENHANCED
- `sign_off` - Reminds about incomplete work
- `first_run_storage` - Detailed guide for choosing storage adapter on first run ← NEW

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

### Examples

- [Basic Usage](examples/basic-usage.md) - Complete workflow guide with examples
- [Multi-Session Coordination](examples/multi-session-coordination.md) - Advanced coordination patterns
- [Configuration Example](examples/config.example.json) - Sample configuration file

### Architecture & Design

- [Architecture](../../docs/architecture/)
- [Implementation Plan](../../docs/implementation/)
- [Use Cases](../../docs/use-cases/)

## License

MIT License - See [LICENSE](../../LICENSE)
