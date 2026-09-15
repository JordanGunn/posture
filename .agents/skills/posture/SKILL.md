---
name: posture
description: Set, clear, inspect, or list the repository's persistent POSTURE. Use only when the user explicitly wants to change or inspect the agent's operating stance.
---

Manage repository POSTURE state using the provider-agnostic CLI.

Interpret the user's requested posture operation as one of:

- `set <name>`
- `clear`
- `show`
- `list`

Run the corresponding command:

```bash
python3 -m posture <operation>
```

Do not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.
