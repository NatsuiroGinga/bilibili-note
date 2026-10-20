---
name: daily-coding
description: Use for everyday coding tasks that involve writing or modifying source code.
version: 1.0.0
tags: [Coding, Daily, Checklist]
---

# Daily Coding Checklist

A minimal coding quality assurance checklist ensuring every code modification follows best practices.

## When to Use

Use this skill for:
- Implementing new features
- Adding code or modifying existing code
- User requests like "write a...", "implement...", "add...", or "modify..."
- Any coding task that involves Edit or Write tools

## When Not to Use

Do not use this skill for:
- Pure reading or understanding tasks with no modification intent
- Work already covered by specialized skills such as `bug-detective`, `architecture-design`, or `verification-loop`
- Configuration-only changes
- Documentation-only writing

## Core Checklist

### Third-Party API Verification (MANDATORY)

**Before writing any call to a third-party library API you have not verified in this session,
invoke the `find-docs` skill.** Training data is frequently outdated on API signatures,
parameter names, and object attributes.

Trigger on all of these:
- First use of a library in this session, or any uncertainty about a signature
- Attribute access on an object returned by a library (`run.public`, `client.foo`)
- Keyword arguments (`experiment_name=` vs `name=`)
- Anything the docs call "recent", "new in vX", or that you last saw in a different major version

`py_compile` / syntax check **does not** prove a runtime attribute exists. Neither does
"I have seen this API before."

Record in the implementation report: library, version actually installed on the target machine,
the source consulted, and the verified signature.

**Evidence this is needed** (two real incidents, same failure mode, same repo):
- `torch.flatnonzero` — does not exist; written from memory, passed syntax check, failed at runtime.
  Correct form is `torch.nonzero(condition, as_tuple=True)[0]`.
- `swanlab` 0.9.0 — code used `run.public.cloud.project_name`; `Run` exposes only
  `id / name / path / url / dir / config / log*`. There is no `public` attribute.
  Crashed on the first run after being pushed to the server unreviewed.
- Same incident, opposite direction: the agent then claimed `experiment_name=` was invalid.
  It is valid — a backward-compatible alias mapped onto `experiment.name`.
  **Asserting an API does NOT exist is as unreliable as asserting it does.** Verify both directions.

### Before Starting

- [ ] **Read before modify** - Must read target file with Read tool before making changes
- [ ] **Understand context** - Confirm understanding of existing code logic and design intent

### During Coding

- [ ] **Minimal changes** - Only change what's necessary, no over-engineering, no unrelated features
- [ ] **Type safety** - Add type hints for Python, avoid `any` in TypeScript
- [ ] **Security check** - Avoid command injection, XSS, SQL injection vulnerabilities

### After Completion

- [ ] **Verify execution** - Ensure code runs correctly with no syntax errors
- [ ] **Clean up** - Remove print/console.log debug statements and temporary files
- [ ] **Brief summary** - Inform user what was changed and the scope of impact

## Quick Reference

### Common Mistakes to Avoid

```python
# ❌ Don't
def process(data=[]):  # Mutable default argument
    pass

# ✅ Should
def process(data: list | None = None):
    data = data or []
```

```python
# ❌ Don't
except:  # Bare except
    pass

# ✅ Should
except ValueError as e:
    logger.error(f"Processing failed: {e}")
    raise
```

### Security Check Points

- User input must be validated/escaped
- Use pathlib for file paths, avoid path traversal
- Never hardcode sensitive info (API keys, passwords)
