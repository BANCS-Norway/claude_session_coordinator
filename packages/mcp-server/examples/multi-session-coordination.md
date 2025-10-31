# Multi-Session Coordination Example

This guide demonstrates advanced patterns for coordinating multiple Claude instances working on the same project.

## Scenario: Parallel Development

You have multiple Claude Code windows open, each working on different tasks in the same repository.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Claude Window 1│     │  Claude Window 2│     │  Claude Window 3│
│   (claude_1)    │     │   (claude_2)    │     │   (claude_3)    │
│                 │     │                 │     │                 │
│  Issue #15      │     │  Issue #16      │     │  Issue #17      │
│  Backend API    │     │  Frontend UI    │     │  Documentation  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Session Coordinator    │
                    │  Local File Storage     │
                    │  .claude/session-state/ │
                    └─────────────────────────┘
```

## Pattern 1: Work Assignment

### Claude Window 1 - Claims Work

```python
# Sign on
sign_on(session_id="claude_1")

# Check what's available
all_issues = list_scopes("issue:*")
print(f"Found {len(all_issues)} issues in progress")

# Check which issues are claimed
claimed_issues = []
all_sessions = list_scopes("session:*")
for session in all_sessions:
    issue = retrieve_data(session, "current_issue")
    if issue:
        claimed_issues.append(issue)
        print(f"{session} is working on issue #{issue}")

# Pick an unclaimed issue
MY_ISSUE = 15
if MY_ISSUE not in claimed_issues:
    store_data("session:claude_1", "current_issue", MY_ISSUE)
    store_data("issue:15", "claimed_by", "claude_1")
    store_data("issue:15", "claimed_at", "2025-10-31T14:00:00Z")
    print(f"Claimed issue #{MY_ISSUE}")
else:
    print(f"Issue #{MY_ISSUE} already claimed!")
```

### Claude Window 2 - Sees Claim

```python
# Sign on with different instance
sign_on(session_id="claude_2")

# Check claimed issues
all_sessions = list_scopes("session:*")
for session in all_sessions:
    issue = retrieve_data(session, "current_issue")
    if issue:
        print(f"{session} is working on issue #{issue}")

# Output:
# session:claude_1 is working on issue #15

# Claim a different issue
store_data("session:claude_2", "current_issue", 16)
store_data("issue:16", "claimed_by", "claude_2")
```

## Pattern 2: Shared State

Multiple sessions can read and write shared project state:

### Session 1 - Creates Shared State

```python
sign_on(session_id="claude_1")

# Create shared migration tracker
store_data("project:migrations", "pending", [
    {"id": "001", "name": "add_users_table", "status": "pending"},
    {"id": "002", "name": "add_sessions_table", "status": "pending"},
    {"id": "003", "name": "add_indexes", "status": "pending"}
])
```

### Session 2 - Updates Shared State

```python
sign_on(session_id="claude_2")

# Read shared state
migrations = retrieve_data("project:migrations", "pending")

# Update - mark one as in progress
migrations[0]["status"] = "in_progress"
migrations[0]["started_by"] = "claude_2"
migrations[0]["started_at"] = "2025-10-31T14:15:00Z"

store_data("project:migrations", "pending", migrations)
```

### Session 3 - Reads Updated State

```python
sign_on(session_id="claude_3")

# Check migration status
migrations = retrieve_data("project:migrations", "pending")
for m in migrations:
    print(f"Migration {m['id']}: {m['status']}")

# Output:
# Migration 001: in_progress (by claude_2)
# Migration 002: pending
# Migration 003: pending
```

## Pattern 3: Lock-Free Coordination

Coordinate without explicit locking by using conventions:

### Resource Reservation Pattern

```python
# Session 1 - Reserve a resource
sign_on(session_id="claude_1")

def try_reserve_resource(resource_name, session_id):
    """Try to reserve a resource for exclusive access."""
    scope = f"locks:{resource_name}"

    # Check if already locked
    current_lock = retrieve_data(scope, "locked_by")
    if current_lock and current_lock != session_id:
        lock_time = retrieve_data(scope, "locked_at")
        return False, f"Locked by {current_lock} at {lock_time}"

    # Claim the lock
    store_data(scope, "locked_by", session_id)
    store_data(scope, "locked_at", "2025-10-31T14:30:00Z")
    return True, "Lock acquired"

# Try to reserve database migration
success, msg = try_reserve_resource("database_migration", "claude_1")
if success:
    # Perform migration
    print("Performing migration...")
    # ... do work ...

    # Release lock
    delete_scope("locks:database_migration")
```

### Session 2 - Respects Lock

```python
sign_on(session_id="claude_2")

success, msg = try_reserve_resource("database_migration", "claude_2")
if not success:
    print(f"Cannot perform migration: {msg}")
    # Do other work instead
```

## Pattern 4: Progress Broadcasting

Share progress updates across sessions:

### Session 1 - Broadcasts Progress

```python
sign_on(session_id="claude_1")

