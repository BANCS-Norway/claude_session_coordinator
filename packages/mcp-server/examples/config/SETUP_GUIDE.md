# MCP Client Setup Guide

This guide walks you through setting up the Claude Session Coordinator MCP server with your MCP client.

## Prerequisites

1. **Install the MCP server** - Follow the [Installation Guide](../../docs/installation.md)
2. **Verify installation**:
   ```bash
   claude-session-coordinator --version
   claude-session-coordinator --validate-config
   ```

## Setup for Claude Code

Claude Code is Anthropic's official CLI tool for using Claude with code.

### Configuration File Location

The Claude Code configuration is typically located at:
- **Linux/macOS**: `~/.config/claude-code/mcp.json`
- **Windows**: `%APPDATA%\claude-code\mcp.json`

### Setup Steps

1. **Open the configuration file**:
   ```bash
   # Create directory if it doesn't exist
   mkdir -p ~/.config/claude-code

   # Edit the configuration
   nano ~/.config/claude-code/mcp.json
   ```

2. **Add the server configuration**:

   If you installed with `pip install -e .` (editable mode):
   ```json
   {
     "mcpServers": {
       "claude-session-coordinator": {
         "command": "/path/to/your/venv/bin/python3",
         "args": ["-m", "claude_session_coordinator"],
         "cwd": "/path/to/your/project"
       }
     }
   }
   ```

   Replace:
   - `/path/to/your/venv/bin/python3` with the path to your virtual environment's Python
   - `/path/to/your/project` with your project directory

   To find your Python path:
   ```bash
   which python3  # After activating your venv
   ```

3. **Test the configuration**:
   ```bash
   # Start Claude Code
   claude-code

   # The session coordinator should be available
   # Try: "Show me the available MCP servers"
   ```

### Example Configurations

See the provided examples:
- `claude-code.json` - Basic setup with PYTHONPATH
- `claude-code-editable.json` - Setup for editable install (recommended)

## Setup for VS Code Continue

Continue is a VS Code extension that supports MCP servers.

### Configuration File Location

The Continue configuration is at:
- `~/.continue/config.json`

### Setup Steps

1. **Install Continue extension** in VS Code

2. **Open the configuration**:
   ```bash
   code ~/.continue/config.json
   ```

3. **Add the MCP server** to the `mcpServers` array:
   ```json
   {
     "mcpServers": [
       {
         "name": "claude-session-coordinator",
         "command": "/path/to/your/venv/bin/python3",
         "args": ["-m", "claude_session_coordinator"],
         "cwd": "/path/to/your/project"
       }
     ]
   }
   ```

4. **Reload VS Code**

### Example Configuration

See `vscode-continue.json` for a complete example.

## Setup for Cursor

Cursor is an AI-first code editor with MCP support.

### Configuration File Location

The Cursor configuration is at:
- **Linux/macOS**: `~/.cursor/mcp.json`
- **Windows**: `%APPDATA%\cursor\mcp.json`

### Setup Steps

1. **Create the configuration directory**:
   ```bash
   mkdir -p ~/.cursor
   ```

2. **Create/edit the configuration file**:
   ```bash
   nano ~/.cursor/mcp.json
   ```

3. **Add the server configuration**:
   ```json
   {
     "mcpServers": {
       "claude-session-coordinator": {
         "command": "/path/to/your/venv/bin/python3",
         "args": ["-m", "claude_session_coordinator"],
         "cwd": "/path/to/your/project"
       }
     }
   }
   ```

4. **Restart Cursor**

### Example Configuration

See `cursor.json` for a complete example.

## Custom Configuration

To customize the MCP server behavior, create a configuration file in your project:

```bash
# In your project directory
mkdir -p .claude
nano .claude/session-coordinator-config.json
```

Example custom configuration:

```json
{
  "server": {
    "port": 9999,
    "host": "localhost"
  },
  "storage": {
    "adapter": "local",
    "config": {
      "base_path": ".claude/session-state"
    }
  },
  "session": {
    "machine_id": "my-laptop",
    "project_detection": "git"
  }
}
```

## Verifying the Setup

After configuring your MCP client:

1. **Start your MCP client** (Claude Code, VS Code, Cursor)

2. **Check for available tools**:
   - The session coordinator should provide 8 tools
   - 2 resources (session context, session state)
   - 2 prompts (startup, sign-off)

3. **Test a simple command**:
   ```
   "Use the session coordinator to sign on as session claude_1"
   ```

4. **Check the storage**:
   ```bash
   # In your project directory
   ls -la .claude/session-state/
   ```

You should see JSON files created by the session coordinator.

## Troubleshooting

### Server Not Appearing

**Problem**: The MCP server doesn't show up in your client.

**Solutions**:
1. Check the Python path is correct:
   ```bash
   /path/to/your/venv/bin/python3 --version
   ```

2. Verify the package is installed:
   ```bash
   /path/to/your/venv/bin/python3 -m claude_session_coordinator --version
   ```

3. Check the configuration file syntax:
   ```bash
   cat ~/.config/claude-code/mcp.json | python3 -m json.tool
   ```

4. Look for error messages in your client's logs

### Permission Errors

**Problem**: Cannot create storage directory.

**Solution**: Ensure write permissions:
```bash
mkdir -p .claude/session-state
chmod 755 .claude/session-state
```

### Import Errors

**Problem**: Module not found errors.

**Solution**: Verify installation:
```bash
source /path/to/your/venv/bin/activate
pip install -e ".[dev]"
```

### Configuration Not Loading

**Problem**: Custom configuration not being used.

**Solution**: Check configuration file locations (in priority order):
1. `CLAUDE_SESSION_COORDINATOR_CONFIG` environment variable
2. `./.claude/session-coordinator-config.json` (project-local)
3. `~/.config/claude-session-coordinator/config.json` (user-global)

Validate your configuration:
```bash
claude-session-coordinator --validate-config
```

## Advanced Usage

### Using Environment Variables

You can set environment variables in your MCP client configuration:

```json
{
  "mcpServers": {
    "claude-session-coordinator": {
      "command": "/path/to/venv/bin/python3",
      "args": ["-m", "claude_session_coordinator"],
      "cwd": "/path/to/your/project",
      "env": {
        "CLAUDE_SESSION_COORDINATOR_CONFIG": "/path/to/custom/config.json"
      }
    }
  }
}
```

### Multiple Projects

To use the session coordinator across multiple projects, configure it separately for each:

**Project 1** (`~/projects/project-a`):
```json
{
  "mcpServers": {
    "session-coordinator-project-a": {
      "command": "/path/to/venv/bin/python3",
      "args": ["-m", "claude_session_coordinator"],
      "cwd": "/home/user/projects/project-a"
    }
  }
}
```

**Project 2** (`~/projects/project-b`):
```json
{
  "mcpServers": {
    "session-coordinator-project-b": {
      "command": "/path/to/venv/bin/python3",
      "args": ["-m", "claude_session_coordinator"],
      "cwd": "/home/user/projects/project-b"
    }
  }
}
```

Each project will have its own isolated session state in `.claude/session-state/`.

## Next Steps

After successful setup:

1. **Read the usage guide** - Learn how to use the MCP tools
2. **Try the examples** - Explore example workflows
3. **Customize for your workflow** - Adapt the configuration to your needs

## Support

- **Documentation**: [https://csc.bancs.no](https://csc.bancs.no)
- **Issues**: [GitHub Issues](https://github.com/BANCS-Norway/claude_session_coordinator/issues)
- **Repository**: [GitHub](https://github.com/BANCS-Norway/claude_session_coordinator)
