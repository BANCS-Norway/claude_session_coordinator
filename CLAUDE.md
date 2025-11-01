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

2. **Session Registry (Optional)** - For multi-session coordination
   - See `.claude/DEV-SQUAD.md` or `.claude/CLONES.md` for session coordination
   - Identify which session you are
   - Check active missions and deployments
   - Understand your specialization
   - Note: Session registries are personal customizations (not tracked in git)

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

## Session Registry Usage (Optional)

This project supports optional session coordination using specialized session registries. These are personal customizations (not tracked in git) that help coordinate parallel Claude Code sessions.

**How It Works:**

1. **Check if registry exists** - Look for `.claude/DEV-SQUAD.md` or `.claude/CLONES.md`
2. **Read registry** - Understand session assignments and current deployments
3. **Sign on** - Update your session status when starting work
4. **Coordinate** - Check for conflicting worktrees or parallel work
5. **Sign off** - Update status when completing work

**Registry Options:**

- **DEV-SQUAD.md** - Professional session registry with specialized agent roles
- **CLONES.md** - Alternative themed session registry (customizable)

Both registries serve the same purpose with different naming schemes. Choose the one that matches your preference, or create your own!

**Note:** Session registries are optional. If they don't exist in `.claude/`, you can work without them.

## Development Guidelines

1. **ALWAYS run pre-flight check first** (for concrete issues)
2. **ALWAYS confirm understanding first** (for ad-hoc tasks)
3. **ALWAYS read workflow.md before starting work**
4. **NEVER deviate from the workflow** without user approval
5. **Claude never pulls or pushes** - user handles that
6. **Claude can configure GitHub settings** - via `gh api` and `gh` CLI commands
7. **Only fix what's in the issue description** - scope is strictly limited to what's described; create new issues for discovered bugs or missing functionality

## Customization

This file contains standard project instructions. To add personal customizations:

1. Create `.claude/CLAUDE.md` (if it doesn't exist)
2. Add your personal preferences, session registry choice, and custom instructions
3. The `.claude/CLAUDE.md` file is gitignored and will not be committed
4. Your customizations will override these standard settings

See `.claude/CLAUDE.md` (if it exists) for personal customizations.

---

**Standard Instructions Version:** 1.0.0
**Last Updated:** 2025-11-01
**For customization, see:** `.claude/CLAUDE.md`
