"""Tests for the MCP server tools, resources, and prompts."""

import json
import pytest
from pathlib import Path
from claude_session_coordinator import server
from claude_session_coordinator.adapters import LocalFileAdapter


@pytest.fixture
def test_storage(tmp_path):
    """Create a test storage adapter with a temporary directory."""
    storage_path = tmp_path / "test-storage"
    return LocalFileAdapter(str(storage_path))


@pytest.fixture
def initialized_server(test_storage, monkeypatch):
    """Initialize the server with test configuration."""
    # Set up test server state
    monkeypatch.setattr(server, "storage", test_storage)
    monkeypatch.setattr(server, "machine_id", "test-machine")
    monkeypatch.setattr(server, "project_id", "test-org/test-repo")
    monkeypatch.setattr(server, "current_session", None)

    yield

    # Cleanup
    server.current_session = None


class TestSignOn:
    """Tests for the sign_on tool."""

    def test_sign_on_auto_assign(self, initialized_server):
        """Test signing on with automatic instance assignment."""
        result = server.sign_on()

        assert result["machine"] == "test-machine"
        assert result["project"] == "test-org/test-repo"
        assert result["session_id"] == "claude_1"  # First available
        assert result["full_scope_prefix"] == "test-machine:test-org/test-repo"

        # Verify instance is marked as taken
        instances_scope = "test-machine:test-org/test-repo:instances"
        instances = server.storage.retrieve(instances_scope, "registry")
        assert instances["claude_1"] == "taken"

    def test_sign_on_specific_instance(self, initialized_server):
        """Test signing on with a specific instance ID."""
        result = server.sign_on(session_id="claude_3")

        assert result["session_id"] == "claude_3"

        # Verify instance is marked as taken
        instances_scope = "test-machine:test-org/test-repo:instances"
        instances = server.storage.retrieve(instances_scope, "registry")
        assert instances["claude_3"] == "taken"

    def test_sign_on_sets_current_session(self, initialized_server):
        """Test that sign_on sets the current session context."""
        assert server.current_session is None

        server.sign_on()

        assert server.current_session is not None
        assert server.current_session["session_id"] == "claude_1"


class TestSignOff:
    """Tests for the sign_off tool."""

    def test_sign_off_releases_instance(self, initialized_server):
        """Test that sign_off releases the instance."""
        # First sign on
        server.sign_on(session_id="claude_2")

        # Then sign off
        result = server.sign_off()

        assert result["status"] == "signed off"
        assert result["session"]["session_id"] == "claude_2"

        # Verify instance is marked as available
        instances_scope = "test-machine:test-org/test-repo:instances"
        instances = server.storage.retrieve(instances_scope, "registry")
        assert instances["claude_2"] == "available"

    def test_sign_off_clears_current_session(self, initialized_server):
        """Test that sign_off clears the current session context."""
        server.sign_on()
        assert server.current_session is not None

        server.sign_off()

        assert server.current_session is None

    def test_sign_off_without_session(self, initialized_server):
        """Test signing off when no session is active."""
        result = server.sign_off()

        assert result["status"] == "no active session"


