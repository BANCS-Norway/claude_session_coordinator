# Contributing to Claude Session Coordinator

Thank you for your interest in contributing to Claude Session Coordinator! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Git Workflow](#git-workflow)
- [Making Changes](#making-changes)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Development Tools](#development-tools)
- [Issue Guidelines](#issue-guidelines)
- [Code of Conduct](#code-of-conduct)
- [Questions and Support](#questions-and-support)

## Getting Started

### Prerequisites

- **Python:** 3.9 or higher
- **Git:** Latest stable version
- **pip:** Python package installer
- **GitHub CLI (gh):** Optional but recommended for issue and PR management

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude_session_coordinator.git
   cd claude_session_coordinator
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/BANCS-Norway/claude_session_coordinator.git
   ```

### Development Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   cd packages/mcp-server
   pip install -e .
   pip install -e ".[dev]"  # Install development dependencies
   ```

## Git Workflow

This project uses a **rebase-only workflow** to maintain a clean, linear Git history.

### Branch Protection Rules

The repository is configured to enforce a clean, linear Git history:

- **Direct commits to `main` are blocked** - All changes must go through pull requests
- **Only rebase and merge allowed** - Merge commits and squash merging are disabled
- **Branches must be up to date with main before merging** - GitHub will require you to rebase on the latest main before allowing merge
- **Linear history enforced** - The commit history must be linear (no merge commits)
- **Force pushes disabled on main** - Main branch is protected from force pushes

These settings ensure every commit in main is a meaningful, atomic change that can be easily reviewed, reverted, or bisected.

### Branch Naming Conventions

Create descriptive branch names using this format:

```
<type>/<issue-number>-<short-description>
```

**Types:**
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `style/` - Code style changes (formatting, etc.)
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

**Examples:**
- `feat/42-redis-adapter`
- `fix/89-session-timeout`
- `docs/14-contributing`
- `chore/55-update-deps`

### Creating a Feature Branch

```bash
git checkout main
git pull upstream main
git checkout -b feat/123-your-feature
```

### Keeping Your PR Up-to-Date with Main

Before submitting or when requested during review, rebase your branch on the latest main:

```bash
git checkout your-feature-branch
git fetch upstream
git rebase upstream/main
```

If there are conflicts, resolve them and continue:

```bash
# After resolving conflicts in your editor
git add <resolved-files>
git rebase --continue
```

Push your rebased branch:

```bash
git push --force-with-lease origin your-feature-branch
```

**Important:** Use `--force-with-lease` instead of `--force` to avoid accidentally overwriting work.

### Why Rebase-Only Workflow?

This repository enforces a rebase-only workflow for several important reasons:

**Clean History:**
- Linear commit history without merge bubbles
- Easy to read `git log` output
- Simple to understand project evolution
- Straightforward to bisect when debugging

**Integration Safety:**
- PRs must be rebased on latest main before merge
- Ensures all changes are tested against current codebase
- Prevents "works on my branch" integration issues
- Reduces merge conflicts and integration bugs

**Best Practices:**
- Follows modern Git workflow patterns
- Makes reverting changes simpler
- Each commit in main represents a complete, tested change
- Reduces repository clutter

### What Happens When Your PR is Not Up-to-Date?

When main has new commits after you created your branch, GitHub will prevent merging your PR with a message like:

> "This branch is out-of-date with the base branch"

**To resolve this:**

1. Fetch the latest changes from upstream:
   ```bash
   git fetch upstream
   ```

2. Rebase your branch on the latest main:
   ```bash
   git checkout your-feature-branch
   git rebase upstream/main
   ```

3. Resolve any conflicts if they occur:
   ```bash
   # Edit conflicted files in your editor
   git add <resolved-files>
   git rebase --continue
   ```

4. Force push your rebased branch:
   ```bash
   git push --force-with-lease origin your-feature-branch
   ```

5. GitHub will now allow your PR to be merged

**Note:** After rebasing, your commit SHAs will change (this is normal and expected). The `--force-with-lease` flag ensures you don't accidentally overwrite any work that may have been pushed to your branch by someone else.

## Making Changes

### Code Style Guidelines

- Follow **PEP 8** style guide for Python code
- Use **type hints** for all function signatures
- Maximum line length: 88 characters (Black default)
- Use descriptive variable and function names
- Add docstrings for modules, classes, and functions

**Example:**

```python
def sign_on(instance_id: str, context: dict[str, Any]) -> SessionState:
    """
    Register a new session instance.

    Args:
        instance_id: Unique identifier for the session instance
        context: Session context information

    Returns:
        SessionState object containing the new session state

    Raises:
        ValueError: If instance_id is already in use
    """
    # Implementation
```

### Testing Requirements

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for high code coverage (>80%)
- Use pytest for testing
- Place tests in `tests/` directory

### Documentation Requirements

- Update README.md if adding new features
- Add/update docstrings for new/modified code
- Update relevant documentation in `docs/` directory
- Include examples for new features

### Commit Message Conventions

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Scope:** Package name or feature area (e.g., `mcp-server`, `storage`, `homepage`)

**Examples:**

```
feat(mcp-server): add session sign-on tool

Implements the sign_on() MCP tool that allows Claude sessions
to register and claim instance identifiers.
```

```
fix(storage): handle null values in local adapter

The local file adapter now properly handles null values when
retrieving data, preventing KeyError exceptions.
```

```
docs(readme): update installation instructions

Added clarification for Python version requirements and
virtual environment setup.
```

## Submitting Pull Requests

### Before Submitting

1. Ensure all tests pass
2. Update documentation
3. Rebase on latest main
4. Verify commit messages follow conventions
5. Check that your branch is up-to-date with main

### PR Title Format

Use the same format as commit messages:

```
<type>(<scope>): <description>
```

### PR Description

Include the following in your PR description:

```markdown
## Summary
Brief overview of the changes

## Changes
- Detailed list of changes made
- Explanation of approach taken
- Any notable implementation details

## Test Plan
- [ ] How to test these changes
- [ ] What scenarios were tested

## Related Issues
Closes #123
```

### PR Requirements

- **Must be up-to-date with main** - Rebase if necessary
- All commits must follow conventional commit format
- All CI/CD checks must pass (when implemented)
- At least one approval required
- No merge conflicts

### Review Process

1. Submit PR with proper title and description
2. Automated checks will run (CI/CD)
3. Maintainers will review your code
4. Address any requested changes
5. Once approved, a maintainer will merge using "Rebase and merge"

## Development Tools

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_session_coordinator

# Run specific test file
pytest tests/test_storage.py

# Run tests matching a pattern
pytest -k "test_sign_on"
```

### Type Checking

```bash
# Run mypy type checker
mypy packages/mcp-server/claude_session_coordinator
```

### Linting

```bash
# Run flake8
flake8 packages/mcp-server/claude_session_coordinator

# Run pylint
pylint packages/mcp-server/claude_session_coordinator
```

### Code Formatting

```bash
# Format code with Black
black packages/mcp-server/claude_session_coordinator

# Check formatting without making changes
black --check packages/mcp-server/claude_session_coordinator

# Sort imports with isort
isort packages/mcp-server/claude_session_coordinator
```

### Development Workflow Summary

```bash
# Before committing
black .
isort .
flake8 .
mypy .
pytest

# Commit your changes
git add <files>
git commit -m "feat(scope): description"
```

## Issue Guidelines

### Reporting Bugs

When reporting bugs, please include:

- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Error messages or logs
- Minimal reproduction example if possible

Use the bug report template when creating issues.

### Requesting Features

When requesting features, please include:

- Clear description of the feature
- Use case and motivation
- Possible implementation approach
- Any related issues or discussions

Use the feature request template when creating issues.

### Using Issue Templates

This repository provides issue templates for:
- Bug reports
- Feature requests
- Documentation improvements

Please use the appropriate template when creating issues.

### Labeling Conventions

Issues are organized using labels:

**Priority:**
- `priority: high` - Immediate attention
- `priority: medium` - Important, address soon
- `priority: low` - Nice to have

**Type:**
- `type: bug` - Something isn't working
- `type: feature` - New feature request
- `type: enhancement` - Enhancement to existing feature
- `type: documentation` - Documentation improvements

**Component:**
- `component: mcp-server` - MCP server implementation
- `component: storage` - Storage adapter functionality
- `component: homepage` - Homepage/documentation site
- `component: docs` - Documentation

**Status:**
- `status: in-progress` - Currently being worked on
- `status: blocked` - Cannot proceed due to dependencies
- `status: needs-review` - Needs review/feedback

**Community:**
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Questions and Support

- **Issues:** For bug reports and feature requests
- **Discussions:** For questions, ideas, and general discussion (coming soon)
- **Email:** For private inquiries, contact the maintainers

### Getting Help

If you're stuck or have questions:

1. Check existing documentation in `docs/`
2. Search existing issues and discussions
3. Ask in GitHub Discussions (when available)
4. Create a new issue with the `question` label

## Thank You!

Your contributions make this project better. Whether it's:

- Reporting a bug
- Discussing the current state of code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

We appreciate your help and involvement in the Claude Session Coordinator community!

---

**Note:** This project is not affiliated with Anthropic PBC. See [README.md](README.md) for disclaimers.
