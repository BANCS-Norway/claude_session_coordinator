#!/bin/bash
# Fix Lefthook hooks to work with git worktrees
#
# This script patches the auto-generated lefthook hooks to correctly find
# the repository root when running from git worktrees.
#
# Issue: https://github.com/BANCS-Norway/claude_session_coordinator/issues/47

set -e

# Find the repository root (works from both main worktree and git worktrees)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
GIT_COMMON_DIR="$(git rev-parse --git-common-dir)"
REPO_ROOT="$(cd "$GIT_COMMON_DIR/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Fixing lefthook hooks for git worktree compatibility..."

# Fix pre-commit hook
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    echo "  Patching pre-commit hook..."

    # Replace the problematic line:
    #   dir="$(git rev-parse --show-toplevel)"
    # With:
    #   git_common_dir="$(git rev-parse --git-common-dir)"
    #   dir="$(cd "$git_common_dir/.." && pwd)"

    sed -i.bak '
        /dir="\$(git rev-parse --show-toplevel)"/c\
    git_common_dir="$(git rev-parse --git-common-dir)"\
    dir="$(cd "$git_common_dir/.." && pwd)"
    ' "$HOOKS_DIR/pre-commit"

    echo "  ✓ pre-commit hook patched"
    rm -f "$HOOKS_DIR/pre-commit.bak"
else
    echo "  ⚠ pre-commit hook not found. Run 'lefthook install' first."
    exit 1
fi

# Fix other hooks if they exist and have the same issue
for hook in pre-push commit-msg prepare-commit-msg post-commit; do
    if [ -f "$HOOKS_DIR/$hook" ] && grep -q 'dir="\$(git rev-parse --show-toplevel)"' "$HOOKS_DIR/$hook"; then
        echo "  Patching $hook hook..."
        sed -i.bak '
            /dir="\$(git rev-parse --show-toplevel)"/c\
    git_common_dir="$(git rev-parse --git-common-dir)"\
    dir="$(cd "$git_common_dir/.." && pwd)"
        ' "$HOOKS_DIR/$hook"
        echo "  ✓ $hook hook patched"
        rm -f "$HOOKS_DIR/$hook.bak"
    fi
done

echo ""
echo "✅ Lefthook hooks are now compatible with git worktrees!"
echo ""
echo "The hooks will now correctly locate the repository root whether running"
echo "from the main worktree or from a git worktree."
