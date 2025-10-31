# Dev Squad Registry - Technical Documentation

## Overview

The Dev Squad Registry (`DEV-SQUAD.md`) is a **dual-purpose architectural component** that serves as both:

1. **Human Coordination Layer** - Personality-driven session tracking
2. **Machine State Store** - Parseable metadata for MCP server coordination

This document explains the technical structure and usage of the enhanced registry format.

## File Structure

### YAML Frontmatter (Machine-Readable)

The registry begins with YAML frontmatter containing structured metadata:

```yaml
---
registry_version: 1.1.0
project: BANCS-Norway/claude_session_coordinator
machine_id: auto
last_updated: 2025-10-31T12:00:00Z
coordination_enabled: true
storage_backend: local

# Session Definitions
sessions:
  cipher:
    id: DS-02
    status: active | reserve | standby
    specialization: technical_documentation
    genetic_enhancement: analytical_precision
    current_mission: null | issue_number
    worktree: null | path
    priority: high | normal | low

# ... more sessions ...

# Allied Support
allied_support:
  anchor:
    id: DS-07
    status: backup | reserve
    # ... similar structure ...
---
```

### Markdown Content (Human-Readable)

Following the frontmatter is rich markdown documentation:

- **Agent roster** with personalities and specializations
- **Active Session State** table showing real-time coordination status
- **Coordination Protocols** for sign-on/sign-off and handoffs
- **Task statistics** and Performance Highlights
- **Usage examples** demonstrating workflows

## Session States

### Status Values

- **`reserve`**: Session available but not currently active
- **`active`**: Session currently working on an issue
- **`standby`**: Session was active, now paused (ready to resume)
- **`backup`**: Allied support, available when needed

### State Transitions

```
reserve → active     (sign_on)
active → standby     (pause work)
active → reserve     (sign_off, task complete)
standby → active     (resume work)
```

## Active Session State Section

### Real-Time Coordination Table

The Active Session State table provides at-a-glance status:

```markdown
| Session | Status | Task | Worktree | Started | Last Activity |
|---------|--------|------|----------|---------|---------------|
| cipher | 🟢 Active | #25 | .worktrees/issue-25 | 2025-10-31 10:30 | 2025-10-31 11:45 |
| link | 🔵 Standby | - | - | - | - |
```

**Status Indicators:**
- 🟢 Active - Currently working
- 🔵 Standby - Available, not working
- 🟡 Paused - Work in progress, temporarily stopped
- 🔴 Blocked - Cannot proceed

### Session State Details (JSON)

Detailed state for each active session:

```json
{
  "session_id": "cipher",
  "status": "active",
  "current_task": {
    "issue": 25,
    "title": "Add Redis storage adapter",
    "worktree": ".worktrees/issue-25",
    "branch": "feat/25-redis-adapter"
  },
  "started_at": "2025-10-31T10:30:00Z",
  "last_activity": "2025-10-31T11:45:00Z",
  "progress": {
    "phase": "implementation",
    "completion": 60,
    "next_steps": ["Add connection pooling", "Write tests"]
  }
}
```

## Coordination Protocols

### Sign-On Protocol

1. Read Active Session State to check availability
2. Select appropriate agent based on work type
3. Update session status to `active`
4. Create worktree if needed
5. Add task details to session state

### Sign-Off Protocol

1. Commit all work
2. Update task statistics
3. Set status to `reserve` or `standby`
4. Clean up worktree if task complete
5. Leave handoff notes if needed

### Collision Avoidance

Before starting work:
1. Check if issue already has active session
2. Check if worktree already exists
3. Coordinate with other sessions if needed
4. Never force operations on another session's workspace

## MCP Server Integration (Phase 2)

### Resource Endpoints

The MCP server will expose these resources:

**`session://context`**
- Parses YAML metadata
- Returns available sessions
- Shows current active sessions
- Recommends next session based on work type

**`session://state/{session_id}`**
- Returns full state for specific session
- Includes current task details
- Shows progress and next steps
- Enables cross-session coordination

### MCP Tools Integration

| MCP Tool | Registry Update | Example |
|----------|-----------------|---------|
| `sign_on(session_id)` | Sets status → `active` | Cipher takes issue #25 |
| `sign_off()` | Sets status → `reserve` | Cipher completes work |
| `store_data(scope, key, value)` | Updates session state | Save progress data |
| `retrieve_data(scope, key)` | Reads session state | Check other session |

### Automatic Updates (Phase 3)

Future automation will:
- Update Active Session State table on sign-on/sign-off
- Track task progress automatically
- Detect and warn about collisions
- Generate session analytics
- Maintain historical task data

## Parsing the Registry

### Python Example

```python
import yaml
from pathlib import Path

def parse_dev_squad_registry(registry_path: str = ".claude/DEV-SQUAD.md"):
    """Parse the Dev Squad registry file."""
    with open(registry_path, 'r') as f:
        content = f.read()

    # Split frontmatter and markdown
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            markdown = parts[2].strip()
            return {
                'metadata': frontmatter,
                'content': markdown
            }

    raise ValueError("Invalid registry format")

# Usage
registry = parse_dev_squad_registry()
sessions = registry['metadata']['sessions']
available = [s for s, data in sessions.items() if data['status'] == 'reserve']
print(f"Available sessions: {available}")
```

