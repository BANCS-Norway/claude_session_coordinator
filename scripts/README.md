# Repository Scripts

This directory contains utility scripts for the claude_session_coordinator repository.

## fix-lefthook-worktree.sh

Patches lefthook git hooks to work correctly with git worktrees.

### Problem

Lefthook's auto-generated hooks use `git rev-parse --show-toplevel` to find the repository root, which returns the worktree directory when running from a git worktree instead of the main repository root. This causes hooks to fail with "Can't find lefthook in PATH" errors.

### Solution

This script patches the hooks to use:
```bash
git_common_dir="$(git rev-parse --git-common-dir)"
dir="$(cd "$git_common_dir/.." && pwd)"
```

This approach correctly finds the repository root whether running from the main worktree or a git worktree.

### Usage

The script is automatically run as part of `npm install` via the postinstall hook in package.json.

Manual execution:
```bash
bash scripts/fix-lefthook-worktree.sh
```

### When to Run

- Automatically after `npm install` (via postinstall hook)
- After manually running `lefthook install`
- If you encounter "Can't find lefthook in PATH" errors from git worktrees

### Related

- Issue #47: Lefthook hooks fail to find executable when running from git worktrees
- Issue #37: Setup Automatic Linting Enforcement (introduced lefthook)
