"""Machine and project detection utilities."""

import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, cast


def detect_machine_id(config: Dict[str, Any]) -> str:
    """Detect machine identifier.

    Args:
        config: Configuration dictionary

    Returns:
        Machine identifier (hostname or configured value)
    """
    machine_id_setting = config.get("session", {}).get("machine_id", "auto")

    if machine_id_setting == "auto":
        # Use hostname
        return socket.gethostname()
    else:
        # Use configured value
        return cast(str, machine_id_setting)


def detect_project_id(config: Dict[str, Any]) -> str:
    """Detect project identifier from git or directory.

    Args:
        config: Configuration dictionary

    Returns:
        Project identifier (e.g., "BANCS-Norway/claude_session_coordinator")
    """
    detection_method = config.get("session", {}).get("project_detection", "git")

    if detection_method == "git":
        return _detect_project_from_git()
    elif detection_method == "directory":
        return _detect_project_from_directory()
    else:
        raise ValueError(f"Unknown project detection method: {detection_method}")


def _detect_project_from_git() -> str:
    """Detect project from git remote URL.

    Returns:
        Project identifier (owner/repo) from git remote

    Raises:
        subprocess.CalledProcessError: If git command fails
    """
    try:
        # Get git remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        remote_url = result.stdout.strip()

        # Parse owner/repo from URL
        # Supports formats:
        #   git@github.com:BANCS-Norway/claude_session_coordinator.git
        #   https://github.com/BANCS-Norway/claude_session_coordinator.git

        if remote_url.startswith("git@"):
            # SSH format: git@github.com:owner/repo.git
            parts = remote_url.split(":")
            if len(parts) >= 2:
                owner_repo = parts[1].replace(".git", "")
                return owner_repo
        elif remote_url.startswith("http://") or remote_url.startswith("https://"):
            # HTTPS format: https://github.com/owner/repo.git
            parts = remote_url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1].replace(".git", "")
                return f"{owner}/{repo}"

        # Fallback to directory name if parsing fails
        return _detect_project_from_directory()

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Git command failed, fallback to directory name
        return _detect_project_from_directory()


def _detect_project_from_directory() -> str:
    """Detect project from current directory name.

    Returns:
        Current directory name as project identifier
    """
    return Path.cwd().name
