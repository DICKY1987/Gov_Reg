Analysis Complete Process Map_NPP.md

---

## 1) What the process map gets right

### A. It’s the first usable “inventory of reality”

You did the most important thing: you mapped the current system as it actually exists—**gates → scripts → dependencies → where they run**. That’s the baseline you need for deterministic refactoring. 

### B. The 5-phase decomposition is structurally correct

Your phase groupings are coherent and align with execution intent:

* Pre-validation (placeholder/no-obfuscation)
* Core-validation (schema + plan internals)
* Automation (index + diagrams)
* Wiring (artifact flow + FM)
* Meta-validation (audit + goal reconciliation) 

### C. You correctly identify the true “special case”

GATE-012 as “FM aggregator” is the non-uniform component and the main place where the proposed “one runner for all gates” approach will break unless handled explicitly. 

---

## 2) Problems / inconsistencies in the map that will bite you during migration

### Issue 1 — Script count contradiction (needs correction)

You say:

* “44 individual scripts in scripts/ + scripts/wiring/”
  But the map’s enumerated gates + FM + utilities suggests:
* 1 (GATE-000)
* 5 (GATE-001..005)
* 3 (GATE-006..008)
* Wiring gates (GATE-010..013 plus 014..017) = 8
* Meta gates (998,999) = 2
* Optional gates = 5
* FM scripts = 12
  That’s already **36** (not counting some support scripts), and your “supporting scripts” list adds more. 

**Feedback:** Add a single authoritative line in the doc:

* “Total gate scripts = X”
* “Total FM scripts = 12”
* “Total supporting scripts = Y”
  And specify whether optional gates are included in “X”.

Right now “44” is plausible, but the doc should not require inference.

---

### Issue 2 — Duplicate listing / naming collision (FM-12)

You list:

* GATE-013 uses `wiring/...validate_e2e_proof_linkage.py`
  And also:
* FM-12 uses the same script name `...validate_e2e_proof_linkage.py` 

That’s either:

* a genuine dual-use script (bad for determinism unless explicitly designed), or
* a documentation duplication error.

**Feedback:** You must resolve this. If the same script is used as both:

* a gate, and
* an FM check inside the FM aggregator,
  then you have **two different call contracts** for the same code path, which becomes a migration hazard.

---

### Issue 3 — “Subsumes FM-*” creates overlap and possible double enforcement

You state:

* GATE-014 subsumes FM-01/02/04/05
* GATE-015 subsumes FM-09
* GATE-016 subsumes FM-08 

**Feedback:** This is a determinism smell unless clarified as one of:

1. “FM checks are legacy; subsuming gates replace them (FM removed)”
2. “FM checks are warnings; gates enforce fail-closed”
3. “FM checks run earlier; gates are redundant hard-stop backstops”

Right now, the map implies you might be checking the same invariants multiple times through different mechanisms. That increases drift and inconsistent outputs.

---

### Issue 4 — Optional gates aren’t integrated into the dependency story

You list optional gates with dependencies on GATE-001, but the orchestration flow doesn’t describe how they’re selected and how that selection affects determinism (`--only-required`). 

**Feedback:** Add a one-paragraph section:

* “Required vs optional gate selection rules”
* “How optional gates affect final status and evidence closure”
* “Whether optional gates produce GateResult-like artifacts the same way”

---

## 3) The map exposes the biggest refactor opportunity (and constraint)

### Opportunity: Many “gates” are actually *one of two types*

From your list, most scripts fall into:

1. **Pure validators** (read-only, emit report, exit 0/1)
2. **Generators** (produce automation index/diagrams)

That’s good: these can be normalized under a shared runner.

### Constraint: Some scripts are “meta-orchestrators”

* GATE-012 (aggregator)
* `run_all_e2e_proofs.py` (batch runner)
  These are not simple validator gates; they are “composites.”

**Feedback:** Your migration design must explicitly classify gate types:

* `type: validator | generator | composite`
  Otherwise you’ll build a shared runner that only fits 80% of your inventory.

---

## 4) What to add to the document (so it becomes executable)

Your map is currently a “human reference.” To make it actionable for the refactor, add these sections.

### Add Section A — Standard interface for every gate script (current-state contract)

For each gate script, record:

* Inputs (plan path, evidence dir, run_id)
* Outputs (exact evidence file names)
* Exit code meaning
* Any environment assumptions

This becomes the extraction basis for GateSpec.

### Add Section B — Evidence normalization checklist

For each script, list:

* evidence file(s) produced
* required fields
* whether schema validation exists today
* what is missing

### Add Section C — Canonical migration mapping

For each gate ID, add:

* `legacy_script_path`
* `future_gate_spec_path`
* `runner_mode: legacy | hybrid | spec`
* `conversion_status: not_started | in_progress | done`

This will let you migrate deterministically gate-by-gate.

---

## 5) Bottom line

Your process map is the right artifact and already valuable. 
To make it *migration-grade* and prevent refactor failure, you must:

1. Resolve the **FM-12 / GATE-013 duplication**.
2. Clarify the **subsumes FM-* overlap** policy (replace vs redundant vs warn).
3. Add an explicit **gate-type classification** (validator/generator/composite).
4. Replace “44 scripts” with authoritative totals and definitions.

If you want, I can convert this process map into a machine-consumable **Gate Inventory Registry JSON** (one record per gate/FM/support script) suitable for driving the GateSpec migration pipeline.