class TestDataTools:
    """Tests for store_data, retrieve_data, and delete_data tools."""

    def test_store_and_retrieve_data(self, initialized_server):
        """Test storing and retrieving data."""
        server.sign_on()

        server.store_data("session:claude_1", "test_key", "test_value")
        result = server.retrieve_data("session:claude_1", "test_key")

        assert result == "test_value"

    def test_store_complex_data(self, initialized_server):
        """Test storing complex data structures."""
        server.sign_on()

        test_data = {
            "current_issue": 15,
            "todos": [
                {"task": "Task 1", "status": "completed"},
                {"task": "Task 2", "status": "pending"}
            ]
        }

        server.store_data("session:claude_1", "complex_data", test_data)
        result = server.retrieve_data("session:claude_1", "complex_data")

        assert result == test_data

    def test_retrieve_nonexistent_key(self, initialized_server):
        """Test retrieving a key that doesn't exist."""
        server.sign_on()

        result = server.retrieve_data("session:claude_1", "nonexistent")

        assert result is None

    def test_delete_data(self, initialized_server):
        """Test deleting data."""
        server.sign_on()

        server.store_data("session:claude_1", "test_key", "test_value")
        deleted = server.delete_data("session:claude_1", "test_key")

        assert deleted is True

        result = server.retrieve_data("session:claude_1", "test_key")
        assert result is None

    def test_delete_nonexistent_key(self, initialized_server):
        """Test deleting a key that doesn't exist."""
        server.sign_on()

        deleted = server.delete_data("session:claude_1", "nonexistent")

        assert deleted is False

    def test_data_tools_require_sign_on(self, initialized_server):
        """Test that data tools require sign_on to be called first."""
        with pytest.raises(RuntimeError, match="Must call sign_on\\(\\) first"):
            server.store_data("session:claude_1", "key", "value")

        with pytest.raises(RuntimeError, match="Must call sign_on\\(\\) first"):
            server.retrieve_data("session:claude_1", "key")

        with pytest.raises(RuntimeError, match="Must call sign_on\\(\\) first"):
            server.delete_data("session:claude_1", "key")


class TestDiscoveryTools:
    """Tests for list_keys, list_scopes, and delete_scope tools."""

    def test_list_keys(self, initialized_server):
        """Test listing keys in a scope."""
        server.sign_on()

        server.store_data("session:claude_1", "key1", "value1")
        server.store_data("session:claude_1", "key2", "value2")
        server.store_data("session:claude_1", "key3", "value3")

        keys = server.list_keys("session:claude_1")

        assert set(keys) == {"key1", "key2", "key3"}

    def test_list_keys_empty_scope(self, initialized_server):
        """Test listing keys in an empty scope."""
        server.sign_on()

        keys = server.list_keys("session:claude_1")

        assert keys == []

    def test_list_scopes_all(self, initialized_server):
        """Test listing all scopes."""
        server.sign_on()

        # Create some scopes
        server.store_data("session:claude_1", "key", "value")
        server.store_data("session:claude_2", "key", "value")
        server.store_data("issue:15", "key", "value")

        scopes = server.list_scopes()

        # Scopes should be returned without the machine:project prefix
        assert "session:claude_1" in scopes
        assert "session:claude_2" in scopes
        assert "issue:15" in scopes
        assert "instances" in scopes  # Created by sign_on

    def test_list_scopes_with_pattern(self, initialized_server):
        """Test listing scopes with a pattern filter."""
        server.sign_on()

        # Create some scopes
        server.store_data("session:claude_1", "key", "value")
        server.store_data("session:claude_2", "key", "value")
        server.store_data("issue:15", "key", "value")

        scopes = server.list_scopes("session:*")

        assert "session:claude_1" in scopes
        assert "session:claude_2" in scopes
        assert "issue:15" not in scopes

    def test_delete_scope(self, initialized_server):
        """Test deleting an entire scope."""
        server.sign_on()

        # Create a scope with multiple keys
        server.store_data("issue:15", "key1", "value1")
        server.store_data("issue:15", "key2", "value2")

        deleted = server.delete_scope("issue:15")

        assert deleted is True

        # Verify scope is gone
        scopes = server.list_scopes()
        assert "issue:15" not in scopes

    def test_delete_nonexistent_scope(self, initialized_server):
        """Test deleting a scope that doesn't exist."""
        server.sign_on()

        deleted = server.delete_scope("nonexistent:scope")

        assert deleted is False

    def test_discovery_tools_require_sign_on(self, initialized_server):
        """Test that discovery tools require sign_on to be called first."""
        with pytest.raises(RuntimeError, match="Must call sign_on\\(\\) first"):
            server.list_keys("session:claude_1")

        with pytest.raises(RuntimeError, match="Must call sign_on\\(\\) first"):
            server.list_scopes()

        with pytest.raises(RuntimeError, match="Must call sign_on\\(\\) first"):
            server.delete_scope("session:claude_1")