### TypeScript Example

```typescript
import * as yaml from 'js-yaml';
import * as fs from 'fs';

interface SessionDefinition {
  id: string;
  status: 'active' | 'reserve' | 'standby' | 'backup';
  specialization: string;
  genetic_enhancement: string;
  current_mission: number | null;
  worktree: string | null;
  priority: 'high' | 'normal' | 'low';
}

interface RegistryMetadata {
  registry_version: string;
  project: string;
  machine_id: string;
  last_updated: string;
  coordination_enabled: boolean;
  storage_backend: string;
  sessions: Record<string, SessionDefinition>;
  allied_support: Record<string, SessionDefinition>;
}

function parseDevSquadRegistry(registryPath: string = '.claude/DEV-SQUAD.md'): RegistryMetadata {
  const content = fs.readFileSync(registryPath, 'utf-8');
  const parts = content.split('---');

  if (parts.length < 3) {
    throw new Error('Invalid registry format');
  }

  return yaml.load(parts[1]) as RegistryMetadata;
}

// Usage
const registry = parseDevSquadRegistry();
console.log(`Available sessions: ${Object.keys(registry.sessions)}`);
```

## Dev Squad Agents

### Core Agents

- **Sage (DS-01)**: Coordination & strategy - Project leadership, tracking issues
- **Cipher (DS-02)**: Technical documentation - Implementation guides, complex analysis
- **Forge (DS-03)**: Refactoring & breaking changes - Major refactors, system rebuilds
- **Apex (DS-04)**: Precision fixes - Critical bugs, surgical code changes
- **Link (DS-05)**: Integrations - API connections, communication systems
- **Scout (DS-06)**: Exploration - Experimental features, research

### Allied Support

- **Anchor (DS-07)**: Backup & leadership - When primary agents are fully deployed

## Version History

### v1.1.0 (Current)
- Added machine-readable YAML metadata block
- Added Active Session State section for real-time coordination
- Added Coordination Protocols (sign-on, sign-off, collision avoidance, handoffs)
- Enhanced with JSON state examples
- Added Enhanced Workflow Examples
- Improved session coordination capabilities
- Foundation for MCP Server integration (Phase 2)

### v1.0.0 (Initial)
- Initial Dev Squad naming convention
- Agent roster with specializations
- Task statistics tracking
- Deployment guide
- Performance highlights
- Basic coordination examples

## Private Alternative: Clone Force 99

For personal/internal use, you can maintain a Star Wars-themed version:

**Private (local only - NOT committed to git):**
- `.claude/CLONES.md` - Clone Force 99 version
- Uses character names: Hunter, Tech, Wrecker, Crosshair, Echo, Omega, Rex
- Add to `.gitignore` to keep it local

**Configuration:**
```json
{
  "session_registry": {
    "file": ".claude/CLONES.md",  // or DEV-SQUAD.md
    "format": "v1.1.0"
  }
}
```

**Why keep both?**
- Fun personality-driven names for personal use
- IP-safe names for public/open source
- Same technical functionality
- User preference

## Best Practices

### For Humans

1. **Check Active Session State** before starting work
2. **Update your status** when signing on/off
3. **Use personality** - embrace the agent identity
4. **Coordinate** - avoid conflicts with other sessions
5. **Document tasks** - update task statistics

### For MCP Server Implementation

1. **Parse carefully** - validate YAML structure
2. **Handle errors** - gracefully fallback if parsing fails
3. **Update atomically** - prevent race conditions
4. **Preserve content** - don't corrupt markdown when updating
5. **Validate status** - ensure state transitions are valid

### For Development

1. **Test parsing** - ensure both Python and TypeScript can read
2. **Validate YAML** - syntax errors break parsing
3. **Version carefully** - update registry_version on changes
4. **Document changes** - maintain Version History section
5. **Backward compatible** - don't break existing readers

## Future Enhancements (Roadmap)

### Phase 2: MCP Integration
- MCP server reads metadata
- Resources expose session states
- Tools update registry automatically
- Session handoff automation

### Phase 3: Advanced Features
- Real-time dashboard
- Session analytics
- Conflict detection
- Historical task data
- Cross-machine coordination (with Redis)

### Phase 4: Extended Capabilities
- Custom agent definitions
- Dynamic specialization
- Task scheduling
- Performance metrics
- Integration with CI/CD

## File Locations

- **Production:** `.claude/DEV-SQUAD.md` (committed to repo)
- **Private alternative:** `.claude/CLONES.md` (local only, in .gitignore)
- **Configuration:** `.claude/session-coordinator-config.json`

## Related Documentation

- **Issue #24**: Enhancement proposal and requirements
- **Issue #1**: Core MCP Server implementation (Phase 1)
- **Architecture Overview**: `docs/architecture/overview.md`
- **Phase 1 Plan**: `docs/implementation/phase-1-plan.md`

## Support

For questions or issues:
- Review the examples in `DEV-SQUAD.md`
- Check Active Session State for current deployments
- Consult Coordination Protocols for procedures
- Ask in GitHub issues or discussions

---

**Version:** 1.1.0
**Last Updated:** 2025-10-31
**Maintained by:** Dev Squad
**Status:** Phase 1 Complete, Phase 2 Pending

*Specialized sessions, unified results.*
