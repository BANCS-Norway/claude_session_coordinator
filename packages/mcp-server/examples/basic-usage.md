# Basic Usage Example

This guide demonstrates the fundamental workflow of using Claude Session Coordinator.

## Prerequisites

1. Install the package:
```bash
pip install -e .
```

2. Configure your Claude Code MCP settings (`.claude/settings.local.json`):
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

3. Restart Claude Code to load the MCP server

## Step 1: Sign On

When Claude starts, it will automatically show available instances. Sign on to claim one:

```python
# Claude will prompt you, or you can call directly:
sign_on()

# Returns:
# {
#   "machine": "laptop",
#   "project": "BANCS-Norway/my-repo",
#   "session_id": "claude_1",
#   "full_scope_prefix": "laptop:BANCS-Norway/my-repo"
# }
```

### Signing On to a Specific Instance

If you want to use a specific instance:

```python
sign_on(session_id="claude_3")
```

## Step 2: Store Session State

Store data to persist state across sessions:

```python
# Store current work context
store_data("session:claude_1", "current_issue", 15)

# Store complex data structures
store_data("session:claude_1", "todos", [
    {"task": "Implement storage adapter", "status": "completed"},
    {"task": "Write tests", "status": "in_progress"},
    {"task": "Update documentation", "status": "pending"}
])

# Store arbitrary data
store_data("session:claude_1", "notes", "Remember to run migrations after deployment")
```

### Organizing Data with Scopes

Use different scopes to organize your data:

```python
# Session-specific data
store_data("session:claude_1", "last_active", "2025-10-31T12:30:00Z")

# Issue-specific data
store_data("issue:15", "status", "in_progress")
store_data("issue:15", "assignee", "claude_1")
store_data("issue:15", "files_modified", ["adapter.py", "tests.py"])

# Project-wide data
store_data("project:metadata", "last_deployment", "2025-10-30")
```

## Step 3: Retrieve Data

Access stored data from anywhere in your session:

```python
# Retrieve simple values
current_issue = retrieve_data("session:claude_1", "current_issue")
# → 15

# Retrieve complex structures
todos = retrieve_data("session:claude_1", "todos")
# → [{"task": "...", "status": "..."}, ...]

# Check if data exists
notes = retrieve_data("session:claude_1", "notes")
if notes:
    print(f"Notes: {notes}")
```

## Step 4: Discover Available Data

List keys and scopes to see what's available:

```python
# List all keys in a scope
keys = list_keys("session:claude_1")
# → ["current_issue", "todos", "notes", "last_active"]

# List all scopes
scopes = list_scopes()
# → ["session:claude_1", "session:claude_2", "issue:15", "project:metadata"]

# Filter scopes by pattern
session_scopes = list_scopes("session:*")
# → ["session:claude_1", "session:claude_2"]

issue_scopes = list_scopes("issue:*")
# → ["issue:15"]
```

## Step 5: Clean Up Data

Delete data when it's no longer needed:

```python
# Delete a specific key
deleted = delete_data("session:claude_1", "notes")
# → True (if existed), False (if didn't exist)

# Delete an entire scope
delete_scope("issue:15")
# → True (deletes all data for issue 15)
```

## Step 6: Sign Off

When you're done working, release your instance:

```python
sign_off()

# Returns:
# {
#   "status": "signed off",
#   "session": {
#     "machine": "laptop",
#     "project": "BANCS-Norway/my-repo",
#     "session_id": "claude_1",
#     "full_scope_prefix": "laptop:BANCS-Norway/my-repo"
#   }
# }
```

**Important:** Your session data is preserved even after signing off. Other sessions can access it, and you can resume it later.

## Complete Workflow Example

Here's a complete workflow showing how Claude might work on an issue:

