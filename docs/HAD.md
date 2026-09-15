# HAD Design

POSTURE is designed using three distinct instruments:

> **H establishes and revokes the standing.  
> D validates, anchors, migrates, and supplies it.  
> A reasons within it.**

## H — Human

The human selects or clears an active posture, authors or approves bounded repository presets, and determines when project conditions justify changing the posture.

## D — Determinism

The deterministic layer validates profiles against the bounded schema, rejects unknown fields and invalid enum values, enforces `write reach <= read reach`, resolves presets, snapshots the exact active profile, detects drift, reinjects the profile, and migrates only legacy state with provable semantics.

D holds the prior. It does not decide how that prior applies to an individual case.

## A — Inference

The agent applies epistemic authority to ambiguous claims and framing, uses read reach to decide when broader investigation is permitted, uses write reach to determine whether consequences may be propagated, and uses continuity as a prior when deciding between preservation and supersession.

A may recommend a posture transition. It does not silently redefine or activate posture.

## Meaningful ambiguity

| | H | A | D |
|---|---|---|---|
| Define delegated standing | chooses | may advise | validates |
| Persist standing | — | — | owns |
| Apply standing to a case | — | owns | supplies |
| Infer facts | may supply | owns | does not |
| Change active posture | authorizes | may recommend | executes |
| Migrate legacy prose | decides if needed | does **not** infer authority | maps only known semantics |

The key boundary is that structured POSTURE values alter the **burden of proof**, not the outcome.

For example, `continuity=supersede` does not mean “delete legacy code.” It means existing code has no preservation claim merely because it exists. Evidence may still establish a real compatibility requirement.

Likewise `epistemic=reconstruct` does not mean “ignore the user.” It means the user's explanatory model is defeasible while explicit requirements and intent remain authoritative.

## Read/write separation

POSTURE preserves the distinction between seeing and doing. An agent can be granted broad read reach with narrow write reach, such as `R=system, W=named`. The inverse is invalid and rejected deterministically.

## Why free-form posture was removed

The original v0.1 design allowed arbitrary Markdown posture bodies. This made the abstraction dangerously open: a posture could become a goal, rulebook, persona, or prompt; an agent could author new standing using unconstrained prose; equivalent concepts could drift lexically; and migration had no mechanical validation surface.

The bounded schema closes that surface while keeping inference where it belongs: in applying the declared standing to real cases.
