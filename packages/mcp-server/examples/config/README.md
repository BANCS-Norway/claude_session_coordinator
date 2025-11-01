# MCP Client Configuration Examples

This directory contains configuration examples for using the Claude Session
Coordinator MCP server with various MCP clients.

## Available Examples

- **Claude Code** - Configuration for Anthropic's official Claude Code CLI
- **VS Code Continue** - Configuration for the Continue extension in VS Code
- **Cursor** - Configuration for Cursor IDE

## General Setup

1. Install the MCP server (see [Installation Guide](../../docs/installation.md))
2. Locate your MCP client's configuration file
3. Add the Claude Session Coordinator server configuration
4. Restart your MCP client

## Important Notes

- **Paths**: Update all file paths to match your system
- **Python**: Ensure the Python path points to your virtual environment or
  system Python 3.10+
- **Working directory**: Set to the root of your project repository
- **Server location**: Update the path to where you cloned the repository

## Testing the Configuration

After adding the configuration, verify the server is working:

```bash
# From your project directory
claude-session-coordinator --validate-config
```

## Troubleshooting

If the MCP server doesn't appear in your client:

1. **Check paths**: Ensure all paths in the config are absolute and correct
2. **Check Python**: Verify Python 3.10+ is installed: `python3 --version`
3. **Check installation**: Verify the package is installed: `pip show claude-session-coordinator`
4. **Check logs**: Look for error messages in your MCP client's logs
5. **Restart client**: Completely restart your MCP client after configuration changes

## Support

For issues or questions:

- [GitHub Issues](https://github.com/BANCS-Norway/claude_session_coordinator/issues)
- [Documentation](https://csc.bancs.no)