class TestResources:
    """Tests for MCP resources."""

    def test_session_context_resource(self, initialized_server):
        """Test the session://context resource."""
        result_json = server.get_session_context()
        result = json.loads(result_json)

        assert result["machine"] == "test-machine"
        assert result["project"] == "test-org/test-repo"
        assert "instances" in result
        assert "instructions" in result
        assert result["first_available"] == "claude_1"

    def test_session_context_after_sign_on(self, initialized_server):
        """Test session context after signing on."""
        server.sign_on(session_id="claude_1")

        result_json = server.get_session_context()
        result = json.loads(result_json)

        assert result["current_session"] is not None
        assert result["current_session"]["session_id"] == "claude_1"

    def test_session_state_resource(self, initialized_server):
        """Test the session://state/{instance_id} resource."""
        # Sign on and create some state
        server.sign_on(session_id="claude_1")
        server.store_data("session:claude_1", "current_issue", 15)
        server.store_data("session:claude_1", "status", "in_progress")

        # Sign off and sign on as another instance to read the state
        server.sign_off()
        server.sign_on(session_id="claude_2")

        result_json = server.get_session_state("claude_1")
        result = json.loads(result_json)

        assert result["instance"] == "claude_1"
        assert result["current_issue"] == 15
        assert result["status"] == "in_progress"

    def test_session_state_nonexistent_instance(self, initialized_server):
        """Test reading state of a nonexistent instance."""
        server.sign_on()

        result_json = server.get_session_state("nonexistent")
        result = json.loads(result_json)

        assert "error" in result


class TestPrompts:
    """Tests for MCP prompts."""

    def test_startup_prompt_with_available_instances(self, initialized_server):
        """Test the startup prompt when instances are available."""
        result = server.startup()

        assert "test-org/test-repo" in result
        assert "test-machine" in result
        assert "claude_1" in result
        assert "sign_on()" in result

    def test_startup_prompt_no_available_instances(self, initialized_server):
        """Test the startup prompt when no instances are available."""
        # Mark all instances as taken
        instances_scope = "test-machine:test-org/test-repo:instances"
        instances = {f"claude_{i}": "taken" for i in range(1, 5)}
        server.storage.store(instances_scope, "registry", instances)

        result = server.startup()

        assert "All instances are currently taken" in result

    def test_sign_off_prompt_with_incomplete_tasks(self, initialized_server):
        """Test the sign-off prompt with incomplete tasks."""
        server.sign_on(session_id="claude_1")

        # Create some incomplete todos
        todos = [
            {"task": "Task 1", "status": "completed"},
            {"task": "Task 2", "status": "pending"},
            {"task": "Task 3", "status": "in_progress"}
        ]
        server.store_data("session:claude_1", "current_issue", 15)
        server.store_data("session:claude_1", "todos", todos)

        result = server.sign_off_prompt()

        assert "incomplete tasks" in result
        assert "Task 2" in result or "Task 3" in result

    def test_sign_off_prompt_all_complete(self, initialized_server):
        """Test the sign-off prompt when all tasks are complete."""
        server.sign_on(session_id="claude_1")

        # Create all completed todos
        todos = [
            {"task": "Task 1", "status": "completed"},
            {"task": "Task 2", "status": "completed"}
        ]
        server.store_data("session:claude_1", "current_issue", 15)
        server.store_data("session:claude_1", "todos", todos)

        result = server.sign_off_prompt()

        assert "Ready to Sign Off" in result or "complete" in result.lower()

    def test_sign_off_prompt_no_active_session(self, initialized_server):
        """Test the sign-off prompt when no session is active."""
        result = server.sign_off_prompt()

        assert "No active session" in result
