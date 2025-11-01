# Installation Guide

## Requirements

- Python 3.10, 3.11, or 3.12
- pip (Python package manager)
- Git (for project detection)

## Installation

### Option 1: Editable Install (Development)

For development or if you want to modify the code:

```bash
# Clone the repository
git clone https://github.com/BANCS-Norway/claude_session_coordinator.git
cd claude_session_coordinator

# Navigate to the MCP server package
cd packages/mcp-server

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Option 2: Install with Development Tools

To install with development dependencies (testing, linting, type checking):

```bash
pip install -e ".[dev]"
```

### Option 3: Install with Redis Support

To install with Redis adapter support (for future multi-machine coordination):

```bash
pip install -e ".[redis]"
```

### Option 4: Install Everything

To install with all optional dependencies:

```bash
pip install -e ".[dev,redis]"
```

## Verification

After installation, verify everything works correctly:

### 1. Check Version

```bash
# Using the console script
claude-session-coordinator --version

# Or using module invocation
python -m claude_session_coordinator --version
```

Expected output:
```
claude-session-coordinator 0.1.0
```

### 2. Validate Configuration

```bash
# Using the console script
claude-session-coordinator --validate-config

# Or using module invocation
python -m claude_session_coordinator --validate-config
```

Expected output:
```
Validating configuration...
✓ Configuration loaded successfully
✓ Storage adapter: local
✓ Storage configuration: {'base_path': '.claude/session-state'}
✓ Machine ID: auto
✓ Project detection: git
✓ Adapter 'local' loaded successfully

✓ Configuration is valid!
```

### 3. Test the Server

To test the server starts correctly:

```bash
# Start the server (it will run until you press Ctrl+C)
claude-session-coordinator --verbose
```

You should see output indicating the server has started. Press `Ctrl+C` to stop the server.

## Configuration

### Claude Code MCP Configuration

For Claude Code users, the easiest way to configure the MCP server is using the `.mcp.json` file:

1. **Copy the template** (from the repository root):
   ```bash
   cp .mcp.json.template .mcp.json
   ```

2. **Edit the file** with your actual paths:
   ```bash
   nano .mcp.json
   ```

3. **Update the placeholder paths**:
   ```json
   {
     "mcpServers": {
       "claude-session-coordinator": {
         "command": "/path/to/your/python3",
         "args": [
           "-m",
           "claude_session_coordinator"
         ],
         "env": {},
         "cwd": "/path/to/claude_session_coordinator"
       }
     }
   }
   ```

   Replace:
   - `/path/to/your/python3` - Path to your Python interpreter (e.g., `/home/user/python.dev/bin/python3`)
   - `/path/to/claude_session_coordinator` - Path to the repository root

4. **Restart Claude Code** - The session coordinator will be available automatically

**Note:** The `.mcp.json` file is gitignored (contains machine-specific paths). Each developer should create their own copy from the template.

### Alternative Configuration Methods

#### MCP Client Configuration Examples

See the [examples/config/](../examples/config/) directory for additional configuration examples for different MCP clients.

### Default Configuration

By default, the MCP server uses:
- **Storage adapter**: Local file storage
- **Storage location**: `.claude/session-state/` (created automatically)
- **Machine ID**: Auto-detected from hostname
- **Project detection**: Git repository (auto-detected)

### Custom Configuration

To customize the configuration, create a configuration file in one of these locations (in priority order):

1. **Project-local** (recommended): `./.claude/session-coordinator-config.json`
2. **User-global**: `~/.config/claude-session-coordinator/config.json`
3. **Environment variable**: Set `CLAUDE_SESSION_COORDINATOR_CONFIG` to the path of your config file

Example configuration file:

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
    "machine_id": "auto",
    "project_detection": "git"
  }
}
```

## Next Steps

After successful installation:

1. **Configure your MCP client**:
   - **Claude Code users**: Copy and edit `.mcp.json.template` (see [Claude Code MCP Configuration](#claude-code-mcp-configuration) above)
   - **Other MCP clients**: See [examples/config/](../examples/config/) for configuration examples
2. **Read the usage guide** - Learn how to use the session coordination tools
3. **Start coordinating sessions** - Begin using multiple Claude sessions with shared state

## Troubleshooting

### Issue: `claude-session-coordinator: command not found`

**Solution**: Make sure your virtual environment is activated and the package is installed:

```bash
source venv/bin/activate
pip install -e .
```

### Issue: Module import errors

**Solution**: Verify all dependencies are installed:

```bash
pip install -e ".[dev]"
```

### Issue: Configuration validation fails

**Solution**: Check your configuration file syntax:

```bash
cat .claude/session-coordinator-config.json | python -m json.tool
```

### Issue: Storage directory permission errors

**Solution**: Ensure you have write permissions to the storage directory:

```bash
mkdir -p .claude/session-state
chmod 755 .claude/session-state
```

### Issue: Git repository not detected

**Solution**: Ensure you're in a git repository:

```bash
git status
```

If not in a git repository, initialize one:

```bash
git init
```

## Platform-Specific Notes

### Linux

No special requirements. Python 3.10+ should work out of the box.

### macOS

No special requirements. Python 3.10+ should work out of the box. You may need to install Python via Homebrew:

```bash
brew install python@3.11
```

### Windows

Install Python 3.10+ from [python.org](https://www.python.org/downloads/).

When activating the virtual environment on Windows:

```bash
# PowerShell
venv\Scripts\Activate.ps1

# Command Prompt
venv\Scripts\activate.bat
```

## Uninstallation

To uninstall the package:

```bash
pip uninstall claude-session-coordinator
```

To also remove the storage data:

```bash
rm -rf .claude/session-state
```

## Support

- **Issues**: [GitHub Issues](https://github.com/BANCS-Norway/claude_session_coordinator/issues)
- **Documentation**: [Project Documentation](https://csc.bancs.no)
- **Repository**: [GitHub Repository](https://github.com/BANCS-Norway/claude_session_coordinator)
