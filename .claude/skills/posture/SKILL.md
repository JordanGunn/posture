---
name: posture
description: Set, clear, inspect, list, or migrate the repository's bounded POSTURE. Invoke explicitly when the user wants to change or inspect the agent's delegated standing.
disable-model-invocation: true
---

Manage repository POSTURE state using the provider-agnostic CLI.

Interpret `$ARGUMENTS` as one of:

- `set <name>`
- `clear`
- `show`
- `list`
- `migrate`

Run:

```bash
posture $ARGUMENTS
```

POSTURE is a bounded schema over epistemic authority, read reach, write reach, and continuity prior.
Do not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.
