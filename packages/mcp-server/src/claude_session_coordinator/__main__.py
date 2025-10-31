"""Entry point for running Claude Session Coordinator as a module.

Run with: python -m claude_session_coordinator
"""

import argparse
import asyncio
import sys
from typing import Optional

from . import __version__
from .config import load_config, get_default_config
from .server import main


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="claude-session-coordinator",
        description="MCP server for coordinating multiple Claude AI sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the MCP server (default)
  python -m claude_session_coordinator

  # Show version
  python -m claude_session_coordinator --version

  # Validate configuration
  python -m claude_session_coordinator --validate-config

For more information, visit:
  https://github.com/BANCS-Norway/claude_session_coordinator
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="show version and exit"
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="validate configuration and exit"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable verbose logging"
    )

    return parser


def validate_config() -> int:
    """Validate the configuration.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    print("Validating configuration...")

    try:
        # Load configuration
        config = load_config()

        print("✓ Configuration loaded successfully")

        # Validate required fields
        if "storage" not in config:
            print("✗ Error: 'storage' section missing from configuration")
            return 1

        if "adapter" not in config["storage"]:
            print("✗ Error: 'storage.adapter' not specified")
            return 1

        adapter_type = config["storage"]["adapter"]
        print(f"✓ Storage adapter: {adapter_type}")

        if "config" not in config["storage"]:
            print("✗ Error: 'storage.config' section missing")
            return 1

        print(f"✓ Storage configuration: {config['storage']['config']}")

        # Validate session configuration
        if "session" in config:
            machine_id = config["session"].get("machine_id", "auto")
            project_detection = config["session"].get("project_detection", "git")
            print(f"✓ Machine ID: {machine_id}")
            print(f"✓ Project detection: {project_detection}")
        else:
            print("✓ Using default session configuration")

        # Try to import the adapter
        from .adapters import AdapterFactory

        # Test adapter creation
        try:
            adapter = AdapterFactory.create_adapter(config["storage"])
            print(f"✓ Adapter '{adapter_type}' loaded successfully")
            adapter.close()
        except Exception as e:
            print(f"✗ Error loading adapter: {e}")
            return 1

        print("\n✓ Configuration is valid!")
        return 0

    except FileNotFoundError as e:
        print(f"✗ Configuration file not found: {e}")
        print("\nUsing default configuration:")
        default_config = get_default_config()
        import json
        print(json.dumps(default_config, indent=2))
        print("\n✓ Default configuration is valid")
        return 0
    except Exception as e:
        print(f"✗ Error validating configuration: {e}")
        return 1


def run_server(verbose: bool = False) -> int:
    """Run the MCP server.

    Args:
        verbose: Enable verbose logging

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        if verbose:
            print("Starting Claude Session Coordinator MCP server...", file=sys.stderr)

        asyncio.run(main())
        return 0

    except KeyboardInterrupt:
        print("\nShutting down Claude Session Coordinator...", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def cli_main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Handle --validate-config
    if args.validate_config:
        return validate_config()

    # Default: run the server
    return run_server(verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(cli_main())
