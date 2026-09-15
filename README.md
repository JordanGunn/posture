# POSTURE

Bounded, persistent context for declaring the standing an AI agent has when ambiguity would otherwise make it defer, stay local, or preserve existing state.

> **H establishes and revokes the stance. D anchors and supplies the stance. A reasons under the stance.**

POSTURE does not specify the work. It specifies how much latitude the human delegates while the work is being interpreted and carried out.

A goal says **what state are we trying to reach?** A directive says **what are we doing now?** POSTURE says **what am I authorized to question, inspect, change, and preserve while doing it?**

## Why

Chat is intentionally volatile. Delegated standing usually should not be.

Agentic systems carry conservative defaults for good reasons: do not challenge the user unnecessarily; do not investigate outside requested scope unnecessarily; do not modify things that were not mentioned unnecessarily; do not remove established behavior unnecessarily.

POSTURE makes explicit when the human wants different burdens of proof.

## Bounded model

POSTURE v0.2 removes free-form posture prose. A posture is a validated profile over four bounded fields:

```text
E — epistemic authority
R — read reach
W — write reach
C — continuity prior
```

### E — Epistemic authority

```text
literal       Treat the human's framing as authoritative.
complete      Fill ordinary gaps without replacing the human's model.
challenge     Correct material mistakes or contradictions when evidence warrants.
reconstruct   Treat articulation as evidence of intent; reconstruct the problem when necessary.
```

### R — Read reach

```text
named         Named scope only.
adjacent      Immediate dependencies, dependents, and neighbors.
closure       Follow materially relevant dependency/coupling chains.
system        Inspect project/system-wide context where materially relevant.
```

### W — Write reach

```text
named         Named scope only.
coupled       Directly coupled artifacts when required for coherence.
closure       Relevant dependency closure when required for coherence.
systemic      System-wide until the relevant invariant is restored.
```

POSTURE enforces `W <= R`: the agent cannot be authorized to modify farther than it may inspect.

### C — Continuity prior

```text
preserve      Existing behavior/structure has a positive preservation prior.
neutral       Existing state receives no special preservation or replacement weight.
supersede     Existing state may be transitional; replacement may be preferred over fusion.
```

Continuity is a prior, not a conclusion. Evidence, hard constraints, and explicit current requirements still win.

See [`docs/SCHEMA.md`](docs/SCHEMA.md) for canonical semantics.

## Presets

Named postures are presets over the bounded axes, not free-form instructions.

```text
maintenance  E=complete   R=closure   W=coupled   C=preserve
migration    E=challenge  R=system    W=closure   C=supersede
```

Repository-specific presets may be committed under `.posture/presets/<name>.json`:

```json
{
  "schema_version": 1,
  "epistemic": "reconstruct",
  "read": "closure",
  "write": "coupled",
  "continuity": "neutral"
}
```

Unknown fields and invalid values are rejected. Arbitrary prose is not part of the posture schema.

## Installation lifecycle

Install the tool:

```bash
curl -fsSL https://raw.githubusercontent.com/JordanGunn/posture/master/install.sh | sh
```

The installer requires only Python 3.10+. It does not require pip, venv support, or sudo.

Bootstrap a repository:

```bash
posture bootstrap
```

This initializes `.posture/.gitignore` and `.posture/presets/` without configuring a provider.

Install provider integration:

```bash
posture install
posture install --provider claude
posture install --provider codex
```

Set a posture:

```bash
posture set migration
```

From then on the active profile is deterministically injected on every supported prompt until the human changes or clears it.

## Migrating from free-form POSTURE

v0.1 stored arbitrary Markdown posture bodies. v0.2 intentionally does not interpret that prose as structured authorization.

After updating the tool, run:

```bash
posture migrate
```

Migration is conservative:

- a legacy active built-in `migration` or `maintenance` posture is mapped deterministically to its new bounded preset;
- an already-current structured posture is validated and left unchanged;
- legacy custom Markdown files are detected and reported but **not inferred into axis values**;
- a legacy active custom/free-form posture is refused until the human explicitly clears it and chooses or authors a bounded preset.

POSTURE will not infer new delegated authority from old arbitrary prose.

Existing v0 provider skills are recognized by `posture install` and upgraded to the bounded skill definition. Foreign files remain protected.

## Control

```bash
posture list
posture set migration
posture show
posture render
posture migrate
posture clear
```

`show` exposes the active axes. `render` shows the canonical context block injected into the agent.

The active state is stored locally in `.posture/active.json` and is intentionally gitignored.

### Snapshot semantics

`set` snapshots the exact structured profile and its SHA-256 hash. If the source preset changes later, the active posture does **not** silently change. `show` reports preset drift; the human must run `set` again to adopt the new profile.

## Runtime contract

Every active profile is wrapped in a provider-independent contract:

- POSTURE changes the burden of proof; it does not predetermine conclusions;
- explicit current requirements, hard constraints, and direct evidence override posture defaults;
- a local override does not mutate persistent posture;
- POSTURE does not elevate external permissions;
- read/write reach are ceilings, not obligations to expand scope;
- unrelated cleanup is not authorized merely because broader action is permitted.

The bounded values are compiled into canonical agent-facing language by POSTURE itself. Preset files do not contain arbitrary instructions.

## Architecture

```text
Human
  │  set / clear / migrate
  ▼
validated bounded preset
  │
  ├── E epistemic authority
  ├── R read reach
  ├── W write reach
  └── C continuity prior
  │
  ▼
deterministic snapshot + hash
  │
  ▼
canonical renderer
  │
  ├───────────────┐
  ▼               ▼
Claude hook     Codex hook
  │               │
  └───────┬───────┘
          ▼
      inference
```

The provider does not define what `migration` means. The preset selects bounded values; the shared renderer owns their canonical semantics.

## HAD

> **H establishes and revokes the standing. D validates, anchors, migrates, and supplies it. A reasons within it.**

A may recommend a change of posture. It does not silently redefine or activate one.

See [`docs/HAD.md`](docs/HAD.md).

## Test

```bash
python3 -m unittest discover -s tests -v
```

The structured model enables both preset-level and axis-isolation experiments. Measure outcomes rather than whether the model repeats posture language: fusion vs replacement, unnecessary compatibility, scope expansion, preservation of real contracts, corrections to flawed framing, unrelated refactoring, clarification loops, downstream rework, and total token cost to an acceptable result.

## Non-goals

No automatic posture selection, automatic switching, dynamic composition, RAG, embeddings, vector stores, supervisory sub-agents, semantic classification, or arbitrary free-form posture instructions.

The mechanism should remain small enough that its effects can be measured.
