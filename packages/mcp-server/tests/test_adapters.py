"""Comprehensive tests for storage adapters."""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from claude_session_coordinator.adapters import (
    AdapterFactory,
    LocalFileAdapter,
    StorageAdapter,
    StorageError,
)


class TestLocalFileAdapter:
    """Tests for LocalFileAdapter."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def adapter(self, temp_dir: Path) -> LocalFileAdapter:
        """Create a LocalFileAdapter instance for testing."""
        return LocalFileAdapter(base_path=str(temp_dir))

    def test_initialization_creates_directory(self, temp_dir: Path) -> None:
        """Test that adapter creates storage directory on initialization."""
        storage_path = temp_dir / "test-storage"
        assert not storage_path.exists()

        LocalFileAdapter(base_path=str(storage_path))
        assert storage_path.exists()
        assert storage_path.is_dir()

    def test_scope_to_filename_conversion(self, adapter: LocalFileAdapter) -> None:
        """Test scope name to filename conversion."""
        scope = "laptop:BANCS-Norway/my-repo:session:claude_1"
        filename = adapter._scope_to_filename(scope)
        assert filename == "laptop__BANCS-Norway__my-repo__session__claude_1.json"

    def test_store_and_retrieve_string(self, adapter: LocalFileAdapter) -> None:
        """Test storing and retrieving a string value."""
        scope = "laptop:org/repo:session:test"
        key = "message"
        value = "Hello, World!"

        adapter.store(scope, key, value)
        retrieved = adapter.retrieve(scope, key)

        assert retrieved == value

    def test_store_and_retrieve_dict(self, adapter: LocalFileAdapter) -> None:
        """Test storing and retrieving a dictionary."""
        scope = "laptop:org/repo:session:test"
        key = "config"
        value = {"option1": True, "option2": 42, "nested": {"key": "value"}}

        adapter.store(scope, key, value)
        retrieved = adapter.retrieve(scope, key)

        assert retrieved == value

    def test_store_and_retrieve_list(self, adapter: LocalFileAdapter) -> None:
        """Test storing and retrieving a list."""
        scope = "laptop:org/repo:session:test"
        key = "items"
        value = [1, 2, "three", {"four": 4}]

        adapter.store(scope, key, value)
        retrieved = adapter.retrieve(scope, key)

        assert retrieved == value

    def test_store_and_retrieve_numeric_types(self, adapter: LocalFileAdapter) -> None:
        """Test storing and retrieving numeric types."""
        scope = "laptop:org/repo:session:test"

        # Integer
        adapter.store(scope, "int_val", 42)
        assert adapter.retrieve(scope, "int_val") == 42

        # Float
        adapter.store(scope, "float_val", 3.14159)
        assert adapter.retrieve(scope, "float_val") == 3.14159

        # Boolean
        adapter.store(scope, "bool_val", True)
        assert adapter.retrieve(scope, "bool_val") is True

        # None
        adapter.store(scope, "none_val", None)
        assert adapter.retrieve(scope, "none_val") is None

    def test_retrieve_nonexistent_key(self, adapter: LocalFileAdapter) -> None:
        """Test retrieving a non-existent key returns None."""
        scope = "laptop:org/repo:session:test"
        retrieved = adapter.retrieve(scope, "nonexistent")
        assert retrieved is None

    def test_retrieve_from_nonexistent_scope(self, adapter: LocalFileAdapter) -> None:
        """Test retrieving from a non-existent scope returns None."""
        retrieved = adapter.retrieve("nonexistent:scope:test:id", "key")
        assert retrieved is None

    def test_update_existing_key(self, adapter: LocalFileAdapter) -> None:
        """Test updating an existing key."""
        scope = "laptop:org/repo:session:test"
        key = "counter"

        adapter.store(scope, key, 1)
        assert adapter.retrieve(scope, key) == 1

        adapter.store(scope, key, 2)
        assert adapter.retrieve(scope, key) == 2

    def test_delete_existing_key(self, adapter: LocalFileAdapter) -> None:
        """Test deleting an existing key."""
        scope = "laptop:org/repo:session:test"
        key = "temp_data"

        adapter.store(scope, key, "to be deleted")
        assert adapter.retrieve(scope, key) == "to be deleted"

        result = adapter.delete(scope, key)
        assert result is True
        assert adapter.retrieve(scope, key) is None

    def test_delete_nonexistent_key(self, adapter: LocalFileAdapter) -> None:
        """Test deleting a non-existent key returns False."""
        scope = "laptop:org/repo:session:test"
        result = adapter.delete(scope, "nonexistent")
        assert result is False

    def test_delete_last_key_removes_file(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that deleting the last key in a scope removes the file."""
        scope = "laptop:org/repo:session:test"
        key = "only_key"

        adapter.store(scope, key, "value")
        scope_file = temp_dir / adapter._scope_to_filename(scope)
        assert scope_file.exists()

        adapter.delete(scope, key)
        assert not scope_file.exists()

    def test_list_keys_in_scope(self, adapter: LocalFileAdapter) -> None:
        """Test listing all keys in a scope."""
        scope = "laptop:org/repo:session:test"

        # Empty scope
        assert adapter.list_keys(scope) == []

        # Add some keys
        adapter.store(scope, "key1", "value1")
        adapter.store(scope, "key2", "value2")
        adapter.store(scope, "key3", "value3")

        keys = adapter.list_keys(scope)
        assert sorted(keys) == ["key1", "key2", "key3"]

    def test_list_keys_from_nonexistent_scope(self, adapter: LocalFileAdapter) -> None:
        """Test listing keys from a non-existent scope returns empty list."""
        keys = adapter.list_keys("nonexistent:scope:test:id")
        assert keys == []

    def test_list_scopes(self, adapter: LocalFileAdapter) -> None:
        """Test listing all scopes."""
        # Initially empty
        assert adapter.list_scopes() == []

        # Create some scopes
        adapter.store("laptop:org1/repo1:session:claude_1", "key", "value")
        adapter.store("laptop:org1/repo2:session:claude_2", "key", "value")
        adapter.store("desktop:org2/repo1:session:claude_1", "key", "value")

        scopes = adapter.list_scopes()
        assert len(scopes) == 3
        assert "laptop:org1/repo1:session:claude_1" in scopes
        assert "laptop:org1/repo2:session:claude_2" in scopes
        assert "desktop:org2/repo1:session:claude_1" in scopes

    def test_list_scopes_with_pattern(self, adapter: LocalFileAdapter) -> None:
        """Test listing scopes with pattern matching."""
        # Create some scopes
        adapter.store("laptop:org1/repo1:session:claude_1", "key", "value")
        adapter.store("laptop:org1/repo2:session:claude_2", "key", "value")
        adapter.store("desktop:org2/repo1:session:claude_1", "key", "value")
        adapter.store("laptop:org1/repo1:task:task_1", "key", "value")

        # Pattern: all laptop scopes
        scopes = adapter.list_scopes("laptop:*")
        assert len(scopes) == 3
        assert all(s.startswith("laptop:") for s in scopes)

        # Pattern: all session scopes
        scopes = adapter.list_scopes("*:session:*")
        assert len(scopes) == 3
        assert all(":session:" in s for s in scopes)

        # Pattern: specific organization
        scopes = adapter.list_scopes("*:org1/*")
        assert len(scopes) == 3
        assert all("org1/" in s for s in scopes)

    def test_delete_scope(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test deleting an entire scope."""
        scope = "laptop:org/repo:session:test"

        # Add multiple keys to the scope
        adapter.store(scope, "key1", "value1")
        adapter.store(scope, "key2", "value2")

        scope_file = temp_dir / adapter._scope_to_filename(scope)
        assert scope_file.exists()

        # Delete the scope
        result = adapter.delete_scope(scope)
        assert result is True
        assert not scope_file.exists()

    def test_delete_nonexistent_scope(self, adapter: LocalFileAdapter) -> None:
        """Test deleting a non-existent scope returns False."""
        result = adapter.delete_scope("nonexistent:scope:test:id")
        assert result is False

    def test_metadata_timestamps(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that metadata includes created_at and updated_at timestamps."""
        scope = "laptop:org/repo:session:test"
        key = "data"

        # Store initial value
        adapter.store(scope, key, "initial")

        # Load the scope file directly to check metadata
        scope_file = temp_dir / adapter._scope_to_filename(scope)
        with open(scope_file) as f:
            scope_data = json.load(f)

        assert "metadata" in scope_data
        assert key in scope_data["metadata"]
        assert "created_at" in scope_data["metadata"][key]
        assert "updated_at" in scope_data["metadata"][key]

        created_at = scope_data["metadata"][key]["created_at"]

        # Update the value
        adapter.store(scope, key, "updated")

        # Check that updated_at changed but created_at didn't
        with open(scope_file) as f:
            scope_data = json.load(f)

        assert scope_data["metadata"][key]["created_at"] == created_at
        assert scope_data["metadata"][key]["updated_at"] >= created_at

    def test_multiple_scopes_independent(self, adapter: LocalFileAdapter) -> None:
        """Test that different scopes are independent."""
        scope1 = "laptop:org/repo1:session:test1"
        scope2 = "laptop:org/repo2:session:test2"
        key = "shared_key"

        adapter.store(scope1, key, "value1")
        adapter.store(scope2, key, "value2")

        assert adapter.retrieve(scope1, key) == "value1"
        assert adapter.retrieve(scope2, key) == "value2"

    def test_close_method(self, adapter: LocalFileAdapter) -> None:
        """Test that close method can be called without error."""
        # For LocalFileAdapter, close() is a no-op, but should not raise
        adapter.close()

    def test_invalid_json_raises_error(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that corrupted JSON file raises StorageError."""
        scope = "laptop:org/repo:session:test"
        scope_file = temp_dir / adapter._scope_to_filename(scope)

        # Write invalid JSON
        with open(scope_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(StorageError, match="Invalid JSON"):
            adapter.retrieve(scope, "key")

    def test_directory_creation_failure(self, temp_dir: Path) -> None:
        """Test that OSError during directory creation raises StorageError."""
        from unittest.mock import patch

        # Create a file where we want to create a directory
        bad_path = temp_dir / "file_not_dir"
        bad_path.write_text("I'm a file, not a directory")

        # Try to create adapter with this path as base (should fail)
        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(StorageError, match="Failed to create storage directory"):
                LocalFileAdapter(base_path=str(bad_path / "subdir"))

    def test_filename_to_scope_short_name(self, adapter: LocalFileAdapter) -> None:
        """Test filename_to_scope fallback for short filenames."""
        # Test with less than 4 parts (uses fallback logic)
        short_filename = "one__two.json"
        scope = adapter._filename_to_scope(short_filename)
        assert scope == "one:two"

        # Test with 2 parts
        filename = "machine__org.json"
        scope = adapter._filename_to_scope(filename)
        assert scope == "machine:org"

    def test_read_scope_file_os_error(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that OSError when reading scope file raises StorageError."""
        from unittest.mock import patch

        scope = "laptop:org/repo:session:test"

        # Create the file first
        adapter.store(scope, "key", "value")

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Read permission denied")):
            with pytest.raises(StorageError, match="Failed to read scope file"):
                adapter.retrieve(scope, "key")

    def test_save_non_json_serializable_value(self, adapter: LocalFileAdapter) -> None:
        """Test that non-JSON-serializable values raise StorageError."""
        scope = "laptop:org/repo:session:test"

        # Try to store a non-serializable object (like a function)
        class NonSerializable:
            pass

        with pytest.raises(StorageError, match="not JSON-serializable"):
            adapter.store(scope, "key", NonSerializable())

    def test_save_scope_file_os_error(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that OSError when saving scope file raises StorageError."""
        from unittest.mock import mock_open, patch

        scope = "laptop:org/repo:session:test"

        # Mock open to raise OSError on write
        m = mock_open()
        m.side_effect = OSError("Write permission denied")

        with patch("builtins.open", m):
            with pytest.raises(StorageError, match="Failed to write scope file"):
                adapter.store(scope, "key", "value")

    def test_delete_scope_file_os_error(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that OSError when deleting scope file raises StorageError."""
        from unittest.mock import patch

        scope = "laptop:org/repo:session:test"
        key = "only_key"

        # Store a value
        adapter.store(scope, key, "value")

        # Mock unlink to raise OSError
        with patch("pathlib.Path.unlink", side_effect=OSError("Delete permission denied")):
            with pytest.raises(StorageError, match="Failed to delete scope file"):
                adapter.delete(scope, key)

    def test_delete_key_from_multi_key_scope(
        self, adapter: LocalFileAdapter, temp_dir: Path
    ) -> None:
        """Test deleting one key from a scope with multiple keys."""
        scope = "laptop:org/repo:session:test"

        # Store multiple keys
        adapter.store(scope, "key1", "value1")
        adapter.store(scope, "key2", "value2")
        adapter.store(scope, "key3", "value3")

        # Delete one key
        result = adapter.delete(scope, "key2")
        assert result is True

        # Verify the file still exists and other keys remain
        scope_file = temp_dir / adapter._scope_to_filename(scope)
        assert scope_file.exists()

        assert adapter.retrieve(scope, "key1") == "value1"
        assert adapter.retrieve(scope, "key2") is None
        assert adapter.retrieve(scope, "key3") == "value3"

    def test_list_scopes_os_error(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that OSError when listing scopes raises StorageError."""
        from unittest.mock import patch

        # Mock glob to raise OSError
        with patch("pathlib.Path.glob", side_effect=OSError("List permission denied")):
            with pytest.raises(StorageError, match="Failed to list scope files"):
                adapter.list_scopes()

    def test_delete_scope_os_error(self, adapter: LocalFileAdapter, temp_dir: Path) -> None:
        """Test that OSError when deleting scope raises StorageError."""
        from unittest.mock import patch

        scope = "laptop:org/repo:session:test"

        # Create the scope
        adapter.store(scope, "key", "value")

        # Mock unlink to raise OSError
        with patch("pathlib.Path.unlink", side_effect=OSError("Delete permission denied")):
            with pytest.raises(StorageError, match="Failed to delete scope file"):
                adapter.delete_scope(scope)


class TestAdapterFactory:
    """Tests for AdapterFactory."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_local_adapter(self, temp_dir: Path) -> None:
        """Test creating a local adapter from configuration."""
        config = {"adapter": "local", "config": {"base_path": str(temp_dir)}}

        adapter = AdapterFactory.create_adapter(config)
        assert isinstance(adapter, LocalFileAdapter)
        assert adapter.base_path == temp_dir

    def test_create_local_adapter_default_path(self) -> None:
        """Test creating local adapter with default path."""
        config = {"adapter": "local", "config": {}}

        adapter = AdapterFactory.create_adapter(config)
        assert isinstance(adapter, LocalFileAdapter)
        assert str(adapter.base_path).endswith(".claude/session-state")

    def test_create_adapter_missing_type(self) -> None:
        """Test that missing adapter type raises error."""
        config = {"config": {}}

        with pytest.raises(StorageError, match="Adapter type not specified"):
            AdapterFactory.create_adapter(config)

    def test_create_adapter_unknown_type(self) -> None:
        """Test that unknown adapter type raises error."""
        config = {"adapter": "unknown", "config": {}}

        with pytest.raises(StorageError, match="Unknown adapter type"):
            AdapterFactory.create_adapter(config)

    def test_register_custom_adapter(self, temp_dir: Path) -> None:
        """Test registering and creating a custom adapter."""

        class CustomAdapter(StorageAdapter):
            def __init__(self, custom_param: str) -> None:
                self.custom_param = custom_param

            def store(self, scope: str, key: str, value: Any) -> None:
                pass

            def retrieve(self, scope: str, key: str) -> Any | None:
                return None

            def delete(self, scope: str, key: str) -> bool:
                return False

            def list_keys(self, scope: str) -> list[str]:
                return []

            def list_scopes(self, pattern: str | None = None) -> list[str]:
                return []

            def delete_scope(self, scope: str) -> bool:
                return False

            def close(self) -> None:
                pass

        def create_custom(config: dict[str, Any]) -> CustomAdapter:
            return CustomAdapter(custom_param=config.get("custom_param", "default"))

        # Register the custom adapter
        AdapterFactory.register_adapter("custom", create_custom)

        # Create instance
        config = {"adapter": "custom", "config": {"custom_param": "test_value"}}
        adapter = AdapterFactory.create_adapter(config)

        assert isinstance(adapter, CustomAdapter)
        assert adapter.custom_param == "test_value"

    def test_custom_adapter_creation_failure(self) -> None:
        """Test that exceptions during custom adapter creation are handled."""

        def failing_creator(config: dict[str, Any]) -> StorageAdapter:
            raise ValueError("Creation failed!")

        # Register a failing adapter
        AdapterFactory.register_adapter("failing", failing_creator)

        config = {"adapter": "failing", "config": {}}

        with pytest.raises(StorageError, match="Failed to create adapter"):
            AdapterFactory.create_adapter(config)


class TestStorageAdapterInterface:
    """Tests to ensure the interface contract is maintained."""

    def test_local_adapter_implements_interface(self) -> None:
        """Test that LocalFileAdapter implements StorageAdapter."""
        assert issubclass(LocalFileAdapter, StorageAdapter)

    def test_adapter_has_all_required_methods(self) -> None:
        """Test that StorageAdapter defines all required methods."""
        required_methods = [
            "store",
            "retrieve",
            "delete",
            "list_keys",
            "list_scopes",
            "delete_scope",
            "close",
        ]

        for method in required_methods:
            assert hasattr(StorageAdapter, method)
            assert callable(getattr(StorageAdapter, method))
