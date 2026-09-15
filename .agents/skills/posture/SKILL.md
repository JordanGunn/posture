---
name: posture
description: Set, clear, inspect, list, or migrate the repository's bounded POSTURE. Use only when the user explicitly wants to change or inspect the agent's delegated standing.
---

Manage repository POSTURE state using the provider-agnostic CLI.

Interpret the user's requested posture operation as one of:

- `set <name>`
- `clear`
- `show`
- `list`
- `migrate`

Run the corresponding command:

```bash
posture <operation>
```

POSTURE is a bounded schema over epistemic authority, read reach, write reach, and continuity prior.
Do not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.
