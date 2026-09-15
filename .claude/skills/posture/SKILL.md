---
name: posture
description: Set, clear, inspect, or list the repository's persistent POSTURE. Invoke explicitly when the user wants to change or inspect the agent's operating stance.
disable-model-invocation: true
---

Manage repository POSTURE state using the provider-agnostic CLI.

Interpret `$ARGUMENTS` as one of:

- `set <name>`
- `clear`
- `show`
- `list`

Run:

```bash
python3 -m posture $ARGUMENTS
```

Do not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.
