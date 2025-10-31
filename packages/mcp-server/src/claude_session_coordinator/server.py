"""MCP Server for Claude Session Coordinator.

This module implements the main MCP server that provides tools, resources,
and prompts for coordinating multiple Claude sessions across machines.
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .adapters import AdapterFactory, StorageAdapter
from .config import load_config
from .detection import detect_machine_id, detect_project_id

# Global server state
app = FastMCP("claude-session-coordinator")
storage: StorageAdapter | None = None
machine_id: str = ""
project_id: str = ""
current_session: dict[str, str] | None = None


def initialize_server() -> None:
    """Initialize the server with configuration and storage adapter."""
    global storage, machine_id, project_id

    # Load configuration
    config = load_config()

    # Create storage adapter from config
    storage = AdapterFactory.create_adapter(config["storage"])

    # Detect machine and project
    machine_id = detect_machine_id(config)
    project_id = detect_project_id(config)


# Tool implementations


@app.tool()
def sign_on(session_id: str | None = None) -> dict[str, str]:
    """Sign on to claim an instance and establish session identity.

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
      "project": "BANCS-Norway/claude_session_coordinator",
      "session_id": "claude_1",
      "full_scope_prefix": "laptop:BANCS-Norway/claude_session_coordinator"
    }

    After signing on, all other tools will work with your session context automatically.
    """
    global current_session

    if storage is None:
        raise RuntimeError("Server not initialized")

    # Auto-detect or assign session
    if not session_id:
        # Find first available
        instances_scope = f"{machine_id}:{project_id}:instances"
        instances = storage.retrieve(instances_scope, "registry") or {}

        # Find first available instance, default to claude_1 if none exist
        session_id = next((k for k, v in instances.items() if v == "available"), "claude_1")

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
        "full_scope_prefix": f"{machine_id}:{project_id}",
    }

    return current_session


@app.tool()
def sign_off() -> dict[str, Any]:
    """Sign off from current session and release the instance.

    When done working:
    1. Ensure all important work is saved
    2. Call this to release your instance for others
    3. Session state is preserved for future reference

    Returns:
    {
      "status": "signed off",
      "session": {...session info...}
    }
    """
    global current_session

    if storage is None:
        raise RuntimeError("Server not initialized")

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


@app.tool()
def store_data(scope: str, key: str, value: Any) -> None:
    """Store data in a scoped context.

    All scopes are automatically prefixed with your machine:project context.

    Parameters:
    - scope: Logical scope (e.g., "session:claude_1", "issue:15")
    - key: Key to store under
    - value: Value to store (must be JSON-serializable)

    Example:
        store_data("session:claude_1", "current_issue", 15)
        store_data("session:claude_1", "todos", [...])
        store_data("issue:15", "status", "in_progress")
    """
    if storage is None:
        raise RuntimeError("Server not initialized")

    if not current_session:
        raise RuntimeError("Must call sign_on() first")

    # Auto-prefix with session context
    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    storage.store(full_scope, key, value)


@app.tool()
def retrieve_data(scope: str, key: str) -> Any:
    """Retrieve data from a scoped context.

    Parameters:
    - scope: Logical scope (e.g., "session:claude_1", "issue:15")
    - key: Key to retrieve

    Returns:
        The stored value, or None if not found

    Example:
        issue = retrieve_data("session:claude_1", "current_issue")
        todos = retrieve_data("session:claude_1", "todos")
    """
    if storage is None:
        raise RuntimeError("Server not initialized")

    if not current_session:
        raise RuntimeError("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.retrieve(full_scope, key)


@app.tool()
def delete_data(scope: str, key: str) -> bool:
    """Delete a specific key from a scope.

    Parameters:
    - scope: Logical scope
    - key: Key to delete

    Returns:
        True if the key existed and was deleted, False otherwise
    """
    if storage is None:
        raise RuntimeError("Server not initialized")

    if not current_session:
        raise RuntimeError("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.delete(full_scope, key)


@app.tool()
def list_keys(scope: str) -> list[str]:
    """List all keys in a scope.

    Parameters:
    - scope: Logical scope to list keys from

    Returns:
        List of key names

    Example:
        keys = list_keys("session:claude_1")
        # → ["current_issue", "todos", "status"]
    """
    if storage is None:
        raise RuntimeError("Server not initialized")

    if not current_session:
        raise RuntimeError("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.list_keys(full_scope)


@app.tool()
def list_scopes(pattern: str | None = None) -> list[str]:
    """List all scopes, optionally filtered by pattern.

    Scopes are automatically filtered to your machine:project context,
    and the prefix is stripped for cleaner output.

    Parameters:
    - pattern (optional): Glob pattern to filter scopes (e.g., "session:*", "issue:*")

    Returns:
        List of scope identifiers (without machine:project prefix)

    Example:
        scopes = list_scopes()
        # → ["session:claude_1", "session:claude_2", "issue:15", "instances"]

        sessions = list_scopes("session:*")
        # → ["session:claude_1", "session:claude_2"]
    """
    if storage is None:
        raise RuntimeError("Server not initialized")

    if not current_session:
        raise RuntimeError("Must call sign_on() first")

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
def delete_scope(scope: str) -> bool:
    """Delete an entire scope and all its keys.

    ⚠️ WARNING: This permanently deletes all data in the scope.

    Parameters:
    - scope: Scope to delete

    Returns:
        True if the scope existed and was deleted, False otherwise

    Example:
        delete_scope("issue:15")  # Delete all data for issue 15
    """
    if storage is None:
        raise RuntimeError("Server not initialized")

    if not current_session:
        raise RuntimeError("Must call sign_on() first")

    full_scope = f"{current_session['full_scope_prefix']}:{scope}"
    return storage.delete_scope(full_scope)


# Resource implementations


@app.resource("session://context")
def get_session_context() -> str:
    """Provide current session context and available instances.

    Claude can read this resource to understand:
    - What machine it's on
    - What project it's in
    - Which instances are available
    - What other sessions are working on

    Returns:
        JSON string with session context information
    """
    if storage is None:
        return '{"error": "Server not initialized"}'

    # Get current state
    instances_scope = f"{machine_id}:{project_id}:instances"
    instances = storage.retrieve(instances_scope, "registry") or {
        "claude_1": "available",
        "claude_2": "available",
        "claude_3": "available",
        "claude_4": "available",
    }

    # Find active sessions
    active_sessions = []
    for instance_id, status in instances.items():
        if status == "taken":
            session_scope = f"{machine_id}:{project_id}:session:{instance_id}"
            keys = storage.list_keys(session_scope)
            if keys:
                current_issue = storage.retrieve(session_scope, "current_issue")
                todos = storage.retrieve(session_scope, "todos") or []
                active_sessions.append(
                    {
                        "instance": instance_id,
                        "status": status,
                        "current_issue": current_issue,
                        "todo_count": len(todos) if isinstance(todos, list) else 0,
                    }
                )

    context = {
        "machine": machine_id,
        "project": project_id,
        "current_session": current_session,
        "instances": instances,
        "active_sessions": active_sessions,
        "first_available": next((k for k, v in instances.items() if v == "available"), None),
        "instructions": {
            "if_not_signed_on": "Call sign_on() to claim an instance",
            "if_signed_on": "Use store_data/retrieve_data to work with session state",
            "when_done": "Call sign_off() to release your instance",
        },
    }

    import json

    return json.dumps(context, indent=2)


@app.resource("session://state/{instance_id}")
def get_session_state(instance_id: str) -> str:
    """Read another session's state (read-only coordination).

    Allows sessions to see what others are working on without
    interfering with their work.

    Parameters:
    - instance_id: Instance to read state from (e.g., "claude_1")

    Returns:
        JSON string with session state information
    """
    if storage is None:
        return '{"error": "Server not initialized"}'

    session_scope = f"{machine_id}:{project_id}:session:{instance_id}"

    keys = storage.list_keys(session_scope)
    if not keys:
        return '{"error": "Session not found or not active"}'

    state = {
        "instance": instance_id,
        "current_issue": storage.retrieve(session_scope, "current_issue"),
        "status": storage.retrieve(session_scope, "status"),
        "todos": storage.retrieve(session_scope, "todos"),
        "last_updated": storage.retrieve(session_scope, "last_updated"),
    }

    import json

    return json.dumps(state, indent=2)


# Prompt implementations


@app.prompt()
def startup() -> str:
    """Guide Claude through session startup.

    This prompt is shown when Claude connects to help establish
    session identity and understand the current state.
    """
    if storage is None:
        return "⚠️ Server not initialized"

    instances_scope = f"{machine_id}:{project_id}:instances"
    instances = storage.retrieve(instances_scope, "registry") or {
        "claude_1": "available",
        "claude_2": "available",
        "claude_3": "available",
        "claude_4": "available",
    }

    first_available = next((k for k, v in instances.items() if v == "available"), None)

    if first_available is None:
        active_count = sum(1 for v in instances.values() if v == "taken")
        return f"""