```python
# 1. Sign on
result = sign_on()  # Claims claude_1

# 2. Check what others are doing
other_scopes = list_scopes("session:*")
for scope in other_scopes:
    if scope != "session:claude_1":
        issue = retrieve_data(scope, "current_issue")
        if issue:
            print(f"{scope} is working on issue #{issue}")

# 3. Start work on issue #15
store_data("session:claude_1", "current_issue", 15)
store_data("session:claude_1", "started_at", "2025-10-31T14:00:00Z")

# 4. Track progress
store_data("session:claude_1", "todos", [
    {"task": "Read issue description", "status": "completed"},
    {"task": "Implement fix", "status": "in_progress"},
    {"task": "Write tests", "status": "pending"},
    {"task": "Update documentation", "status": "pending"}
])

# 5. Store work context
store_data("issue:15", "branch", "fix/15-timeout-handling")
store_data("issue:15", "files_modified", [
    "src/server.py",
    "tests/test_server.py"
])

# 6. Update progress periodically
todos = retrieve_data("session:claude_1", "todos")
todos[1]["status"] = "completed"  # Implement fix done
todos[2]["status"] = "in_progress"  # Started writing tests
store_data("session:claude_1", "todos", todos)

# 7. When complete, clean up
delete_scope("session:claude_1")  # Optional: clear session data
sign_off()  # Release instance
```

## Working Across Multiple Sessions

If you have multiple Claude windows working on the same project:

**Session 1 (claude_1):**
```python
sign_on(session_id="claude_1")
store_data("session:claude_1", "current_issue", 15)
store_data("issue:15", "status", "in_progress")
```

**Session 2 (claude_2):**
```python
sign_on(session_id="claude_2")

# Check what claude_1 is working on
claude1_issue = retrieve_data("session:claude_1", "current_issue")
# → 15

# Check issue status
issue_status = retrieve_data("issue:15", "status")
# → "in_progress"

# Work on a different issue
store_data("session:claude_2", "current_issue", 16)
```

## Best Practices

1. **Always sign on first** - All data operations require an active session
2. **Use clear scope names** - E.g., `session:claude_1`, `issue:15`, `project:metadata`
3. **Store progress frequently** - Update todos and status regularly
4. **Sign off when done** - Release your instance for others
5. **Clean up old data** - Delete scopes for completed issues
6. **Use descriptive keys** - `current_issue` not `ci`, `todos` not `t`

## Common Patterns

### Resuming Work

```python
sign_on()

# Check if there's prior work
current_issue = retrieve_data("session:claude_1", "current_issue")
if current_issue:
    todos = retrieve_data("session:claude_1", "todos")
    print(f"Resuming work on issue #{current_issue}")
    print(f"Pending tasks: {[t for t in todos if t['status'] != 'completed']}")
```

### Coordinating with Other Sessions

```python
# Check all active sessions
all_sessions = list_scopes("session:*")
for session in all_sessions:
    issue = retrieve_data(session, "current_issue")
    if issue:
        print(f"{session} is on issue #{issue}")

# Avoid duplicate work
my_planned_issue = 20
for session in all_sessions:
    if retrieve_data(session, "current_issue") == my_planned_issue:
        print(f"Issue #{my_planned_issue} already being worked on by {session}")
        break
```

### Tracking Long-Running Tasks

```python
# Start a task
store_data("session:claude_1", "task:migration", {
    "status": "running",
    "started_at": "2025-10-31T14:00:00Z",
    "progress": 0
})

# Update progress
task = retrieve_data("session:claude_1", "task:migration")
task["progress"] = 50
store_data("session:claude_1", "task:migration", task)

# Complete
task["status"] = "completed"
task["completed_at"] = "2025-10-31T15:30:00Z"
task["progress"] = 100
store_data("session:claude_1", "task:migration", task)
```

## Troubleshooting

### "Must call sign_on() first"

You must sign on before using any data operations:

```python
sign_on()  # Do this first!
store_data(...)  # Now this will work
```

### All Instances Taken

If all instances are busy:

```python
# Check available instances
from claude_session_coordinator import server
context = server.get_session_context()
# Shows which instances are taken/available

# Wait for one to become available, or ask user
```

### Lost Session Context

If your session context is lost (e.g., after restart):

```python
# Just sign on again
sign_on(session_id="claude_1")  # Use the same ID to resume

# Your data is still there
current_issue = retrieve_data("session:claude_1", "current_issue")
```

## Next Steps

- See [Multi-Session Coordination](multi-session-coordination.md) for advanced patterns
- Check [Configuration](../README.md#configuration) for customization options
- Read [Architecture Overview](../../docs/architecture/overview.md) for system design
