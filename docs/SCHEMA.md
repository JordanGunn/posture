# POSTURE Schema

POSTURE is a bounded declaration of delegated agent standing.

It answers four questions:

```text
E — Can I question the human's framing?
R — How far may I look?
W — How far may I change?
C — How strongly should existing state be preserved?
```

A posture is not an arbitrary instruction block. A preset selects exactly one value on each axis.

## Canonical profile schema

```json
{
  "schema_version": 1,
  "epistemic": "challenge",
  "read": "system",
  "write": "closure",
  "continuity": "supersede"
}
```

No additional fields are accepted.

## Epistemic authority

Ordered from least to greatest authority to reinterpret the human's framing:

| Value | Standing |
|---|---|
| `literal` | Treat framing and terminology as authoritative. |
| `complete` | Fill routine omissions without replacing the human's conceptual model. |
| `challenge` | Correct material mistakes, contradictions, or terminology when evidence warrants. |
| `reconstruct` | Treat articulation as evidence of intent; reconstruct a coherent problem when necessary. |

This axis applies to claims and framing, not explicit hard requirements. A user requirement remains a requirement unless changed by the human or contradicted by a higher-order constraint.

## Read reach

| Value | Standing |
|---|---|
| `named` | Named scope and minimum required context. |
| `adjacent` | Immediate dependencies, dependents, and neighbors. |
| `closure` | Relevant dependency/coupling closure. |
| `system` | Project/system-wide where materially relevant. |

Read reach is permission to perceive, not an obligation to explore everything.

## Write reach

| Value | Standing |
|---|---|
| `named` | Named scope only. |
| `coupled` | Directly coupled artifacts required for coherence. |
| `closure` | Relevant dependency closure required for coherence. |
| `systemic` | System-wide propagation until the relevant invariant is restored. |

Write reach is a ceiling, not a cleanup mandate.

The schema enforces:

```text
write_rank <= read_rank
```

An agent cannot be granted authority to modify farther than it may inspect.

## Continuity prior

| Value | Prior |
|---|---|
| `preserve` | Existing state and compatibility receive positive preservation weight. |
| `neutral` | Existing state has no special claim solely because it exists. |
| `supersede` | Existing state may be transitional; prefer replacement when evidence supports supersession. |

Continuity is intentionally not an authorization axis. It is a decision prior used when multiple valid actions remain.

## Presets

A named posture is a preset over the schema.

### `maintenance`

```text
E=complete
R=closure
W=coupled
C=preserve
```

### `migration`

```text
E=challenge
R=system
W=closure
C=supersede
```

Repository-specific presets use the same schema under `.posture/presets/<name>.json`.

## Canonical rendering

Preset files contain only structured values. They do not contain the prose supplied to the model.

The POSTURE renderer owns the canonical natural-language meaning of every enum value. This creates a single implementation of semantics across built-in presets, repository presets, Claude integration, Codex integration, and future providers.

Changing a preset changes which values are selected. Changing the meaning of a value is a schema/renderer change and therefore a tool version change.

## Mutation boundary

POSTURE state is persistent and explicit:

```text
posture set <preset>
posture clear
```

The agent may inspect the active state and recommend a different posture, but activation remains an explicit control-plane operation.

## Migration

Schema v1 active state contained arbitrary prose. It is not automatically interpreted.

`posture migrate` may translate a legacy active posture only when its provenance establishes a known bundled preset whose structured successor is defined.

Custom legacy prose is reported, not inferred.

This is a security and semantics property:

> changing the representation must not silently expand delegated authority.