⚠️ All instances are currently taken in {project_id}.

Active sessions: {active_count}

Please wait for an instance to become available, or ask the user which instance to use.
"""

    available_list = [k for k, v in instances.items() if v == "available"]
    active_count = sum(1 for v in instances.values() if v == "taken")

    return f"""
# Session Coordinator Startup

You are starting a new session in: **{project_id}**
Machine: {machine_id}

## Current Status

Available instances: {available_list}
Active sessions: {active_count}

## Next Steps

1. **Sign on**: Call `sign_on()` to claim instance `{first_available}`
2. **Check coordination**: Read other sessions' state to see what's being worked on
3. **Start work**: Use `store_data()` to track your progress
4. **Sign off**: When done, call `sign_off()` to release your instance

Would you like me to sign on now?
"""


@app.prompt()
def sign_off_prompt() -> str:
    """Guide Claude through proper sign-off procedure.

    Reminds about incomplete work and ensures proper cleanup.
    """
    if not current_session:
        return "No active session to sign off from."

    # Get current work state
    session_scope = (
        f"{current_session['full_scope_prefix']}:session:{current_session['session_id']}"
    )
    current_issue = storage.retrieve(session_scope, "current_issue") if storage else None
    todos = storage.retrieve(session_scope, "todos") if storage else []

    if isinstance(todos, list):
        incomplete = [t for t in todos if isinstance(t, dict) and t.get("status") != "completed"]
    else:
        incomplete = []

    if incomplete:
        todo_list = "\n".join(f"  - {t.get('task', 'Unknown task')}" for t in incomplete)
        return f"""
# Sign-off Checklist

You have {len(incomplete)} incomplete tasks:
{todo_list}

Before signing off:
1. Save current progress to session state
2. Ensure all important work is committed
3. Call `sign_off()` to release instance {current_session['session_id']}

Are you ready to sign off?
"""

    return f"""
# Ready to Sign Off

All tasks complete{f" for issue #{current_issue}" if current_issue else ""}!

Call `sign_off()` to release instance {current_session['session_id']}.
"""


# Server entry point


async def main() -> None:
    """Main entry point for the MCP server."""
    initialize_server()
    await app.run_stdio_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