def update_progress(issue_id, phase, percent, message):
    """Broadcast progress to other sessions."""
    scope = f"issue:{issue_id}"
    store_data(scope, "progress", {
        "phase": phase,
        "percent": percent,
        "message": message,
        "updated_at": "2025-10-31T14:45:00Z",
        "updated_by": "claude_1"
    })

# Update progress as work proceeds
update_progress(15, "analysis", 25, "Analyzing codebase")
# ... do work ...
update_progress(15, "implementation", 50, "Implementing fix")
# ... do work ...
update_progress(15, "testing", 75, "Writing tests")
# ... do work ...
update_progress(15, "complete", 100, "All tasks complete")
```

### Session 2 - Monitors Progress

```python
sign_on(session_id="claude_2")

def check_progress(issue_id):
    """Check progress of another issue."""
    scope = f"issue:{issue_id}"
    progress = retrieve_data(scope, "progress")
    if progress:
        return f"Issue #{issue_id}: {progress['phase']} ({progress['percent']}%) - {progress['message']}"
    return f"Issue #{issue_id}: No progress data"

# Monitor other issues
print(check_progress(15))
# Output: Issue #15: testing (75%) - Writing tests
```

## Pattern 5: Task Queue

Implement a simple task queue for coordinating work:

### Initialize Queue

```python
sign_on(session_id="claude_1")

# Create task queue
store_data("project:queue", "tasks", [
    {"id": 1, "type": "test", "file": "adapters.py", "status": "pending"},
    {"id": 2, "type": "test", "file": "server.py", "status": "pending"},
    {"id": 3, "type": "lint", "file": "config.py", "status": "pending"},
    {"id": 4, "type": "test", "file": "detection.py", "status": "pending"}
])
```

### Worker Pattern - Claim and Process Tasks

```python
def claim_next_task(session_id):
    """Claim the next available task from the queue."""
    tasks = retrieve_data("project:queue", "tasks")

    # Find first pending task
    for task in tasks:
        if task["status"] == "pending":
            # Claim it
            task["status"] = "claimed"
            task["claimed_by"] = session_id
            task["claimed_at"] = "2025-10-31T15:00:00Z"

            # Update queue
            store_data("project:queue", "tasks", tasks)
            return task

    return None

# Session 1
sign_on(session_id="claude_1")
task = claim_next_task("claude_1")
if task:
    print(f"Processing task {task['id']}: {task['type']} {task['file']}")
    # ... process task ...

    # Mark complete
    tasks = retrieve_data("project:queue", "tasks")
    for t in tasks:
        if t["id"] == task["id"]:
            t["status"] = "completed"
            t["completed_at"] = "2025-10-31T15:05:00Z"
    store_data("project:queue", "tasks", tasks)

# Session 2 (runs in parallel)
sign_on(session_id="claude_2")
task = claim_next_task("claude_2")
# Gets a different task!
```

## Pattern 6: Handoff Between Sessions

Pass work from one session to another:

### Session 1 - Prepares Handoff

```python
sign_on(session_id="claude_1")

# Prepare handoff
store_data("issue:15", "handoff", {
    "from_session": "claude_1",
    "phase": "implementation_complete",
    "next_steps": [
        "Review code changes in src/adapters/local.py",
        "Run test suite with pytest",
        "Update documentation if tests pass"
    ],
    "context": {
        "files_modified": ["src/adapters/local.py"],
        "tests_added": ["tests/test_adapters.py"],
        "branch": "feat/15-local-adapter"
    },
    "handoff_at": "2025-10-31T15:30:00Z"
})

# Mark session as available for others
store_data("session:claude_1", "status", "handoff_ready")

# Sign off
sign_off()
```

### Session 2 - Picks Up Handoff

```python
sign_on(session_id="claude_2")

# Check for handoffs
handoff = retrieve_data("issue:15", "handoff")
if handoff and handoff["from_session"] == "claude_1":
    print(f"Picking up handoff from {handoff['from_session']}")
    print(f"Phase: {handoff['phase']}")
    print(f"Next steps:")
    for step in handoff["next_steps"]:
        print(f"  - {step}")

    # Claim the work
    store_data("session:claude_2", "current_issue", 15)
    store_data("issue:15", "current_session", "claude_2")

    # Clear handoff
    delete_data("issue:15", "handoff")

    # Continue work...
```

## Pattern 7: Session Health Check

Monitor session health and detect abandoned work:

```python
sign_on(session_id="claude_1")

def check_session_health():
    """Check health of all active sessions."""
    import datetime

    sessions = list_scopes("session:*")
    current_time = datetime.datetime.now()

    for session in sessions:
        last_update = retrieve_data(session, "last_heartbeat")
        if last_update:
            # Parse timestamp and check staleness
            # If stale (e.g., > 1 hour), mark as potentially abandoned
            print(f"{session}: last heartbeat {last_update}")

def heartbeat(session_id):
    """Update session heartbeat."""
    import datetime
    store_data(f"session:{session_id}", "last_heartbeat",
               datetime.datetime.now().isoformat())

# Update heartbeat periodically
heartbeat("claude_1")
```

## Pattern 8: Event Log

Maintain a shared event log for audit trail:

```python
sign_on(session_id="claude_1")

