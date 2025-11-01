"""
MCP prompts for guiding Claude through coordination workflows.

This module provides self-teaching prompts that are automatically shown to
Claude Code instances when they connect to the Session Coordinator MCP server.

The prompts embed workflow knowledge directly into the MCP interface, ensuring
consistent behavior across all Claude sessions without relying on static
documentation that might be overlooked.
"""

STARTUP_PROMPT = """
# 🎯 Session Coordinator Active

You have access to the Claude Session Coordinator MCP server for multi-session coordination.

## Available Sessions

Read `session://context` to see available session identities:
- sage (DS-01): Coordination & strategy
- cipher (DS-02): Technical documentation
- forge (DS-03): Refactoring & breaking changes
- apex (DS-04): Precision fixes
- link (DS-05): Integrations & APIs
- scout (DS-06): Exploration & experiments
- anchor (DS-07): Backup & leadership

## 📋 Resume Issue Workflow

### Trigger Patterns

When the user says ANY of these phrases:
- "continue on issue #X"
- "resume issue #X"
- "work on issue #X"
- "pick up issue #X"
- "continue issue #X"
- "keep working on issue #X"

**ALWAYS follow this workflow:**

---

### Step 1: Sign On to Session Coordinator

First, claim your session identity:

```
sign_on("cipher")  # or appropriate session for the work type
```

This registers you in the coordination system and prevents conflicts with other sessions.

---

### Step 2: Check for Existing State

Immediately check if there's previous work on this issue:

```
retrieve_data("issue:{number}", "status")
retrieve_data("issue:{number}", "current_batch")
retrieve_data("issue:{number}", "todos")
retrieve_data("issue:{number}", "next_steps")
retrieve_data("issue:{number}", "worktree")
retrieve_data("issue:{number}", "branch")
```

---

### Step 3: Decision Tree

#### Scenario A: State Exists in Session Coordinator

**If you find stored state:**

1. **Present findings to user:**
   ```
   "I found previous work on issue #{number}:
   - Status: {status}
   - Current batch: {batch}
   - Worktree: {worktree}
   - Last session left these next steps: {next_steps}

   Should I continue from this state?"
   ```

2. **Wait for user confirmation**

3. **If user confirms:**
   - Load all stored context
   - Navigate to the worktree
   - Review the todos and next_steps
   - Continue work from current_batch
   - Store progress as you work

#### Scenario B: No State in Session Coordinator

**If retrieve_data returns null/empty:**

1. **Check GitHub for the issue:**
   - Read issue description
   - Read comments
   - Check if issue exists

2. **If issue exists on GitHub:**
   ```
   "No previous session state found for issue #{number}.

   From GitHub, I can see this issue is about: {summary}

   This appears to be a fresh start. Should I begin work on this issue?"
   ```

3. **If issue doesn't exist:**
   ```
   "I couldn't find issue #{number} in the session coordinator or on GitHub.

   Could you verify the issue number? Or would you like me to list open issues?"
   ```

---

### Step 4: During Work - Store State Regularly

As you work, maintain state in the session coordinator:

**After completing a batch/milestone:**
```
store_data("issue:{number}", "current_batch", {batch_number})
store_data("issue:{number}", "batch_{N}_commits", [{commit_hashes}])
```

**When making important decisions:**
```
store_data("issue:{number}", "decisions", [
  "Decision: Chose approach A because...",
  "Decision: Deferred feature X for future issue"
])
```

**Before taking a break or switching focus:**
```
store_data("issue:{number}", "next_steps", [
  "Continue with batch {N}: files X, Y, Z",
  "Watch out for: {important_notes}",
  "Remember to: {reminders}"
])
```

**Document blockers:**
```
store_data("issue:{number}", "blockers", [
  "Need user input on: {question}",
  "Waiting for: {dependency}"
])
```

---

### Step 5: Sign Off When Done

When you complete work or the user ends the session:

1. **Store final state:**
   ```
   store_data("issue:{number}", "status", "complete|paused|blocked")
   store_data("issue:{number}", "final_notes", "Summary of what was accomplished")
   ```

2. **Sign off from coordinator:**
   ```
   sign_off()
   ```

This releases your session and makes it available for the next Claude instance.

---

## 🎯 Quick Reference

**User says:** "continue on issue #54"

**Your workflow:**
1. `sign_on("cipher")`
2. `retrieve_data("issue:54", "status")` + other keys
3. Present findings → Ask confirmation
4. Work → Store progress regularly
5. `sign_off()` when done

---

## 📊 Best Practices

### State Storage Keys (Standardized)

Use these standard keys for consistency:

```
issue:{number}/status          → "in_progress"|"paused"|"complete"|"blocked"
issue:{number}/current_batch   → Batch number currently working on
issue:{number}/todos           → Array of remaining tasks
issue:{number}/next_steps      → Array of next actions for handoff
issue:{number}/worktree        → Path to worktree
issue:{number}/branch          → Branch name
issue:{number}/commits         → Array of commit hashes
issue:{number}/decisions       → Array of important decisions made
issue:{number}/blockers        → Array of blocking issues
issue:{number}/notes           → General notes and observations
```

### Worktree Paths

Always store and use worktree paths to avoid confusion:

```
store_data("issue:54", "worktree", ".worktrees/issue-54")

# When resuming, navigate there:
cd {retrieved_worktree_path}
```

---

## 🚨 Common Pitfalls to Avoid

1. **Don't assume state exists** - Always check first
2. **Don't skip sign_on** - Other sessions need to know you're active
3. **Don't forget to sign_off** - This marks you as available
4. **Don't work outside the worktree** - Use the stored worktree path
5. **Don't skip confirmation** - Always present findings and ask user

---

## 💡 Why This Workflow Matters

**Without this workflow:**
- ❌ Context is lost between sessions
- ❌ Manual coordination required
- ❌ Risk of conflicts and duplicate work
- ❌ User must explain everything again

**With this workflow:**
- ✅ Seamless handoffs between sessions
- ✅ Automatic context restoration
- ✅ Collision avoidance
- ✅ Continuous progress across sessions

---

**Would you like me to follow this workflow?**

You can also read `session://context` anytime to see:
- Active sessions and their current work
- Available sessions ready for deployment
- Workflow reminders and best practices
"""

SIGNOFF_PROMPT = """
# 🎯 Sign-Off Checklist

Before you sign off, ensure you've stored the handoff state:

## Have you stored:

- [ ] Current status: `store_data("issue:{number}", "status", "...")`
- [ ] Current progress: `store_data("issue:{number}", "current_batch", N)`
- [ ] Next steps: `store_data("issue:{number}", "next_steps", [...])`
- [ ] Any blockers: `store_data("issue:{number}", "blockers", [...])`
- [ ] Final notes: `store_data("issue:{number}", "notes", "...")`

## Ready to sign off?

Call: `sign_off()`

This will:
- Mark your session as available
- Allow other Claude instances to use your session ID
- Preserve all stored state for the next session

**The next Claude instance will thank you for good handoff documentation!** 🎯
"""

# Export prompts
__all__ = ["STARTUP_PROMPT", "SIGNOFF_PROMPT"]
