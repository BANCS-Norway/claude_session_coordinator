# Claude Session Coordinator

A flexible MCP server enabling multiple Claude AI sessions to coordinate work across machines through shared state management.

## ⚠️ Important Disclaimers

**No Affiliation:** Claude Session Coordinator (CSC) and BANCS AS are not affiliated with, employed by, endorsed by, or sponsored by Anthropic PBC. We receive no compensation or support from Anthropic. This is an independent community project.

**Use at Your Own Risk:** This software is provided "as is" without warranty of any kind. Users assume all risks associated with using this tool.

**No Official Support:** Anthropic has not reviewed, approved, or endorsed this tool. Anthropic is not responsible for this tool's functionality or support.

## Overview

Claude Session Coordinator provides a storage adapter-based MCP server that enables multiple Claude sessions to:
- Share state and coordinate work
- Avoid conflicts when working in parallel
- Track progress across sessions
- Support multiple workflow patterns

**Core Philosophy:** Flexible primitives over opinionated workflows. The server provides simple, universal building blocks that support any coordination pattern.

## Project Structure

This is a monorepo containing:

- **`packages/mcp-server/`** - Python MCP server with storage adapters
- **`packages/homepage/`** - Public documentation site (for Phase 2+ launch)
- **`docs/`** - Shared architectural and implementation documentation

## Quick Start

### Installation (Phase 1 - Development)

```bash
cd packages/mcp-server
pip install -e .
```

### Configuration

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "session-coordinator": {
      "command": "python",
      "args": ["-m", "claude_session_coordinator"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

## Features

### Storage Adapters

- **Local File Adapter** (Phase 1) - Simple JSON file storage
- **Redis Adapter** (Phase 2+) - Cross-machine coordination
- **Custom Adapters** - Implement your own backend

### MCP Tools

- `sign_on()` - Claim an instance and establish session identity
- `store_data()` - Store data in scoped contexts
- `retrieve_data()` - Retrieve stored data
- `list_keys()` - Discover available keys in a scope
- `list_scopes()` - List all scopes with optional filtering
- `delete_data()` - Remove specific data
- `delete_scope()` - Remove entire scope
- `sign_off()` - Release session instance

### MCP Resources

- `session://context` - Current session state and available instances
- `session://state/{id}` - Read other sessions' state (coordination)

### MCP Prompts

- `startup` - Guides Claude through sign-on process
- `sign-off` - Guides proper session release

## Development Status

**Phase 1** (Current): MCP Server Core Implementation
- Storage adapter architecture
- Local file adapter
- Core MCP tools, resources, and prompts
- Internal testing and iteration

**Phase 2** (Future): Public Launch
- Homepage and documentation site
- PyPI publishing
- Community announcement

**Phase 3+** (Future): Ecosystem
- VS Code extension
- CLI tools
- Web dashboard
- Additional adapters

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Storage Adapters](docs/architecture/storage-adapters.md)
- [Implementation Plan](docs/implementation/phase-1-plan.md)
- [Use Cases](docs/use-cases/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Support

This is a community project. For issues and feature requests, please use GitHub Issues.

---

**Built by the community, for the community** 🚀
