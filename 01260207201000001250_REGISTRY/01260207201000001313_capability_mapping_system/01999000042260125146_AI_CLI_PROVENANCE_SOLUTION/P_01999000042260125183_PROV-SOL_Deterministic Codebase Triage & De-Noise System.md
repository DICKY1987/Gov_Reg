# DOC_ID: DOC-SCRIPT-1040
Deterministic vs Heuristic Layers
Deterministic Layer (Unchanged)

This layer:

Decides state

Enforces hard stops

Controls quarantine eligibility

It answers:

“Is this allowed to be retired or not?”

Nothing in the new system can override it.

Heuristic (Subjective) Layer (New)

This layer:

Generates hypotheses

Improves ranking

Identifies investigation priorities

Explains why something feels suspicious

It cannot:

Mark something obsolete

Override reachability

Bypass scream tests

Force quarantine

Why Subjective Signals Were Added

AI-generated code introduces failure modes that are invisible to traditional tooling:

High churn, low provenance

Semantic duplication with different shapes

Valuable logic hidden behind poor naming

Repeated regeneration across repos

Subjective signals allow the system to:

See patterns humans intuitively notice

Scale that intuition safely

Convert intuition into requests for deterministic evidence

New Capabilities Introduced
1. Negative Evidence Accumulation

Tracks absence over time.
Silence becomes measurable.

Enables confidence to increase without new scans.

2. Differential Replacement Proof

Proves supersession by behavior, not reachability.

This allows safe retirement of still-used but fully replaced code.

3. Cost vs Value Signals

Identifies AI-generated inefficiencies:

bloated imports

excessive memory

slow startup

Used for canonical selection, not deletion.

4. Reverse Dependency Surprise Test

Finds hidden foundational utilities.
Prevents catastrophic removals.

5. Cross-Repo Echo Detection

Detects organization-wide duplication.
Supports canonicalization at scale.

6. Entropy vs Structure Analysis

Prevents deleting:

ugly but correct AI code

Targets:

shallow scaffolding

prompt residue

7. Intent Drift Detection

Identifies files that outgrew their original purpose.
Supports relocation, extraction, or re-classification.

8. AI Provenance Signals

Used only for prioritization, never deletion.

9. Human Touch Frequency

Encodes collective human judgment as a soft signal.

10. Future-Use Likelihood

Avoids deleting code aligned with roadmap or upcoming work.

Why This Strengthens the System

Before:

Safe

Deterministic

Conservative

Now:

Still safe

Still deterministic

Faster convergence to confidence

Lower human review load

Better AI comprehension

The system now answers three questions instead of one:

Is this allowed to be removed? (deterministic)

How suspicious is this? (heuristic)

What evidence should we collect next? (actionable)

Final Positioning

This is no longer just a code cleanup framework.

It is a governed intelligence system for managing:

AI-generated code

Legacy systems

Continuous refactoring

Organizational technical debt

Determinism remains the law.
Heuristics become the scouts.