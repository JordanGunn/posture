# POSTURE

Persistent, anchored context for holding an AI agent's decision posture in place across volatile prompts and long-running work.

> **H establishes and revokes the stance. D anchors and supplies the stance. A reasons under the stance.**

POSTURE is persistent context that controls **how an agent should regard and resolve what it encounters while doing the work**, without specifying the work itself.

A goal says *what state are we trying to reach?* A directive says *what are we doing now?* POSTURE says *how should I regard what I encounter while doing it?*

## Why

Chat is intentionally volatile. Architectural stance usually should not be.

Long-running agentic work often fails when an old or transitional implementation is treated as authoritative simply because the current prompt did not explicitly revoke it. The agent conservatively merges the requested correction into the stale architecture, producing fusion instead of remediation.

POSTURE gives slow-moving decision context somewhere slow to live.

It is deliberately not RAG, memory, a planning system, a sub-agent, or another project instruction file. v0 is a small deterministic mechanism that repeatedly supplies a small human-selected reasoning prior.

## Installation lifecycle

POSTURE separates installing the tool from preparing and integrating a repository.

### 1. Install the tool

The tool installer creates an isolated virtual environment under `~/.local/share/posture` and exposes the CLI at `~/.local/bin/posture`.

```bash
curl -fsSL https://raw.githubusercontent.com/JordanGunn/posture/master/install.sh | sh
```

For inspection before execution:

```bash
curl -fsSLO https://raw.githubusercontent.com/JordanGunn/posture/master/install.sh
sh install.sh
```

The installer requires Python 3.10+ and Python's `venv` support. It does not modify a repository.

For development from a local clone:

```bash
python3 -m pip install -e .
```

### 2. Bootstrap a repository

From inside a Git repository:

```bash
posture bootstrap
```

This initializes only POSTURE's repository-local state:

```text
.posture/
├── .gitignore       # keeps active.json local
└── postures/        # optional repository-specific definitions
```

It does not configure Claude, Codex, or any other provider.

### 3. Install provider integration

After bootstrapping:

```bash
posture install
```

By default this wires both Claude Code and Codex. To install only one provider:

```bash
posture install --provider claude
posture install --provider codex
```

The installer merges POSTURE hooks into existing JSON configuration while preserving unrelated keys. It is idempotent and refuses to overwrite a conflicting existing POSTURE skill file.

### 4. Set a posture

```bash
posture set migration
```

From then on the active posture is deterministically injected on every supported prompt until the human explicitly changes or clears it.

## v0

Two deliberately opposed postures are bundled:

- `migration`: existing architecture may be transitional; compatibility is not presumed; prefer coherent replacement over fusion.
- `maintenance`: established behavior is presumptively intentional; prefer localized compatible changes.

Only zero or one posture can be active.

### Control

```bash
posture list
posture set migration
posture show
posture clear
```

The active state is stored locally in `.posture/active.json` and is intentionally gitignored.

### Definition snapshots

`set` snapshots the exact posture text and its SHA-256 hash into active state. If a posture definition changes later, the active posture **does not silently change**. `show` reports definition drift; the human must run `set` again to adopt the new definition.

Repository-specific definitions may be committed at:

```text
.posture/postures/<name>.md
```

They override bundled definitions of the same name.

## Agent integration

The core is provider-agnostic. `posture hook` renders one canonical context block. Provider configuration only decides how that block reaches the model.

### Claude Code

`.claude/settings.json` registers a `UserPromptSubmit` hook. Claude Code injects the returned `additionalContext` alongside every submitted prompt.

A project skill is installed at `.claude/skills/posture/SKILL.md` for explicit posture control.

### Codex

`.codex/hooks.json` registers the same `UserPromptSubmit` hook. Codex injects the returned `additionalContext` as developer context.

A repo skill is installed at `.agents/skills/posture/SKILL.md`. Its OpenAI metadata disables implicit invocation so posture mutation stays explicit.

Project-local hooks are subject to each provider's workspace/trust controls.

## Runtime contract

Every active posture is wrapped in a provider-independent contract:

- posture is a default over judgment, not a fact or predetermined conclusion;
- explicit current requirements and direct evidence override posture defaults for the current decision;
- local overrides do not mutate persistent posture;
- posture does not elevate permissions;
- posture does not justify unrelated cleanup.

This is designed to change the **burden of proof**, not predetermine the answer.

## Architecture

```text
Human
  │  set / clear
  ▼
deterministic repo state
  │
  ├── canonical snapshot + hash
  │
  ▼
shared renderer
  │
  ├───────────────┐
  ▼               ▼
Claude hook     Codex hook
  │               │
  └───────┬───────┘
          ▼
      inference
```

The providers do not have separate meanings for `migration`. They receive the same rendered snapshot.

## Test

```bash
python3 -m unittest discover -s tests -v
```

The initial experiment is intentionally simple:

```text
same repository
same task
same model
same tools

A: no posture
B: migration posture
C: maintenance posture
```

Measure whether the posture changes ambiguous decisions appropriately: fusion vs. replacement, unnecessary compatibility, scope expansion, preservation of real contracts, unrelated refactoring, clarification loops, downstream rework, and total token cost to an acceptable result.

## Non-goals for v0

No automatic posture selection, automatic switching, dynamic composition, RAG, embeddings, vector stores, sub-agents, semantic classification, or large predefined taxonomy.

The mechanism should stay boring until evidence says it needs to become more complicated.

See [`docs/HAD.md`](docs/HAD.md) for the design boundaries.