def log_event(event_type, message, metadata=None):
    """Append event to shared log."""
    import datetime

    # Get current log
    events = retrieve_data("project:events", "log") or []

    # Append new event
    events.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "session": current_session["session_id"],
        "type": event_type,
        "message": message,
        "metadata": metadata or {}
    })

    # Keep only last 1000 events
    if len(events) > 1000:
        events = events[-1000:]

    store_data("project:events", "log", events)

# Log events
log_event("issue_started", "Started work on issue #15", {"issue": 15})
log_event("file_modified", "Modified adapter.py", {"file": "src/adapters/local.py"})
log_event("tests_added", "Added unit tests", {"count": 10})
log_event("issue_completed", "Completed issue #15", {"issue": 15})
```

## Best Practices for Multi-Session Coordination

1. **Use Clear Naming Conventions**
   - `session:{id}` for session-specific data
   - `issue:{id}` for issue-specific data
   - `project:{name}` for project-wide data
   - `locks:{resource}` for resource locks

2. **Implement Heartbeats**
   - Update `last_heartbeat` periodically
   - Check for stale sessions before claiming work

3. **Broadcast Intent**
   - Store what you're working on
   - Check what others are working on before starting

4. **Use Soft Locks**
   - Store lock claims rather than file system locks
   - Include timestamps for timeout detection

5. **Clean Up After Yourself**
   - Delete session data when complete
   - Clear locks when done with resources

6. **Document State**
   - Store context about what you're doing
   - Leave breadcrumbs for the next session

7. **Handle Conflicts Gracefully**
   - Check before claiming
   - Have fallback tasks if preferred work is taken

8. **Monitor Progress**
   - Broadcast progress updates
   - Provide visibility into what's happening

## Complete Multi-Session Workflow

Here's a complete example of three sessions coordinating on a release:

```python
# === Session 1: Release Manager ===
sign_on(session_id="claude_1")

# Create release plan
store_data("project:release", "v1.0.0", {
    "status": "in_progress",
    "coordinator": "claude_1",
    "tasks": [
        {"id": 1, "name": "Run test suite", "assignee": None, "status": "pending"},
        {"id": 2, "name": "Build packages", "assignee": None, "status": "pending"},
        {"id": 3, "name": "Update changelog", "assignee": None, "status": "pending"}
    ]
})

# === Session 2: Tester ===
sign_on(session_id="claude_2")

release = retrieve_data("project:release", "v1.0.0")
for task in release["tasks"]:
    if task["id"] == 1 and task["status"] == "pending":
        task["assignee"] = "claude_2"
        task["status"] = "in_progress"
        break
store_data("project:release", "v1.0.0", release)

# Run tests...
# Mark complete
release = retrieve_data("project:release", "v1.0.0")
release["tasks"][0]["status"] = "completed"
store_data("project:release", "v1.0.0", release)

# === Session 3: Builder ===
sign_on(session_id="claude_3")

# Wait for tests to complete
release = retrieve_data("project:release", "v1.0.0")
if release["tasks"][0]["status"] == "completed":
    # Claim build task
    release["tasks"][1]["assignee"] = "claude_3"
    release["tasks"][1]["status"] = "in_progress"
    store_data("project:release", "v1.0.0", release)

    # Build packages...
```

## Troubleshooting

### Race Conditions

If two sessions try to claim the same resource simultaneously:

```python
# Use timestamps to detect and resolve
def safe_claim(resource, session_id):
    """Claim with race condition detection."""
    import time

    # Read current state
    current = retrieve_data(resource, "claimed_by")

    # Small delay to increase chance of seeing conflicts
    time.sleep(0.1)

    # Claim
    store_data(resource, "claimed_by", session_id)
    store_data(resource, "claimed_at", time.time())

    # Verify claim held
    time.sleep(0.1)
    verify = retrieve_data(resource, "claimed_by")

    if verify != session_id:
        return False, "Claim lost to another session"

    return True, "Claim successful"
```

### Abandoned Sessions

Detect and clean up abandoned sessions:

```python
import datetime

def cleanup_abandoned_sessions(timeout_minutes=60):
    """Clean up sessions that haven't updated in a while."""
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=timeout_minutes)

    sessions = list_scopes("session:*")
    for session in sessions:
        last_heartbeat = retrieve_data(session, "last_heartbeat")
        if last_heartbeat:
            last_time = datetime.datetime.fromisoformat(last_heartbeat)
            if last_time < cutoff:
                print(f"Cleaning up abandoned session: {session}")
                # Release any claimed resources
                current_issue = retrieve_data(session, "current_issue")
                if current_issue:
                    delete_data(f"issue:{current_issue}", "claimed_by")
                # Clean up session
                delete_scope(session)
```

## Next Steps

- See [Basic Usage](basic-usage.md) for fundamentals
- Check [Architecture Overview](../../docs/architecture/overview.md) for system design
- Read about [Storage Adapters](../README.md#storage-adapters) for scaling beyond local files
