# POSTURE through HAD

POSTURE is intentionally small:

> **H establishes and revokes the stance. D anchors and supplies the stance. A reasons under the stance.**

| Concern | H — Human | A — Inference | D — Determinism |
|---|---|---|---|
| Define posture | Determines and approves the stance | May help draft it | Stores canonical definitions |
| Select / clear | Explicitly establishes or revokes | May recommend, never self-activate | Performs the state transition |
| Persistence | — | Does not remember | Stores repo-scoped state |
| Injection | — | Receives posture as context | Reinjects the exact snapshot each prompt |
| Interpretation | Sets the prior | Resolves concrete ambiguity | Does not interpret prose |
| Evidence conflict | — | Evidence wins | — |
| Local explicit override | Supplies the requirement | Applies it to that decision | Leaves persistent posture unchanged |
| Permissions | Grants separately | Cannot infer new authority | Existing security/tool gates remain authoritative |

## Invariants

1. Posture influences judgment; it does not manufacture facts.
2. Posture supplies defaults; explicit current requirements can override them locally.
3. Evidence can defeat the posture prior.
4. A local override does not mutate persistent posture.
5. POSTURE never bypasses external permissions or safety boundaries.
6. Only trusted human-authorized control establishes, replaces, or clears persistent posture.
7. The canonical posture is deterministically reinjected; the agent never has to remember it.
8. v0 supports zero or one active posture.
9. Posture remains small: it describes a stance, not the project, goal, architecture, or personality.
10. The agent may recommend a posture transition but cannot self-modify it.

## v0

The first experiment deliberately provides two opposed priors:

- **migration** — compatibility is not presumed; prefer coherent replacement over fusion.
- **maintenance** — existing behavior is presumptively intentional; prefer localized compatible changes.

The useful experiment is to hold repository, task, model, and tools constant while varying only the active posture.
