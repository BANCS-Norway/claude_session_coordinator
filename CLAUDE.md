# Claude Instructions for claude_session_coordinator

> **Note:** This is the root CLAUDE.md template containing standard project instructions. Personal customizations should be added to `.claude/CLAUDE.md` which will override settings here.

## 🚨 CRITICAL: Read Before Starting

**Before starting ANY work, you MUST read:**

1. **`workflow.md`** - Development workflow (mandatory)
   - Pre-flight checks (mandatory before starting)
   - Git worktree workflow
   - Branch naming conventions
   - Commit message formats
   - PR creation process
   - Cleanup procedures

2. **Session Coordination** - MCP server for multi-session coordination
   - Use MCP tools for automated session coordination (see Session Coordination section)
   - `mcp__claude-session-coordinator__sign_on` - Claim session at start
   - `mcp__claude-session-coordinator__sign_off` - Release session when done
   - Fallback: Manual `.claude/CLONES.md` editing if MCP unavailable
   - Note: MCP server replaced manual session registries (Phase 3)

## Repository Overview

**Repository:** https://github.com/BANCS-Norway/claude_session_coordinator

This is a monorepo containing:
- **packages/mcp-server/** - Python MCP server implementation
- **packages/homepage/** - Documentation site
- **docs/** - Shared documentation

## Repository Configuration

This repository is configured to enforce a clean, linear Git history:

**Merge Settings (configured via GitHub API):**
- ✅ Rebase and merge only
- ❌ Merge commits disabled
- ❌ Squash merging disabled

**Branch Protection (main branch):**
- ✅ Required linear history
- ✅ Branches must be up-to-date before merging
- ✅ Force pushes disabled
- ✅ Direct commits blocked (all changes via PR)

**Note:** Claude can configure repository settings via `gh api` commands when needed.

## Monorepo-First Decision Making

**CRITICAL: This is a monorepo - decisions must consider the entire project, not just individual packages.**

When working on any issue:

1. **Think monorepo-wide first** - Consider impact across all packages
2. **Don't be language-siloed** - Don't make decisions solely based on what's common in Python, JavaScript, etc.
3. **Consistent patterns** - Prefer consistent approaches across packages over language-specific "best practices"
4. **Cross-package implications** - Always ask: "How does this affect other packages?"
5. **Shared tooling** - Prefer tools that work across the monorepo (e.g., git hooks, CI/CD, linting)

**Examples:**
- ❌ "This is a Python package, so let's use Python-specific tooling"
- ✅ "This is part of a monorepo, so let's use tooling that supports all packages"
- ❌ "JavaScript projects usually do X, so let's do that"
- ✅ "What's best for the monorepo as a whole? How does this align with other packages?"

## Quick Reference

**Branch naming format:**
```
{type}/{issuenumber}-{description}
```

Examples:
- `feat/15-add-redis-adapter`
- `fix/23-session-timeout`
- `docs/8-update-readme`
- `chore/13-rebase-merge-config`

**Common types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Task Confirmation Protocol

**For ad-hoc tasks (no concrete GitHub issue):**

When the user gives you a task that is not tied to a specific GitHub issue:

1. **Summarize your understanding** - Explain what you think they're asking for
2. **Ask for confirmation** - "Have I understood this correctly?"
3. **Wait for clarification** - Don't proceed until confirmed
4. **Decide on formality** - Should this become an issue, or proceed informally?

**Example:**
```
User: "Update the documentation to focus on monorepo-wide decisions"

Claude: "I understand you want me to add guidance to the internal documentation
         (.claude/ files) that emphasizes making decisions with the full monorepo
         scope in mind, rather than being siloed by individual package languages.

         Have I understood this correctly?"

User: "Yes, exactly"

Claude: "Great! This seems like a documentation update that doesn't need a formal
         issue. I'll update .claude/CLAUDE.md and .claude/workflow.md with this
         guidance. Proceeding..."
```

**For concrete issues:**
- Issue description defines scope → read issue → run pre-flight check → proceed

## Session Coordination

This project provides automated session coordination via the **claude_session_coordinator MCP server**, enabling multiple Claude Code sessions to work in parallel without conflicts.

### Primary Method: MCP Server (Automated)

The MCP server provides programmatic session coordination through the following tools:

**Sign On:**
```
mcp__claude-session-coordinator__sign_on
```
- Auto-detects machine (from hostname)
- Auto-detects project (from git remote)
- Claims session instance (e.g., `claude_1`)
- Returns session context for coordination

**Sign Off:**
```
mcp__claude-session-coordinator__sign_off
```
- Releases session instance for others
- Preserves session state for future reference

**Workflow Integration:**

1. **Pre-flight check** → Verify workspace is clean
2. **Sign on via MCP** → Claim session and coordinate
3. **Work on issue** → Create worktree, make changes, commit
4. **PR merged** → Sign off via MCP, clean up worktree

The MCP server automatically:
- Detects your machine and project
- Manages session assignments
- Stores coordination state
- Prevents worktree conflicts

**Why MCP Coordination?**

The project evolved from manual session registries (Phase 1-2) to automated MCP coordination (Phase 3):
- **Phase 1-2:** Manual CLONES.md/DEV-SQUAD.md files edited by hand
- **Phase 3:** MCP server provides programmatic coordination API
- **Result:** Faster, more reliable session coordination with less manual work

### Fallback Method: Session Registries (Manual)

If the MCP server is unavailable, you can fall back to manual session coordination using `.claude/CLONES.md` or `.claude/DEV-SQUAD.md` files.

**Legacy Registry Workflow:**

1. **Check registry** - Read `.claude/CLONES.md` for session assignments
2. **Update status** - Manually edit to mark session as "deployed"
3. **Coordinate** - Check for conflicting worktrees before starting
4. **Sign off** - Edit file again to mark session as "standby"

**Note:** Manual registries are personal customizations (not tracked in git). They were the original solution before MCP automation and remain as a fallback option.

## Development Guidelines

1. **ALWAYS run pre-flight check first** (for concrete issues)
2. **ALWAYS sign on via MCP after pre-flight check** - claim session and coordinate with other instances
3. **ALWAYS confirm understanding first** (for ad-hoc tasks)
4. **ALWAYS read workflow.md before starting work**
5. **NEVER deviate from the workflow** without user approval
6. **Claude never pulls or pushes** - user handles that
7. **Claude can configure GitHub settings** - via `gh api` and `gh` CLI commands
8. **Only fix what's in the issue description** - scope is strictly limited to what's described; create new issues for discovered bugs or missing functionality
9. **ALWAYS sign off via MCP after PR is merged** - release session for others to use

## Customization

This file contains standard project instructions. To add personal customizations:

1. Create `.claude/CLAUDE.md` (if it doesn't exist)
2. Add your personal preferences, session registry choice, and custom instructions
3. The `.claude/CLAUDE.md` file is gitignored and will not be committed
4. Your customizations will override these standard settings

See `.claude/CLAUDE.md` (if it exists) for personal customizations.

---

**Standard Instructions Version:** 1.1.0
**Last Updated:** 2025-11-01
**Changelog:** Added MCP session coordination as primary method (replaced manual session registries)
**For customization, see:** `.claude/CLAUDE.md`
