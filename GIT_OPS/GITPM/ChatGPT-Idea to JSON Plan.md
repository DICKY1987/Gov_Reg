# Idea to JSON Plan

**User:**   
**Created:** 4/16/2026 22:17:22  
**Updated:** 4/17/2026 12:18:08  
**Exported:** 4/17/2026 12:50:38  
**Link:** [https://chatgpt.com/g/g-p-69d5a430d8448191aa90599a0c798731-evertything-git/c/69e1a5f0-3af4-83ea-b341-29dace41ab33](https://chatgpt.com/g/g-p-69d5a430d8448191aa90599a0c798731-evertything-git/c/69e1a5f0-3af4-83ea-b341-29dace41ab33)  

## Response:
4/16/2026, 10:17:21 PM

Below is the **actual end-to-end process** from _idea → Jason (JSON) plan file_, reconstructed from your conversations, templates, and GitHub SSOT design.

This is not conceptual — this is the **deterministic pipeline your system is already converging toward**.

* * *

0\. SYSTEM CONTEXT (NON-NEGOTIABLE)
===================================

*   **Planning SSOT = JSON/YAML plan artifacts**
*   **GitHub = execution surface**
*   **No work exists outside the plan**
*   **Everything maps to StepID → Issue → PR → Gate → Evidence**

PROC-DESIGN-GITHUB-AUTOMATION-S…

ChatGPT-Template to GitHub Mapp…

* * *

1\. IDEA → IDEA INTAKE CARD
===========================

### Input (minimum required)

*   `idea_title`
*   `idea_description`

### Output Artifact

```
{
  "idea_id": "IDEA-XXXX",
  "title": "...",
  "description": "...",
  "submitted_at": "...",
  "status": "RAW"
}
```

### Purpose

*   Capture **unfiltered user intent**
*   No structure enforcement yet

* * *

2\. IDEA → IDEA QUALIFICATION RECORD
====================================

### Transformation

Raw idea → evaluated for viability

### Adds:

*   feasibility
*   scope estimate
*   domain classification
*   priority

### Output Artifact

```
{
  "idea_id": "IDEA-XXXX",
  "qualified": true,
  "priority": "HIGH|MEDIUM|LOW",
  "complexity": "LOW|MEDIUM|HIGH",
  "domain": ["automation", "registry", "github"],
  "decision": "PROCEED|HOLD|REJECT"
}
```

### Gate

*   Reject weak / duplicate / out-of-scope ideas

* * *

3\. IDEA → CONCEPT BRIEF
========================

### Transformation

Idea → structured intent

### Adds:

*   problem statement
*   desired outcome
*   constraints
*   success criteria

### Output Artifact

```
{
  "concept_id": "CONCEPT-XXXX",
  "problem": "...",
  "objective": "...",
  "constraints": [],
  "success_criteria": []
}
```

### Purpose

*   Removes ambiguity
*   Forces clarity before design

* * *

4\. CONCEPT → DISCOVERY / SPEC PACKET
=====================================

### Transformation

Concept → explored solution space

### Adds:

*   existing systems analysis
*   alternatives
*   risks
*   dependencies

### Output Artifact

```
{
  "discovery_id": "DISC-XXXX",
  "options": [],
  "selected_approach": "...",
  "risks": [],
  "dependencies": []
}
```

### Purpose

*   Prevents rework
*   Anchors decisions early

* * *

5\. DISCOVERY → TECHNICAL DESIGN DOCUMENT
=========================================

### Transformation

Selected approach → full system design

### Adds (critical):

*   architecture
*   modules
*   components
*   data flows
*   contracts
*   interfaces

### Output Artifact

```
{
  "design_id": "DESIGN-XXXX",
  "architecture": {},
  "modules": [],
  "components": [],
  "interfaces": [],
  "data_flow": []
}
```

### Key Rule

This is the **last human-readable abstraction layer**

* * *

6\. DESIGN → PLAN-INPUT PACKET
==============================

This is where your system becomes **deterministic**

### Transformation

Design → machine-consumable inputs

### Adds:

*   normalized structure
*   IDs
*   decomposition rules
*   execution intent

### Output Artifact

```
{
  "plan_input_id": "PIN-XXXX",
  "normalized_modules": [],
  "normalized_components": [],
  "decomposition_rules": {},
  "execution_constraints": {}
}
```

### Purpose

*   Remove interpretation
*   Prepare for plan generation

* * *

7\. PLAN-INPUT → JASON PLAN FILE (FINAL OUTPUT)
===============================================

This is your **target deliverable**

* * *

Core Structure (simplified)
---------------------------

```
{
  "plan_id": "PLAN-XXXX",
  "plan_hash": "SHA256",
  "phases": [
    {
      "phase_id": "PH-01",
      "name": "...",
      "steps": [
        {
          "step_id": "STEP-001",
          "contract": {
            "inputs": [],
            "outputs": [],
            "invariants": [],
            "preconditions": [],
            "postconditions": []
          },
          "execution": {
            "method": "FULL_REWRITE | PATCH | AST",
            "targets": []
          },
          "gates": ["GATE-001", "GATE-002"],
          "evidence_required": [],
          "rollback": {}
        }
      ]
    }
  ],
  "milestones": [],
  "gate_definitions": [],
  "evidence_schema": {},
  "projection": {
    "github": {
      "enabled": true
    }
  }
}
```

* * *

8\. PLAN → GITHUB PROJECTION (AUTOMATIC)
========================================

From your system:

*   Step → Issue
*   Phase → Project Field
*   Gate → CI Check
*   Execution → PR
*   Evidence → Comment + Field

PROC-DESIGN-GITHUB-AUTOMATION-S…

ChatGPT-Template to GitHub Mapp…

* * *

Deterministic Mapping
---------------------

```
PLAN (SSOT)
    ↓
STEP → GitHub Issue
    ↓
PR → Execution
    ↓
CI → Gates
    ↓
Merge → Completion
    ↓
Evidence → Stored + Linked
```

* * *

9\. CRITICAL SYSTEM RULES (FROM YOUR ARCHITECTURE)
==================================================

These define how the pipeline behaves:

### 1\. No work without StepID

*   Every task must originate from plan  
    PROC-DESIGN-GITHUB-AUTOMATION-S…

### 2\. No PR without Issue

*   Execution must map to contract  
    PROC-DESIGN-GITHUB-AUTOMATION-S…

### 3\. No merge without gates

*   Validation is mandatory  
    PROC-DESIGN-GITHUB-AUTOMATION-S…

### 4\. Plan is SSOT

*   GitHub cannot override plan  
    PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

10\. FULL PIPELINE (COMPRESSED VIEW)
====================================

```
IDEA
  ↓
IDEA INTAKE CARD
  ↓
IDEA QUALIFICATION
  ↓
CONCEPT BRIEF
  ↓
DISCOVERY / SPEC PACKET
  ↓
TECHNICAL DESIGN DOCUMENT
  ↓
PLAN-INPUT PACKET
  ↓
JASON PLAN FILE (SSOT)
  ↓
GITHUB PROJECTION
  ↓
EXECUTION (PR)
  ↓
GATES (CI)
  ↓
EVIDENCE
  ↓
COMPLETION
```

* * *

11\. WHAT’S UNIQUE ABOUT YOUR SYSTEM
====================================

Most systems stop at:

> idea → tasks → execution

Your system adds:

*   **pre-plan artifact chain**
*   **deterministic plan compilation**
*   **strict contract-based execution**
*   **bidirectional traceability**
*   **fail-closed governance**

* * *

12\. REAL GAP (STRAIGHT ANSWER)
===============================

You are **90% there**, but missing:

### 1\. Formal schema for each pre-plan artifact

(you asked for this — partially defined but not enforced)

### 2\. Deterministic compiler:

```
Plan-Input → Jason Plan
```

### 3\. Explicit linkage:

```
idea_id → concept_id → design_id → step_id
```

### 4\. Artifact lifecycle (create / modify / delete / archive)

* * *

13\. BOTTOM LINE
================

*   The process is already defined implicitly across your system
*   It is **not fully formalized as a single pipeline spec**
*   The Jason plan file is the **first fully executable artifact**
*   Everything before it is **input refinement layers**

* * *

If you want next step:  
I can convert this into a **single machine-executable orchestration JSON** that wires every stage, artifact, and gate into one deterministic system.

## Response:
4/16/2026, 10:37:40 PM

Short answer: **yes, but only if panels are treated as a projection layer—not the source of truth.**  
If panels become the place where logic lives, your system breaks.

* * *

1\. WHAT YOU’RE ACTUALLY DESIGNING
==================================

You are not “building panels.”

You are defining a **GitHub submission interface layer** that sits between:

```
PLAN (SSOT JSON)
        ↓
PANEL CONFIG (UI STRUCTURE)
        ↓
GITHUB ARTIFACTS (Issues / Fields / PRs)
```

Panels = **controlled input/output surfaces** for GitHub artifacts.

* * *

2\. CORRECT APPROACH (NON-NEGOTIABLE)
=====================================

### Panels must be:

*   **Schema-driven (not manually designed)**
*   **Derived from the plan**
*   **Non-authoritative**
*   **Deterministically mapped to GitHub fields**

If you try to “design UI first,” you will:

*   duplicate logic
*   lose determinism
*   introduce drift

* * *

3\. WHAT A “PANEL” REALLY IS
============================

A panel is just a **structured form + mapping contract**

### Panel =

```
{
  "panel_id": "STEP_EXECUTION_PANEL",
  "source": "plan.step.contract",
  "fields": [],
  "layout": {},
  "github_mapping": {}
}
```

* * *

4\. REQUIRED PANEL TYPES
========================

You don’t need many. You need the right ones.

* * *

4.1 IDEA INTAKE PANEL
---------------------

**Purpose:** create Idea Intake Card

```
{
  "panel_id": "IDEA_INTAKE",
  "fields": [
    { "id": "title", "type": "text", "required": true },
    { "id": "description", "type": "textarea", "required": true }
  ],
  "output": "idea_intake.json"
}
```

* * *

4.2 PLAN STRUCTURE PANEL (READ-ONLY)
------------------------------------

**Purpose:** visualize plan hierarchy

*   phases
*   steps
*   dependencies

⚠️ No editing unless it writes back to plan JSON

* * *

4.3 STEP CONTRACT PANEL (CRITICAL)
----------------------------------

This is the most important one.

### Displays:

*   inputs
*   outputs
*   invariants
*   gates
*   evidence

```
{
  "panel_id": "STEP_CONTRACT",
  "source": "plan.phases[].steps[]",
  "fields": [
    "step_id",
    "inputs",
    "outputs",
    "invariants",
    "gate_requirements",
    "evidence_required"
  ]
}
```

* * *

4.4 EXECUTION PANEL
-------------------

**Purpose:** control PR + execution

Maps to:

*   PR creation
*   branch naming
*   execution method

* * *

4.5 GATE STATUS PANEL
---------------------

**Purpose:** show CI state

Maps to:

*   GitHub checks
*   pass/fail
*   logs

* * *

4.6 EVIDENCE PANEL
------------------

**Purpose:** display and validate outputs

Maps to:

*   artifacts
*   hashes
*   storage paths

* * *

4.7 GITHUB PROJECTION PANEL
---------------------------

This is the one you’re really asking about.

* * *

5\. GITHUB SUBMISSION PANEL (CORE)
==================================

This panel defines how data becomes GitHub artifacts.

* * *

5.1 STRUCTURE
-------------

```
{
  "panel_id": "GITHUB_PROJECTION",
  "sections": [
    "issue_definition",
    "project_fields",
    "milestone_assignment",
    "linkage",
    "validation"
  ]
}
```

* * *

5.2 ISSUE DEFINITION
--------------------

```
{
  "title_template": "[{step_id}] {summary}",
  "body_template": "{full_contract_markdown}",
  "labels": ["auto-generated"],
  "assignees": []
}
```

* * *

5.3 PROJECT FIELD MAPPING
-------------------------

Direct mapping from plan → GitHub

```
{
  "fields": {
    "StepID": "{step_id}",
    "Phase": "{phase_id}",
    "PlanHash": "{plan_hash}",
    "ProjectionVersion": "{projection_version}",
    "Status": "Todo"
  }
}
```

This must obey:

*   no hardcoded IDs
*   runtime resolution from registry  
    PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

5.4 MILESTONE LOGIC
-------------------

```
{
  "milestone": "{milestone_group}",
  "create_if_missing": true
}
```

* * *

5.5 LINKAGE SYSTEM (CRITICAL)
-----------------------------

```
{
  "step_to_issue": {
    "STEP-001": 123
  }
}
```

Stored in:

```
config/step_issue_linkage.json
```

This is required for:

*   traceability
*   PR validation
*   phase advancement

* * *

5.6 VALIDATION RULES
--------------------

Before submission:

```
{
  "rules": [
    "StepID must exist in plan",
    "Phase must exist",
    "No duplicate issues",
    "PlanHash must match"
  ]
}
```

* * *

6\. PANEL LAYOUT (HOW TO ORGANIZE)
==================================

Do NOT overcomplicate this.

* * *

Recommended Layout
------------------

```
LEFT COLUMN
-----------
- Plan Tree (phases → steps)

CENTER
-----------
- Step Contract Panel
- Execution Panel

RIGHT COLUMN
-----------
- GitHub Projection Panel
- Gate Status
- Evidence
```

* * *

Behavior
--------

*   Selecting a step → updates all panels
*   Panels are synchronized views of same data
*   No independent state

* * *

7\. CRITICAL DESIGN RULES
=========================

* * *

RULE 1 — PANELS NEVER OWN DATA
------------------------------

All data comes from:

```
PLAN JSON
or
GITHUB STATE
```

* * *

RULE 2 — ONE FIELD = ONE OWNER
------------------------------

Example:

| Field | Owner |
| --- | --- |
| Phase | Phase evaluator |
| Status | execution sync |
| StepID | projection system |

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

RULE 3 — NO BIDIRECTIONAL DRIFT
-------------------------------

*   Plan → GitHub = allowed
*   GitHub → Plan = forbidden

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

RULE 4 — PANEL = CONFIG, NOT CODE
---------------------------------

All panels should be defined like:

```
{
  "panel_id": "...",
  "fields": [],
  "layout": {},
  "mappings": {}
}
```

This lets you:

*   reuse panels
*   generate UI dynamically
*   keep system deterministic

* * *

8\. WHAT YOU’RE REALLY SOLVING
==============================

You are building:

```
CONFIG-DRIVEN UI → GITHUB AUTOMATION COMPILER
```

Not a UI.

* * *

9\. IS THIS THE RIGHT APPROACH?
===============================

### Yes — IF you do it like this:

*   Panels = thin, config-driven
*   Plan = SSOT
*   GitHub = execution surface
*   Mapping = explicit and enforced

* * *

### No — if you:

*   design UI manually
*   let users edit GitHub data directly
*   duplicate plan logic in panels
*   skip linkage system

* * *

10\. NEXT STEP (WHAT YOU SHOULD DO)
===================================

Define this file:

```
panels/
  github_projection.panel.json
  step_contract.panel.json
  execution.panel.json
```

Then build:

```
renderer → reads panel config → renders UI
mapper → reads panel config → writes GitHub
```

* * *

If you want, next step:  
I can define a **complete panel schema + rendering engine spec + GitHub mapping engine** that plugs directly into your system.

## Response:
4/16/2026, 10:38:54 PM

> Thought for 5s

That automation is the **projection/reconciliation layer**.  
It is not optional. Without it, the interface is just a dead form.

What you need is not “submit panel data to GitHub.”  
You need a **controlled automation pipeline** that takes interface data, validates it, resolves GitHub IDs, writes to the correct GitHub surface, and records linkage/evidence.

Correct model
=============

```
PANEL / INTERFACE
      ↓
NORMALIZED SUBMISSION PAYLOAD
      ↓
PROJECTION ENGINE
      ↓
GITHUB PROJECTS / ISSUES / MILESTONES / PR LINKAGE
      ↓
RECONCILIATION + DRIFT REPORT
```

The key distinction
===================

There are really **two separate automations**:

1\. Submission automation
-------------------------

This moves data from your interface into GitHub artifacts.

Examples:

*   create/update issue
*   add issue to project
*   set project fields
*   assign milestone
*   update status
*   write StepID linkage

2\. Reconciliation automation
-----------------------------

This checks whether GitHub still matches what the plan/interface intended.

Examples:

*   detect missing project item
*   detect wrong phase/status
*   detect orphan issue with no StepID
*   detect mismatch between PlanHash in plan vs GitHub
*   re-apply missing fields or flag override/drift

Your own GitHub SSOT design already defines this as an **observe → diff → act → report** reconciliation controller, not a one-time form submit.

PROC-DESIGN-GITHUB-AUTOMATION-S…

compass\_artifact\_wf-4a39ee83-b5…

What the automation should actually do
======================================

Stage 1: interface capture
--------------------------

The panel should emit a normalized payload like:

```
{
  "submission_type": "step_projection",
  "step_id": "STEP-001",
  "phase_id": "PH-01",
  "title": "[STEP-001] Build projection engine",
  "body": "...rendered contract...",
  "milestone_group": "Projection MVP",
  "plan_hash": "abc123",
  "projection_version": 4
}
```

This payload is not yet GitHub-specific enough to mutate GitHub safely.

Stage 2: validation
-------------------

Before any write:

*   StepID must exist
*   phase must exist
*   milestone group must be valid
*   payload must match current plan hash
*   field registry must be present
*   automation-only fields must not be user-overridden

Your process design already requires fail-closed behavior if the field registry is missing or invalid.

PROC-DESIGN-GITHUB-AUTOMATION-S…

Stage 3: GitHub field/option resolution
---------------------------------------

Do **not** hardcode:

*   project node id
*   field ids
*   option ids
*   iteration ids

Those must come from `config/github_field_registry.json`, generated by the bootstrap workflow. That is explicitly required by `LAW-GH-002`.

PROC-DESIGN-GITHUB-AUTOMATION-S…

CLAUDE

Stage 4: projection apply
-------------------------

Then the automation performs the actual GitHub mutations:

1.  Create issue if the step has no linked issue yet
2.  Add issue to project
3.  Set StepID field
4.  Set Phase field
5.  Set PlanHash
6.  Set ProjectionVersion
7.  Assign milestone if applicable
8.  Save linkage into `config/step_issue_linkage.json`

That exact projection pattern is already described in your SSOT process design.

PROC-DESIGN-GITHUB-AUTOMATION-S…

The most important rule
=======================

This should be **automation-owned**, not user-owned.

The user can fill interface data, but the system should own the actual write path for:

*   Phase
*   Status
*   EvidenceState
*   DeterminismState
*   PlanHash
*   ProjectionVersion
*   GateStatus

Your design already classifies those as automation-only fields.

PROC-DESIGN-GITHUB-AUTOMATION-S…

What GitHub surface gets written to
===================================

The automation does not write to “one GitHub thing.” It writes to multiple surfaces.

Issue layer
-----------

For the work record:

*   title
*   body
*   labels
*   milestone
*   repo issue number

Project layer
-------------

For execution tracking:

*   Phase
*   Status
*   StepID
*   EvidenceState
*   PlanHash
*   ProjectionVersion
*   GateStatus

PR layer
--------

For execution linkage:

*   PR references linked issue
*   merge closes issue
*   status transitions update project state

Evidence layer
--------------

For governance:

*   comment on issue with evidence seal
*   artifact path/hash recorded

That mapping is already the backbone of your template→GitHub model.

ChatGPT-Template to GitHub Mapp…

PROC-DESIGN-GITHUB-AUTOMATION-S…

The right automation architecture
=================================

You should split it into four small engines.

1\. Payload normalizer
----------------------

Converts panel output into deterministic submission JSON.

2\. Projection engine
---------------------

Applies desired state to GitHub.

This is your:

*   `GH_PROJECTION_GENERATE`
*   `GH_PROJECTION_APPLY`

Those programs are already called out in the SSOT process.

PROC-DESIGN-GITHUB-AUTOMATION-S…

3\. Sync/reconciliation engine
------------------------------

Scheduled + event-driven.  
Detects and heals drift.

Your hardening docs explicitly say robust systems must be **level-triggered**, not just event-triggered.

compass\_artifact\_wf-4a39ee83-b5…

CLAUDE

4\. Linkage/evidence writer
---------------------------

Maintains:

*   `config/step_issue_linkage.json`
*   projection registry
*   reports
*   evidence comments

What not to do
==============

Do not let the interface write directly to GitHub APIs
------------------------------------------------------

That creates:

*   duplicated logic
*   inconsistent field writes
*   no audit trail
*   no drift handling
*   no deterministic linkage

Do not let users manually set automation-owned fields
-----------------------------------------------------

That breaks ownership and reconciliation.

Do not mix “draft editing UI” with “authoritative GitHub mutation”
------------------------------------------------------------------

Those are two different concerns.

Best practical approach
=======================

Treat the interface as a **staging layer**, not the writer.

```
USER EDITS PANEL
      ↓
SAVE SUBMISSION DRAFT
      ↓
VALIDATE
      ↓
PROJECTION APPLY
      ↓
RECONCILE
      ↓
REPORT RESULT
```

That gives you:

*   rollback point
*   auditability
*   deterministic writes
*   safer retries

Straight answer
===============

Yes, you need automation that moves data from the interface into GitHub project management.

But the correct implementation is:

*   **interface captures intent**
*   **projection engine writes GitHub**
*   **reconciliation engine keeps GitHub aligned**
*   **linkage registry preserves traceability**

If you skip the projection/reconciliation layer and let the interface talk straight to GitHub, the system will turn into drift and field chaos fast.

The next artifact you likely need is a **submission payload schema + projection engine contract**.

## Response:
4/16/2026, 11:13:52 PM

I’m pulling the artifact chain and the GitHub/process artifacts together into one end-to-end inventory so the list is usable as a design backbone.

I found two useful strands: the pre-plan artifact chain and the runtime/package artifacts around planning, projection, and reconciliation. I’m opening the strongest sources so the final list can separate “required to define the plan” from “required to execute/govern it.”

> **Searching for relevant documents**
>
> I think I need to pull in information from past conversations and documents since the user is asking for design insights. I’ll search through relevant files for mentions of things like idea intake, concept briefs, technical designs, and other documents that might help clarify the requested artifacts.
>
> **Evaluating citation approach for file results**
>
> I need to provide citations based on file snippets, but the search results don’t include line numbers—only exact snippets are available. For factual claims, I might cite entire snippets. I’ll try using the document pointers and
>
> Thought for 25s

Yes. Below is the **artifact list needed for a functional idea → JSON plan process**, organized as a design inventory, not just a file dump.

I split it into four layers so you can see what is truly required versus what is runtime/governance support:

1.  **Definition artifacts** — needed to turn an idea into a valid plan
2.  **Refinement/control artifacts** — needed to iteratively improve and validate the plan
3.  **Execution/package artifacts** — needed once the JSON plan becomes a portable handoff package
4.  **GitHub projection artifacts** — needed if the process includes submission into GitHub Projects/Issues

This structure is grounded in your planning-only refinement loop, portable plan package model, and GitHub SSOT/projection design.

Planning-Only Refinement Loop

ChatGPT-GitHub Automation Files

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

A. Core definition artifacts
============================

These are the artifacts required to move from a raw idea to a usable JSON plan input set.

1\. Idea Intake Card
--------------------

**Process stage:** intake  
**Purpose:** captures the raw user request at the earliest possible point with minimal friction  
**Why needed:** this is the official start of the process; without it, later artifacts lose origin traceability

2\. Idea Qualification Record
-----------------------------

**Process stage:** screening / feasibility  
**Purpose:** records whether the idea should proceed, be deferred, merged, or rejected  
**Why needed:** prevents low-value or duplicate ideas from entering the expensive planning path

3\. Concept Brief
-----------------

**Process stage:** concept shaping  
**Purpose:** converts the raw idea into a clearer problem statement, objective, constraints, and success conditions  
**Why needed:** this is the first artifact that removes ambiguity from the idea

4\. Discovery / Spec Packet
---------------------------

**Process stage:** research / scoping  
**Purpose:** records alternatives, assumptions, risks, dependencies, and known system context  
**Why needed:** stops the plan from being built on unexamined assumptions

5\. Technical Design Document
-----------------------------

**Process stage:** design  
**Purpose:** defines architecture, modules, data flow, interfaces, boundaries, and solution structure  
**Why needed:** this is the last major human-facing design artifact before machine-oriented normalization

6\. Plan-Input Packet
---------------------

**Process stage:** plan compilation input  
**Purpose:** converts the design into normalized, machine-consumable planning inputs  
**Why needed:** this is the direct precursor to generating the JSON plan; it is where ambiguity should already be gone

7\. Artifact Intent Manifest
----------------------------

**Process stage:** design-to-plan bridge  
**Purpose:** declares which artifacts the process expects to create, modify, remove, or observe, and why  
**Why needed:** your validator work already shows this as critical for traceability between planned outputs and steps; it prevents “files appearing without purpose” and “steps with no declared outputs.”

terminal chat

8\. Master Application Plan / Program Plan
------------------------------------------

**Process stage:** portfolio / multi-phase orchestration  
**Purpose:** sits above individual phase plans and defines global scope, sequencing, milestones, shared constraints, and GitHub generation rules  
**Why needed:** your current phase plan is one level too low for full orchestration; this higher-order artifact is needed if the system manages multiple phase plans or large initiatives.

ChatGPT-Branch · GitHub Automat…

ChatGPT-GitHub Automation Files

* * *

B. Planning refinement and control-plane artifacts
==================================================

These are the artifacts needed to make the idea → JSON process deterministic, auditable, and bounded.

9\. Planning Run Manifest (`planning_run_manifest.json`)
--------------------------------------------------------

**Process stage:** run initialization  
**Purpose:** establishes run identity, artifact pointers, hashes, policy references, and run-level metadata  
**Why needed:** acts as the top-level record for a single planning run; the refinement loop treats it as foundational.

Planning-Only Refinement Loop

10\. Planning Policy Snapshot (`planning_policy_snapshot.json`)
---------------------------------------------------------------

**Process stage:** run initialization  
**Purpose:** freezes the rules, defect taxonomy, loop limits, and required sections for that run  
**Why needed:** ensures the run is fail-closed and not subject to shifting rules mid-process.

Planning-Only Refinement Loop

11\. Context Bundle (`context_bundle.json`)
-------------------------------------------

**Process stage:** grounding / context generation  
**Purpose:** stores the inventory-first grounding data the planner and critic are allowed to rely on  
**Why needed:** prevents invention and constrains the planning process to actual repo/system context.

Planning-Only Refinement Loop

12\. Context Bundle Signature (`context_bundle_signature.json`)
---------------------------------------------------------------

**Process stage:** grounding  
**Purpose:** records bundle hash, repo SHA, counts, and signature data  
**Why needed:** proves the context bundle is tied to a specific repo state and has not drifted.

Planning-Only Refinement Loop

13\. Plan Skeleton (`plan_skeleton.json`)
-----------------------------------------

**Process stage:** first structured plan output  
**Purpose:** creates a complete structural shell of the plan with all required sections present  
**Why needed:** makes the system produce a valid shape before it starts refining content.

Planning-Only Refinement Loop

14\. Plan Skeleton Schema Validation (`plan_skeleton_schema_validation.json`)
-----------------------------------------------------------------------------

**Process stage:** skeleton validation  
**Purpose:** proves the skeleton conforms to schema/policy  
**Why needed:** fail-closed check before refinement begins.

Planning-Only Refinement Loop

15\. Input Plan Snapshot (`in_plan.json`)
-----------------------------------------

**Process stage:** per-iteration refinement  
**Purpose:** stores the exact plan used as input to a specific refinement round  
**Why needed:** gives you iteration traceability and patch reproducibility.

Planning-Only Refinement Loop

16\. Output Plan Snapshot (`out_plan.json`)
-------------------------------------------

**Process stage:** per-iteration refinement  
**Purpose:** stores the plan after that round’s refinement  
**Why needed:** needed to compare before/after state deterministically.

Planning-Only Refinement Loop

17\. Plan Lint Report (`plan_lint_report.json`)
-----------------------------------------------

**Process stage:** critic analysis  
**Purpose:** lists hard and soft defects in the current plan  
**Why needed:** this is the main structured feedback artifact that drives refinement.

Planning-Only Refinement Loop

18\. Plan Dependency Graph (`plan_dependency_graph.json`)
---------------------------------------------------------

**Process stage:** critic analysis  
**Purpose:** records dependency relationships inside the plan  
**Why needed:** helps prove execution order is valid and identify hidden coupling; recommended, not optional in serious runs.

Planning-Only Refinement Loop

19\. Plan Cycles Report (`plan_cycles_report.json`)
---------------------------------------------------

**Process stage:** critic analysis  
**Purpose:** detects dependency loops  
**Why needed:** a plan with cycles is not execution-safe.

Planning-Only Refinement Loop

20\. Plan Scope Overlap Report (`plan_scope_overlap_report.json`)
-----------------------------------------------------------------

**Process stage:** critic analysis  
**Purpose:** detects overlapping write scopes or ambiguous ownership  
**Why needed:** prevents conflicting workstreams and nondeterministic execution.

Planning-Only Refinement Loop

21\. Plan Delta Patch (`plan_delta_patch_N.json`)
-------------------------------------------------

**Process stage:** refinement  
**Purpose:** records the exact RFC-6902 patch applied to move from one plan state to the next  
**Why needed:** your loop is patch-only; this is the proof of controlled mutation.

Planning-Only Refinement Loop

CLI application that implements…

22\. Refinement Round Record (`refinement_round.json`)
------------------------------------------------------

**Process stage:** per-iteration bookkeeping  
**Purpose:** records what happened in a single iteration  
**Why needed:** gives bounded-loop observability and aids debugging or oscillation detection.

Planning-Only Refinement Loop

23\. Iteration Hashes (`hashes.json`)
-------------------------------------

**Process stage:** per-iteration integrity  
**Purpose:** stores hashes for in-plan, out-plan, patch, lint outputs  
**Why needed:** supports deterministic verification and tamper detection.

Planning-Only Refinement Loop

24\. Refinement Termination Record (`refinement_termination_record.json`)
-------------------------------------------------------------------------

**Process stage:** loop termination  
**Purpose:** records why the refinement loop stopped  
**Why needed:** proves whether the final plan passed, failed, or terminated by bound.

Planning-Only Refinement Loop

25\. Final Plan (`99_final/plan.json`)
--------------------------------------

**Process stage:** final output  
**Purpose:** this is the actual machine-consumable JSON plan artifact  
**Why needed:** this is the end product of the idea → JSON process.

Planning-Only Refinement Loop

26\. Final Summary (`99_final/summary.json`)
--------------------------------------------

**Process stage:** final packaging  
**Purpose:** summarizes the final run outcome, plan quality, and termination state  
**Why needed:** gives operators and downstream tools a quick machine-readable recap.

Planning-Only Refinement Loop

* * *

C. Plan package and execution-handoff artifacts
===============================================

These become necessary once the final JSON plan needs to move between tools or into execution workflows.

27\. Portable Plan Package Spec
-------------------------------

**Process stage:** handoff contract design  
**Purpose:** defines the self-contained package structure passed between CLI applications  
**Why needed:** without this, multi-tool handoff is fragile and each tool invents its own package contract.

✳ Diagnose and improve computer…

28\. Program Specs (`programs/*.spec.json`)
-------------------------------------------

**Process stage:** execution preparation  
**Purpose:** declarative specs for automation steps such as intake, sync, validation, or projection  
**Why needed:** replaces ad hoc scripts with schema-driven, idempotent, reusable automation.

ChatGPT-GitHub Automation Files

✳ Diagnose and improve computer…

29\. Write Manifests (`write_manifests/*.json`)
-----------------------------------------------

**Process stage:** parallel / controlled execution  
**Purpose:** declares what each workstream is allowed to modify  
**Why needed:** required for single-writer governance and conflict detection.

ChatGPT-GitHub Automation Files

30\. Conflict Graph (`conflict_graph.json`)
-------------------------------------------

**Process stage:** workstream planning  
**Purpose:** computes which workstreams conflict  
**Why needed:** necessary for deterministic parallelization and merge safety.

ChatGPT-GitHub Automation Files

31\. Parallel Groups (`parallel_groups.json`)
---------------------------------------------

**Process stage:** scheduling  
**Purpose:** groups non-conflicting workstreams for concurrent execution  
**Why needed:** lets the system scale execution while preserving safety.

ChatGPT-GitHub Automation Files

32\. Worktree Map (`worktree_map.json`)
---------------------------------------

**Process stage:** isolated execution  
**Purpose:** maps workstreams to worktrees/environments  
**Why needed:** required when execution is physically isolated.

ChatGPT-GitHub Automation Files

33\. Execution Reports (`execution_reports/*.json`)
---------------------------------------------------

**Process stage:** execution observability  
**Purpose:** records the results of each execution unit  
**Why needed:** needed for evidence, debugging, and downstream reconciliation.

ChatGPT-GitHub Automation Files

34\. Touched Files Reports (`touched_files/*.json`)
---------------------------------------------------

**Process stage:** execution observability  
**Purpose:** records the actual files touched by workstreams  
**Why needed:** supports write-governance enforcement and comparison against declared manifests.

ChatGPT-GitHub Automation Files

35\. Patches (`patches/*.patch`)
--------------------------------

**Process stage:** code/document mutation evidence  
**Purpose:** stores actual changes applied during execution  
**Why needed:** preserves atomic change records and supports auditability.

ChatGPT-GitHub Automation Files

36\. Integration Report (`integration_report.json`)
---------------------------------------------------

**Process stage:** merge/integration  
**Purpose:** records post-integration status and any merge issues  
**Why needed:** required to prove the final integrated state is valid.

ChatGPT-GitHub Automation Files

37\. Determinism Report (`determinism_report.json`)
---------------------------------------------------

**Process stage:** final validation  
**Purpose:** proves the package and execution outputs meet determinism constraints  
**Why needed:** this is the final machine-readable proof that the process did not drift into ambiguity.

ChatGPT-GitHub Automation Files

38\. Evidence Bundle Index (`evidence_bundle_index.json`)
---------------------------------------------------------

**Process stage:** evidence packaging  
**Purpose:** indexes all evidence artifacts for the run  
**Why needed:** lets auditors or downstream automations find evidence without guessing.

ChatGPT-GitHub Automation Files

39\. Termination Record (`termination_record.json`)
---------------------------------------------------

**Process stage:** package closeout  
**Purpose:** records final process disposition at package level  
**Why needed:** closes the handoff package cleanly.

ChatGPT-GitHub Automation Files

* * *

D. GitHub projection artifacts
==============================

These are needed only if the idea → JSON process feeds GitHub project management automatically.

40\. Plan-to-GitHub Projection Contract
---------------------------------------

**Process stage:** projection design  
**Purpose:** formal mapping between plan objects and GitHub issues, project items, milestones, and fields  
**Why needed:** without it, mapping logic is implicit and drifts into scripts.

✳ Diagnose and improve computer…

41\. Field Ownership Matrix
---------------------------

**Process stage:** projection governance  
**Purpose:** declares who owns every field and state transition: plan, GitHub, orchestrator, or AI  
**Why needed:** this is the main defense against automation collisions and drift.

✳ Diagnose and improve computer…

42\. GitHub Field Registry (`config/github_field_registry.json`)
----------------------------------------------------------------

**Process stage:** GitHub bootstrap  
**Purpose:** stores runtime-discovered GitHub field IDs and option IDs  
**Why needed:** your GitHub process explicitly forbids inline field IDs; this registry is mandatory for safe mutation.

PROC-DESIGN-GITHUB-AUTOMATION-S…

43\. GitHub Projection Registry / Manifest (`github_projection_manifest.json` or `config/github_projection_registry.json`)
--------------------------------------------------------------------------------------------------------------------------

**Process stage:** projection generation  
**Purpose:** stores the desired GitHub-side representation of the plan  
**Why needed:** this is the desired-state artifact the projection engine applies.

ChatGPT-GitHub Automation Files

PROC-DESIGN-GITHUB-AUTOMATION-S…

44\. Step-Issue Linkage Table (`config/step_issue_linkage.json`)
----------------------------------------------------------------

**Process stage:** projection apply / traceability  
**Purpose:** maps `step_id` to GitHub issue number/item ID  
**Why needed:** required for PR linkage, reconciliation, and phase advancement; without it traceability breaks.

PROC-DESIGN-GITHUB-AUTOMATION-S…

45\. GitHub Override Registry (`github_override_registry.json`)
---------------------------------------------------------------

**Process stage:** override handling  
**Purpose:** records approved intentional divergence from plan-owned GitHub state  
**Why needed:** your research and hardening design both show that systems without escape hatches fail during real incidents.

PROC-DESIGN-GITHUB-AUTOMATION-S…

compass\_artifact\_wf-4a39ee83-b5…

46\. Sync Governance Policy (`policies/github_sync_governance.yaml`)
--------------------------------------------------------------------

**Process stage:** projection governance  
**Purpose:** defines ownership model, drift taxonomy, and reconciliation rules  
**Why needed:** this is the law file for unidirectional projection and automation-only fields.

PROC-DESIGN-GITHUB-AUTOMATION-S…

47\. Reconciliation Report
--------------------------

**Process stage:** scheduled/event reconciliation  
**Purpose:** records observe → diff → act → report results for GitHub drift handling  
**Why needed:** the research makes clear that projection without reconciliation is fragile and incomplete.

compass\_artifact\_wf-4a39ee83-b5…

ChatGPT-Branch · GitHub Automat…

48\. Phase Advancement Report (`phase_advancement_report.json`)
---------------------------------------------------------------

**Process stage:** composite lifecycle evaluation  
**Purpose:** records whether a phase is eligible to advance based on GitHub observed state plus plan rules  
**Why needed:** phase transitions cannot be event-only side effects; they must be decision artifacts.

PROC-DESIGN-GITHUB-AUTOMATION-S…

49\. Phase Transition Decision (`phase_transition_decision.json`)
-----------------------------------------------------------------

**Process stage:** phase advancement  
**Purpose:** exact rule outcome for advancing or blocking phase transition  
**Why needed:** acts as the authoritative decision record for automation-owned phase writes.

ChatGPT-Branch · GitHub Automat…

* * *

E. Governance / disposition artifacts
=====================================

These are needed to keep the process clean over time.

50\. Patch-to-Implementation Reconciliation Report
--------------------------------------------------

**Process stage:** post-change governance  
**Purpose:** maps requested change constructs to what was actually implemented  
**Why needed:** prevents later reviewers from reopening settled work due to structural deviations.

remaining\_modifications\_report

51\. Cleanup Policy
-------------------

**Process stage:** post-run governance  
**Purpose:** defines what evidence, backups, support inputs, and generated files are kept, archived, or deleted  
**Why needed:** your recent review shows technical work can outrun governance unless retention policy is explicit.

remaining\_modifications\_report

52\. Final Disposition Matrix
-----------------------------

**Process stage:** post-run cleanup  
**Purpose:** classifies every support artifact as authoritative, retained support, archival, or disposable  
**Why needed:** without this, every cleanup session re-runs the same analysis.

remaining\_modifications\_report

remaining\_modifications\_report

* * *

Recommended “minimum viable intended artifact list”
===================================================

If your immediate goal is to design the **idea → JSON** process only, and not full execution or GitHub automation yet, the minimum intended list is:

1.  Idea Intake Card
2.  Idea Qualification Record
3.  Concept Brief
4.  Discovery / Spec Packet
5.  Technical Design Document
6.  Plan-Input Packet
7.  Artifact Intent Manifest
8.  Planning Run Manifest
9.  Planning Policy Snapshot
10.  Context Bundle
11.  Context Bundle Signature
12.  Plan Skeleton
13.  Plan Skeleton Schema Validation
14.  Plan Lint Report
15.  Plan Delta Patch
16.  Refinement Round Record
17.  Iteration Hashes
18.  Refinement Termination Record
19.  Final Plan (`plan.json`)
20.  Final Summary (`summary.json`)

That is the smallest artifact chain that still gives you:

*   intake
*   qualification
*   concept formation
*   design
*   normalization
*   grounded planning
*   bounded refinement
*   deterministic final JSON output

* * *

Straight answer
===============

Yes, using an explicit **artifact list first** is the correct approach.

Right now, the process is strong conceptually but still mixes together:

*   input-definition artifacts
*   refinement-control artifacts
*   execution artifacts
*   GitHub projection artifacts
*   retention/governance artifacts

Separating them now will make the rest of the system design much cleaner.

The next useful move is to turn this into a **formal artifact inventory spec** with fields like:

*   `artifact_id`
*   `artifact_name`
*   `artifact_stage`
*   `required`
*   `producer`
*   `consumer`
*   `purpose`
*   `schema_required`
*   `authoritative`
*   `retention_class`

That would give you a machine-usable backbone for the whole process.

## Response:
4/16/2026, 11:27:06 PM

I’m checking current GitHub-native capabilities first so we can separate what already exists from what you’d still be forced to custom-build.

> **Searching GitHub Docs for current Projects features**
>
> [Using the built-in automations](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)
> [GitHub Projects: Import items based on a query and ...](https://github.blog/changelog/2026-02-19-github-projects-import-items-based-on-a-query-and-hierarchy-view-improvements/)
>
> **Clarifying API and templates for project management**
>
> I should mention what’s native and what's custom. Also, I could refer to documentation on API limits and project templates. It would be useful to check for issue fields, templates, actions for adding to a project, as well as how to manage those via the API, including issue forms.
>
> **Searching official docs on GitHub project management features**
>
> [Adding and managing issue fields](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-and-managing-issue-fields)
>
> Thought for 19s

Yes — **GitHub already has enough native project-management features to eliminate a meaningful chunk of the custom solution**. But it does **not** natively provide the full deterministic idea → governed JSON-plan → reconciliation architecture you’ve been describing. The right move is to **shrink the custom layer**, not assume GitHub can replace it. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/planning-and-tracking-with-projects?utm_source=chatgpt.com)

What GitHub can already do natively
-----------------------------------

GitHub Projects can already act as a solid **intake + tracking + visibility layer**. A project can track issues, pull requests, and draft ideas; it supports table, board, and roadmap views; and it has filters, grouping, sorting, charts, and custom fields. GitHub also supports project templates, so you can standardize much of the surface configuration instead of rebuilding that from scratch. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/planning-and-tracking-with-projects?utm_source=chatgpt.com)

GitHub can also reduce your need for a custom **idea intake** UI. Repository issue templates and issue forms let you define structured inputs, validations, default labels, and default assignees, and GitHub’s form schema includes an `upload` element for file attachments. That means a decent amount of “idea intake card / concept brief capture” can start inside GitHub instead of a separate front end. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)

GitHub also already supports **hierarchical work breakdown**. Issues can be decomposed into sub-issues, with up to 100 sub-issues per parent and up to 8 nested levels, and Projects can expose parent issue and sub-issue progress fields for grouping and filtering. That can replace a lot of custom hierarchy visualization and work-breakdown UI. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues?utm_source=chatgpt.com)

For project setup and standardization, GitHub templates are stronger than many people realize. A project template can carry views, custom fields, draft issues and associated fields, configured workflows except auto-add workflows, and insights. Copying an existing project also saves time configuring views and fields. That means your “panel layout / submission surface” may not need to be a custom application at all in the first version. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects?utm_source=chatgpt.com)

GitHub also has native **workflow automation** for basic routing. Built-in workflows can auto-add items, set status on events, and archive items automatically. Newer functionality also allows creating a project by importing items from a search query, which helps with quickly materializing an initiative from an existing issue set. [The GitHub Blog+3GitHub Docs+3GitHub Docs+3](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations?utm_source=chatgpt.com)

GitHub now also has better **structured metadata** than older label-heavy setups. Issue fields are organization-level structured metadata with API support, and Projects already supports custom project fields plus iteration fields. That reduces the need to invent a separate metadata store just to hold things like priority, effort, dates, or typed classification. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization?utm_source=chatgpt.com)

What GitHub can partially replace
---------------------------------

GitHub can partially replace your custom solution for:

*   **idea intake**
*   **initial triage**
*   **issue decomposition**
*   **status tracking**
*   **roadmap/iteration views**
*   **basic reporting**
*   **basic templates and standardized layouts**
*   **basic auto-routing into projects** [GitHub Docs+3GitHub Docs+3GitHub Docs+3](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)

GitHub can also partially replace a custom **submission layer** because Actions plus the GraphQL API already let you add items to projects and update field values. GitHub’s own examples show adding a PR to a project and then setting project fields from Actions. [GitHub Docs+1](https://docs.github.com/enterprise-cloud%40latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions?utm_source=chatgpt.com)

What GitHub does **not** replace
--------------------------------

GitHub does **not** natively give you a deterministic **idea → normalized pre-plan artifacts → JSON plan compiler**. It has structured issue intake and project metadata, but it does not have a native concept of “Idea Intake Card → Qualification Record → Concept Brief → Discovery Packet → Technical Design Document → Plan-Input Packet → final machine plan.” You would still need your own schemas, transformation rules, and artifact contracts for that. This is the main gap. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)

GitHub also does **not** natively provide a true **plan SSOT with controlled projection/reconciliation**. It can store and visualize work items, but it does not act like a formal controller that continuously reconciles a canonical external plan into GitHub state according to your laws about ownership, drift classes, and fail-closed behavior. You still need a custom projection/reconciliation layer if the plan lives outside GitHub. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects?utm_source=chatgpt.com)

GitHub also does **not** solve your **field-governance and identity discipline** by itself. Yes, there is API support, but you still need your own policies for StepID ownership, plan hash, projection version, evidence state, linkage tables, and override handling. GitHub gives mutation primitives; it does not impose your governance model for you. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects?utm_source=chatgpt.com)

GitHub project templates also stop short of being a full architecture substitute. They do not include auto-add workflows, and they do not encode your end-to-end deterministic transformation logic. They standardize the surface, not the deeper control plane. [GitHub Docs+1](https://docs.github.com/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects?utm_source=chatgpt.com)

The practical conclusion
------------------------

So the answer is: **something like part of it already exists, but not the whole thing**. GitHub already has enough native capability that building a full custom intake/planning UI first would probably be overbuilding. A better approach is:

1.  Use **GitHub-native intake and PM features first**
2.  Keep a **small custom layer only where GitHub is missing hard determinism**
3.  Build custom architecture only for:
    *   artifact schemas
    *   plan compilation
    *   projection/reconciliation
    *   governance/evidence/linkage enforcement [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)

What I would cut from the custom build right now
------------------------------------------------

I would **not** build a custom front-end for:

*   intake forms
*   project board layouts
*   hierarchy visualization
*   standard project templates
*   simple auto-add/status/archive flows
*   basic roadmap/chart reporting

GitHub already covers those well enough to start. [GitHub Docs+4GitHub Docs+4GitHub Docs+4](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)

What I would still custom-build
-------------------------------

I would still custom-build:

*   the **artifact schemas**
*   the **idea-to-plan transformation pipeline**
*   the **final JSON plan compiler**
*   the **projection manifest**
*   the **step↔issue linkage registry**
*   the **reconciliation/drift engine**
*   the **governance/evidence rules**

That is where GitHub stops and your architecture begins. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects?utm_source=chatgpt.com)

Straight answer
---------------

**Do not assume you need a full custom solution. You do not.**  
**Do not assume GitHub already solves your entire process. It does not.**

The right design target is:

```
GitHub native features for intake + planning surface + operational tracking
+
Custom deterministic layer for artifact compilation, governance, and reconciliation
```

That is the leanest version that still preserves your architecture.

I can turn this into a **build-vs-buy matrix** that lists every planned capability and marks it as:  
**GitHub-native / GitHub+light automation / custom required**.

---

**Sources:**

- [Planning and tracking with Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects?utm_source=chatgpt.com)

## Response:
4/16/2026, 11:30:35 PM

I’m testing the “GitHub-only” path against the actual gaps so the answer is about what you can stop building, not just what GitHub markets.

> **Browsing GitHub Docs for Project 2026 features**
>
> [Managing project templates in your organization](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization)
>
> **Searching for auto-adding items and project templates**
>
> [Managing project templates in your organization - GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization)
>
> **Searching GitHub docs for issue forms and imports**
>
> [Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
>
> **Considering GitHub alternatives without full customization**
>
> I think I should mention the possibility of using GitHub Actions and GraphQL for configuration instead of a completely custom UI. It's still a form of automation but works within GitHub's framework. The user asked for no custom solutions, but I can assess how close we can get to their goals by tweaking existing features like issue forms and templates. I’ll need to state the trade-offs and back it up with documentation.
>
> **Assessing GitHub workflows without custom solutions**
>
> [About tasklists](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists)
>
> **Adapting to a GitHub-only solution**
>
> To meet the user's "no custom solution" request, I think I should clarify that a GitHub-only approach means excluding external apps, but may still involve some GitHub Actions YAML or small scripts. We could suggest a no-code path using GitHub-only automation, or a light-code path with GitHub Actions. But if no custom architecture is allowed, we’ll have to shift the goals—relying on GitHub Issues/Projects for structure and dropping external JSON SSOT. This would mean using things like issue forms, project templates, and task lists for organization.
>
> Thought for 33s

Yes — **if you are willing to change the architecture goals slightly, you can get close enough on GitHub that a separate custom system probably is not worth building first**.

The core change is this:

**Stop treating JSON as the primary SSOT artifact.**  
Treat **GitHub Issues + Projects + structured fields + templates** as the operational and planning SSOT, and only emit JSON later if you still need it for a downstream tool.

That is the move that eliminates most of the custom architecture.

GitHub already gives you:

*   structured intake via **issue forms** with validations, defaults, labels, assignees, and file uploads [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)
*   standardized planning surfaces via **project templates** [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization)
*   typed planning metadata via **issue types** and **issue fields** [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization)
*   work decomposition via **sub-issues** and parent/sub-issue progress fields [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues?utm_source=chatgpt.com)
*   project-native ideas via **draft issues**, plus later conversion into real issues [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project)
*   built-in project automations and API/Actions automation for item/field changes [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)
*   charts and historical/current insights for reporting [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects?utm_source=chatgpt.com)

So the answer is not “GitHub does everything.”  
The answer is: **GitHub can do enough if you redesign the process around GitHub-native objects instead of around a custom artifact compiler.**

* * *

What has to change
------------------

Your current model is roughly:

```
idea → pre-plan artifacts → technical design → plan-input packet → JSON plan → GitHub
```

To avoid the custom solution, change it to:

```
idea form → GitHub issue → sub-issues / fields / project views → PR execution
```

And optionally:

```
GitHub state → export JSON snapshot only when needed
```

That gets you much faster adoption because GitHub becomes the main system, not the destination.

* * *

How to replace the “missing” custom pieces with GitHub-native substitutes
-------------------------------------------------------------------------

1\. Replace the pre-plan artifact chain with staged issue templates and issue types
===================================================================================

You do not need separate artifacts like:

*   Idea Intake Card
*   Qualification Record
*   Concept Brief
*   Discovery Packet

as independent files.

Instead, use:

*   **issue forms** to capture structured intake
*   **issue types** to distinguish Idea / Discovery / Design / Execution / Bug / Feature
*   **issue fields** for priority, effort, risk, target date, readiness, approval state

GitHub issue forms support structured inputs and validations, and issue types/fields give you organization-wide typed metadata. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms?utm_source=chatgpt.com)

### What this means

Instead of generating four artifacts, you create one issue with sections and typed metadata.

### Result

You lose some artifact purity, but keep the actual decision content.

* * *

2\. Replace the concept/design packet hierarchy with issue hierarchy
====================================================================

You do not need a custom hierarchy browser.

Use:

*   one **parent issue** for the initiative or feature
*   **sub-issues** for design, discovery, implementation units, and follow-on tasks
*   project views grouped by **Parent issue**
*   **Sub-issue progress** field for rollup

GitHub already supports sub-issues and project-level parent/progress fields. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues?utm_source=chatgpt.com)

### Example

Parent issue:

*   “GitHub-native planning model”

Sub-issues:

*   “Define intake form”
*   “Define issue type taxonomy”
*   “Define project template”
*   “Define automation rules”
*   “Pilot repo rollout”

That gives you a real planning tree without custom code.

* * *

3\. Replace a custom panel system with project templates + views
================================================================

You do not need to build custom panels for:

*   intake
*   hierarchy
*   planning board
*   status board
*   roadmap
*   reporting dashboard

Use:

*   **project templates** for layout standardization
*   table view for data entry and field editing
*   board view for workflow/status
*   roadmap view for dates/iterations
*   insights for dashboards

GitHub project templates are explicitly meant to share pre-configured projects in an organization. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization)

### Translation

Your “panels” become:

*   saved project views
*   issue forms
*   issue layouts
*   issue templates

That is close enough for a fast first system.

* * *

4\. Replace custom “idea staging” with draft issues
===================================================

If you want a lightweight place to capture incomplete ideas before they become full issues, GitHub already has **draft issues** inside Projects. They exist only in the project until converted into repo issues. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project)

That means your flow can be:

```
rough idea → draft issue in project → triage → convert to issue when accepted
```

That can replace a separate intake artifact repository.

* * *

5\. Replace a lot of custom classification logic with issue fields + issue types + labels
=========================================================================================

Your custom architecture was trying to track structured metadata externally.

GitHub now gives you:

*   **issue types** for classifying work categories [GitHub Docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization)
*   **issue fields** for structured organization-wide metadata like priority, effort, impact, or custom fields [GitHub Docs+1](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization)
*   **project custom fields** for execution-facing metadata on items in a project [GitHub Docs](https://docs.github.com/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects?utm_source=chatgpt.com)

### Better split

Use:

*   **issue fields** = planning inputs
*   **project fields** = execution-state outputs

That gets you most of the metadata control you were trying to custom-build.

* * *

6\. Replace part of the artifact lifecycle with issue state transitions
=======================================================================

You were heading toward a large artifact inventory and lifecycle model.

GitHub-only version:

*   **draft issue** = raw idea
*   **open issue** = accepted/planned
*   **sub-issues created** = decomposed
*   **project status** = execution state
*   **closed issue** = complete
*   **milestone** = delivery grouping
*   **archived item** = inactive historical state

Built-in project workflows can update status automatically based on events, and projects can auto-add or archive items. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)

This is less formal than your artifact model, but operationally it covers a lot.

* * *

7\. Replace custom reporting with project insights and saved views
==================================================================

GitHub already supports:

*   current charts
*   historical charts
*   filtered views
*   grouped views
*   roadmap views

Insights are built from project items directly. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects?utm_source=chatgpt.com)

That means you do not need to build a first-generation reporting subsystem.

* * *

8\. Replace custom decomposition aids with tasklists when full sub-issues are overkill
======================================================================================

GitHub tasklists can break work into smaller tracked tasks and can be converted into issues when needed. [GitHub Docs+1](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists?utm_source=chatgpt.com)

Use this for lighter-weight decomposition when creating a full issue tree would be too much overhead.

* * *

What you still cannot truly replace without custom logic
--------------------------------------------------------

This is the hard part.

If you require these **exactly as stated**, GitHub-only will not fully do it:

### A. Deterministic external JSON plan compilation

GitHub does not natively turn issue/project state into your custom machine plan format. It can store the data, but it is not a plan compiler. The closest native automation path is Actions + API. [GitHub Docs+1](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

### B. Formal reconciliation controller with drift taxonomy

GitHub can automate state changes, but it does not natively implement your full “observe → diff → act → report” governance model across plan-owned vs automation-owned vs override states. The docs point you to built-in workflows, API, and Actions, not to a native reconciliation engine. [GitHub Docs+2GitHub Docs+2](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)

### C. Strict single-writer governance over fields like PlanHash, StepID, ProjectionVersion

GitHub has the primitives, but not your governance law layer. That still needs either discipline or custom automation. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

### D. Rich pre-plan artifact preservation as separate formal files

GitHub can hold the content, but as issues, comments, templates, and attachments rather than separate governed artifact files. [GitHub Docs+1](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository?utm_source=chatgpt.com)

* * *

The key question: can you alter the goals enough to avoid custom architecture?
------------------------------------------------------------------------------

Yes.

Here is the exact trade:

Keep these goals
----------------

*   structured intake
*   idea triage
*   hierarchy
*   milestone/phase tracking
*   execution status
*   basic governance
*   PR linkage
*   dashboards
*   fast startup
*   everything visible in GitHub

Relax these goals
-----------------

*   external JSON as first-class planning SSOT
*   separate artifact file for every pre-plan stage
*   deep deterministic compiler before planning starts
*   custom panel/rendering framework
*   custom reconciliation engine in v1
*   exact field-ownership enforcement in code from day one

If you make that trade, GitHub-only becomes realistic.

* * *

Recommended GitHub-only operating model
---------------------------------------

### Intake

Use **issue forms** with required structured sections:

*   idea
*   problem
*   desired outcome
*   constraints
*   dependencies
*   evidence uploads if needed

### Classification

Use **issue type** + **issue fields**:

*   Type: Idea / Discovery / Design / Execution
*   Fields: Priority, Effort, Risk, Approval, Target Date

### Planning

Use one **organization project template** with views like:

*   Intake
*   Qualified
*   Discovery
*   Design Ready
*   Execution Ready
*   In Progress
*   Review
*   Done
*   Archived

### Decomposition

Use:

*   **parent issue**
*   **sub-issues**
*   **tasklists** for lighter breakdown

### Execution

Use:

*   issues linked to PRs
*   milestones for delivery groups
*   built-in automations for simple status changes
*   GitHub Actions only where necessary for field updates

### Reporting

Use:

*   saved views
*   roadmap
*   insights charts

That can get you up fast with very little custom work. [GitHub Docs+3GitHub Docs+3GitHub Docs+3](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization)

* * *

My blunt recommendation
-----------------------

Do **not** build the custom architecture first.

Build a **GitHub-native v1** and only add custom logic if GitHub visibly fails you in practice.

Because right now, the highest-risk waste is spending weeks or months implementing:

*   custom forms
*   custom panels
*   custom hierarchy
*   custom metadata layer
*   custom dashboards
*   custom lifecycle artifacts

when GitHub already covers most of that.

* * *

Best practical decision rule
----------------------------

Adopt GitHub-only if you can accept this principle:

> “The planning truth lives in GitHub objects, not in a separately compiled JSON plan.”

If you cannot accept that, then you still need custom architecture.

If you **can** accept it, then a GitHub-native rollout is probably the smartest move.

* * *

Straight answer
---------------

Yes — by changing the approach, you can likely get to **80–90% of the intended outcome with GitHub only**, and get there much faster.

But the change required is not technical. It is architectural:

**GitHub must become the primary planning system, not just the execution surface.**

That is what removes the need for most of the custom solution.

I can turn this into a **GitHub-native replacement design** that maps your current intended artifacts and controls into:

*   issue forms
*   issue types
*   issue fields
*   project fields
*   project template views
*   sub-issue rules
*   milestone/iteration rules
*   minimal Actions automations

## Response:
4/16/2026, 11:38:50 PM

Here’s the comprehensive GitHub‑native replacement design, mapping your intended artifacts and controls into GitHub’s features and workflows:

GitHub‑Native Replacement Design for the Idea‑to‑Plan Pipeline
==============================================================

Background
----------

Your original process converted each idea into a chain of structured artifacts (Idea Intake Card, Qualification Record, Concept Brief, Discovery Packet, Technical Design Document, Plan‑Input Packet, JSON plan, etc.) before pushing the work to GitHub. Because maintaining a separate plan‑compiler and reconciliation engine is heavy, you asked whether GitHub’s native features could replace most of this architecture. The answer is “yes” – if you accept GitHub Issues and Projects as the **source of truth** and treat the JSON plan as an optional export rather than the primary control plane.

GitHub’s modern planning features include structured **issue forms**, **issue types**, **organization‑level issue fields**, **project fields** (including single‑select, date and iteration fields), **parent/sub‑issue relationships**, **boards** and **roadmaps**, **draft issues**, **milestones**, **project templates**, and built‑in or custom **automations**. These can replicate most of your artifact pipeline without a bespoke system.

Overview of Relevant GitHub Features
------------------------------------

*   **Issue forms & templates:** YAML‑based issue forms allow repositories to collect structured inputs; fields are converted to markdown in the issue body and can include text, dropdowns, checkboxes, uploads, and validation rules[docs.github.com](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms#:~:text=Syntax%20for%20issue%20forms). They can set default labels, assignees and can target specific projects[docs.github.com](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms#:~:text=You%20can%20create%20custom%20issue,labels%20for%20your%20issue%20forms).
*   **Issue types:** Organizations can define up to 25 custom issue types in addition to the defaults (task, bug, feature). Issue types classify work and support filtering and project views.
*   **Issue fields:** Issue fields let organizations add structured metadata—such as priority, effort, impact or any custom category—to every issue[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=Note). Field types include single‑select, text, number and date[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=You%20can%20create%20up%20to,following%20field%20types%20are%20available); the default fields Priority, Effort, Start date and Target date are customizable[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=Default%20fields).
*   **Project custom fields:** Projects support additional field types such as single‑select and iteration. Single‑select fields provide dropdowns with color‑coded options[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-single-select-fields#:~:text=You%20can%20create%20single%20select,selected%20from%20a%20dropdown%20menu). Iteration fields create recurring time blocks (e.g., sprints) and allow grouping/filtering by iteration[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=You%20can%20create%20an%20iteration,iteration%2C%20and%20sort%20by%20iteration).
*   **Parent issues and sub‑issue progress:** Projects can display a **Parent issue** field and **Sub‑issue progress** field to show relationships and completion progress between issues[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues). This enables hierarchical work breakdown within GitHub[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects#:~:text=Break%20down%20large%20issues%20into,smaller%20issues).
*   **Milestones:** Milestones track progress across a group of issues or pull requests with due dates, completion percentage and lists of open/closed items[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=You%20can%20use%20milestones%20to,pull%20requests%20in%20a%20repository). Issues and pull requests can be associated with a milestone and can be prioritized within it[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=You%20can%20use%20milestones%20to,pull%20requests%20in%20a%20repository).
*   **Project views (table, board, roadmap):** Projects can display items in table (spreadsheet‑like), board (kanban) or roadmap layouts. The board layout spreads items across columns keyed by a single‑select or iteration field; dragging cards adjusts their field values accordingly[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-board-layout#:~:text=About%20the%20board%20layout). Table layouts allow grouping, slicing and sorting by field values[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-table-layout#:~:text=About%20the%20table%20layout).
*   **Project templates:** Projects can be marked as templates; new projects created from a template inherit the template’s views, custom fields, draft issues and configured workflows[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization#:~:text=You%20can%20create%20a%20template%2C,the%20base%20for%20their%20projects).
*   **Built‑in workflows & automations:** Projects include default workflows that update item status when issues are closed or pull requests are merged[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed). You can configure workflows to auto‑archive items or auto‑add items from repositories based on filters[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=You%20can%20also%20configure%20workflows,automatically%20%20and%20%2057); auto‑add filters include qualifiers such as `label`, `is`, and `assignee`[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=About%20automatically%20adding%20items). GitHub Actions and the GraphQL API can automate more complex behaviours (e.g., adding PRs to projects and setting field values).

Mapping Intended Artifacts to GitHub Features
---------------------------------------------

The table below summarizes how each artifact or control from your original pipeline can be realized using GitHub’s planning features:

| Original artifact / control | GitHub‑native equivalent | Purpose & rationale |
| --- | --- | --- |
| **Idea Intake Card** | **Issue form** (YAML) with fields for title, problem description, desired outcome, constraints, attachments, etc.; optionally uses the default “Idea” issue type and default issue fields (priority, effort, dates). | Issue forms allow you to collect structured information from submitters and automatically apply labels, assignees and project placement[docs.github.com](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms#:~:text=You%20can%20create%20custom%20issue,labels%20for%20your%20issue%20forms). The collected data becomes the initial issue body and can be grouped or filtered within projects using fields. |
| **Idea Qualification Record** | **Custom issue fields** (e.g., “Feasibility”, “Complexity”, “Domain”) pinned to the “Idea” issue type[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=Issue%20fields%20let%20you%20add,all%20repositories%20in%20your%20organization); use single‑select options such as “Low/Medium/High” for complexity and a decision field (“Proceed/Hold/Reject”). | Instead of a separate document, the qualification data lives in structured fields on the same issue. Fields are organization‑wide and support filtering and grouping[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=Issue%20fields%20let%20you%20add,all%20repositories%20in%20your%20organization). |
| **Concept Brief** | **Issue template** or issue form section; store problem statement, objectives, constraints and success criteria as rich text in the issue body; optionally add a custom **“Concept ready?”** boolean field (single‑select). | The concept brief becomes part of the issue; there is no separate artifact. A custom field indicates readiness for the next stage. |
| **Discovery / Spec Packet** | **Sub‑issues** or **linked issues** for research tasks; record findings in the parent issue’s comments or as attachments; use an **“Exploration status”** field. | Breaking discovery tasks into sub‑issues enables parallel work and progress tracking[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects#:~:text=Break%20down%20large%20issues%20into,smaller%20issues). A field or label can mark the discovery phase. |
| **Technical Design Document** | **Linked design issue** or sub‑issue using the “Design” issue type; attach design documents or use the issue body for architecture details; include custom fields for architecture decision status. | A dedicated issue type keeps design discussions separate while preserving hierarchy. Design issues can have their own sub‑issues if the design requires decomposition. |
| **Plan‑Input Packet / JSON plan** | **Project fields and views**; the normalized structure becomes project fields and grouped views (phases, steps, dependencies). If needed, a JSON export can be generated from project data via API but is not required for day‑to‑day planning. | Treat the project as the plan SSOT: phases correspond to single‑select fields (“Phase”); steps correspond to issues; dependencies can be expressed via blocking relationships or links. |
| **Artifact Intent Manifest** | **Custom fields** on the issue or project (e.g., “Declared outputs”) and a checklist in the issue body; or use sub‑issues to represent intended artifacts. | Each output becomes a sub‑issue or checklist item, making intended deliverables visible and trackable. |
| **Planning run manifest / policy snapshot** | **Project template settings and organization‑level guidelines**; record the planning policies in a repository README or wiki. | Since GitHub becomes the SSOT, you do not need separate manifest files; the project template encodes the baseline views, fields and workflows[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization#:~:text=You%20can%20create%20a%20template%2C,the%20base%20for%20their%20projects). |
| **Context bundle & signature** | **References and attachments** within the issue; if your process requires capturing inventory context, attach the analysis documents or link to repository files. | GitHub does not provide tamper‑proof signatures; if required, you can store checksums in a field or comment. |
| **Plan Skeleton & Lint Reports** | **Project views** configured via templates; required fields ensure completeness; built‑in workflows can flag missing values. | Instead of generating skeleton JSON and linting it, define required fields in issue forms and use built‑in workflows to set status or remind users when fields are empty. |
| **Refinement rounds & delta patches** | **Issue comments and edits**; design refinements occur as edits and comments on the issue; sub‑issue tasks capture changes. | GitHub’s history preserves edits and discussions. You can label or tag iterations if needed. |
| **Phase advancement & gates** | **Project single‑select “Status” field** combined with **automations** that change status based on events (e.g., issue closed → Status “Done”)[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed); use additional fields for gate status (e.g., “Review passed/failed”). | Built‑in workflows update status automatically when issues or pull requests are closed or merged[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed). Manual changes or approvals are recorded as field changes. |
| **Evidence & linkage registry** | **Attachments and comments** on issues and pull requests; use the **“Parent issue”** and **“Sub‑issue progress”** fields to visualize relationships[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues); use issue links (e.g., “relates to”, “blocks”) to model dependencies; milestone or iteration fields track completion. | Evidence is stored directly on the issue; hierarchical relations are visible in project views. The need for a separate registry file disappears. |

Designing the GitHub‑Native Workflow
------------------------------------

1.  **Create an Idea Issue Form:**
    *   Define a YAML form in the repository’s `.github/ISSUE_TEMPLATE` folder. Use text inputs, text areas, dropdowns and file upload types to capture the required information[docs.github.com](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms#:~:text=Syntax%20for%20issue%20forms). Specify default labels (e.g., `idea`) and assign the issue to a project.
    *   Include fields for title, problem description, desired outcomes, constraints, dependencies, attachments, and optional fields like “Proposed priority” or “Domain”.
    *   When submitted, responses are converted to markdown and become the issue body[docs.github.com](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms#:~:text=You%20can%20create%20custom%20issue,labels%20for%20your%20issue%20forms). The issue will carry any default labels and will be added to the relevant project automatically.
2.  **Define Issue Types for Each Stage:**
    *   Use organization settings to create custom issue types such as _Idea_, _Discovery_, _Design_, _Implementation_, _Bug_ etc. Organization owners can create up to 25 issue types. Assign colors and descriptions to help users choose the appropriate type.
    *   Pin relevant issue fields to each issue type. For example, pin “Feasibility”, “Complexity”, and “Decision” fields to the Idea type; pin “Exploration Status” to Discovery; pin “Architecture status” to Design. Fields that are not pinned remain hidden until filled[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=,Click%20Create).
3.  **Create Organization‑Level Issue Fields:**
    *   In the organization’s Planning settings, create custom fields (single‑select, text, number, or date) to capture metadata needed for your process[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=You%20can%20create%20up%20to,following%20field%20types%20are%20available). Examples: `Feasibility` (Low/Medium/High), `Complexity` (Low/Medium/High), `Domain` (Automation/Registry/GitHub), `Decision` (Proceed/Hold/Reject), `Target Phase`, `Review Status`, `Evidence Link` etc.
    *   Default fields such as Priority and Effort can be retained and customized[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=Default%20fields).
    *   Pin these fields to appropriate issue types so they appear automatically when creating or viewing issues[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#:~:text=Pinning%20fields%20to%20issue%20types).
4.  **Set Up a Planning Project Template:**
    *   Create a project within the organization and configure it with the desired layouts and fields. Add custom fields like `Status` (single‑select: Idea, Discovery, Design, Implementation, Review, Done), `Phase`, `Plan Hash` (if you still want to store a checksum), `Review Result`, `Evidence State`, and `Iteration` (for sprints). Use a `Milestone` field or GitHub milestones to indicate major delivery targets[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=You%20can%20use%20milestones%20to,pull%20requests%20in%20a%20repository).
    *   Configure the table view to group items by `Status` or `Phase` and show essential fields. You can group by any field; dragging an item to another group automatically updates the field value[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-table-layout#:~:text=You%20can%20group%20items%20by,the%20value%20of%20the%20group).
    *   Configure a board view with columns mapped to the `Status` or `Phase` field. Dragging cards between columns automatically changes their status[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-board-layout#:~:text=About%20the%20board%20layout).
    *   Add a roadmap view if you want to visualize items on a timeline based on an iteration field[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=If%20your%20project%20makes%20use,view%20%20and%20%2050).
    *   Once configured, mark the project as a template so new projects will inherit the views, custom fields, draft issues, configured workflows and insights[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization#:~:text=You%20can%20create%20a%20template%2C,the%20base%20for%20their%20projects).
5.  **Use Sub‑Issues for Decomposition:**
    *   Break large issues into sub‑issues to represent tasks, discovery activities or deliverables. Sub‑issues add hierarchical relationships and support multiple levels of nesting[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects#:~:text=Break%20down%20large%20issues%20into,smaller%20issues).
    *   Enable the **Parent issue** and **Sub‑issue progress** fields in your project so that you can group by parent issue and see completion progress[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues). Filters allow you to display only sub‑issues of a particular parent[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=You%20can%20also%20filter%20by,type%20the%20filter%20in%20full).
    *   Use tasklists inside the issue body for lightweight checklists; GitHub can convert tasklist items into linked issues when necessary.
6.  **Define Milestones and Iterations:**
    *   Use GitHub milestones to group issues and pull requests by release or major deliverable. Milestones show a description, due date, completion percentage and the list of associated issues and pull requests[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=You%20can%20use%20milestones%20to,pull%20requests%20in%20a%20repository).
    *   Use an **Iteration** project field to plan work in repeating time blocks (e.g., sprints); iterations can have custom start dates, durations and breaks[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=You%20can%20create%20an%20iteration,iteration%2C%20and%20sort%20by%20iteration). You can filter or group by iteration and use roadmap views to visualize items across iterations[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=You%20can%20create%20an%20iteration,iteration%2C%20and%20sort%20by%20iteration).
7.  **Configure Built‑In Workflows:**
    *   Enable the default workflows so that when an issue or pull request in the project is closed or merged, the item’s status is set to “Done”[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed).
    *   Optionally configure a workflow that automatically sets `Status` to “Todo” when new items are added, or automatically archives items when they meet criteria[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed).
    *   Configure an **Auto‑add** workflow to add items from repositories when they match filters such as labels, assignees or open/closed status[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=About%20automatically%20adding%20items). This removes the need to manually add new issues to your project.
8.  **Add Custom Actions for Advanced Automations (Minimal):**
    *   If you need behaviours beyond the built‑in workflows, use GitHub Actions. For example, an action can trigger when a pull request is marked “ready for review” to add it to a project and set a field to `Needs Review`.
    *   Use the `actions/add-to-project` workflow maintained by GitHub to add an issue or pull request to a project with predefined field values.
    *   Actions can also compute a plan hash and write it to a field, copy data between fields, or validate that required fields are populated. Keep these automations minimal to avoid reproducing the complexity of your previous projection layer.

Summary
-------

Moving the planning workflow into GitHub simplifies your architecture by treating GitHub Issues and Projects as the **single source of truth**. Issue forms capture structured intake; issue types and fields encode classification and qualification; project fields, views, milestones and iterations become the “plan”; sub‑issues represent decomposition; and built‑in workflows and minimal GitHub Actions handle status transitions and auto‑addition of items. Templates ensure repeatability and consistency across projects[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/managing-your-project/managing-project-templates-in-your-organization#:~:text=You%20can%20create%20a%20template%2C,the%20base%20for%20their%20projects). This design replaces the complex chain of pre‑plan artifacts and a custom projection layer with native GitHub features while preserving the core goals of traceability, structure, and automation.

This report explains how to use issue forms, issue types, custom fields, project templates, sub‑issues, milestones/iterations and minimal automations to achieve your planning pipeline entirely within GitHub.

## Response:
4/16/2026, 11:44:27 PM

Thought for 24s

Your CLI applications should interact with GitHub through **four distinct channels**, not one.

1\. The real communication model
--------------------------------

```
CLI app
  ├─ A. Git transport        → clone / fetch / pull / push / PR branches
  ├─ B. REST API             → create issues, milestones, comments, PR metadata
  ├─ C. GraphQL API          → add items to Projects v2, update project fields
  └─ D. Event / reconcile    → webhook payloads, Actions events, scheduled polling
```

That is the clean model.

Your own subsystem design already treats GitHub as the **execution surface** and the plan/package as the authority, with projection and reconciliation between them.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

2\. What each channel is for
----------------------------

### A. Git transport

This is just code and file movement.

Use it for:

*   clone
*   fetch
*   pull
*   push
*   branch creation
*   PR source branches

This is separate from project management state.  
Git moves repository content. It does **not** create project items, set project fields, or assign milestones.

Your Git automation notes already separate the Git loop from the GitHub PM layer and recommend a deterministic Git adapter plus audit ledger.

Git automation subsystem

* * *

### B. REST API

Use REST for GitHub objects that are not Projects-v2-field-centric.

Use REST for:

*   create/update **issues**
*   create/update **milestones**
*   create/update **comments**
*   read/write some PR and issue metadata
*   repo operations not tied to Project v2 fields

This is where your CLI creates the actual issue records that users see in repositories.

* * *

### C. GraphQL API

Use GraphQL for **Projects v2** operations.

Use GraphQL for:

*   `addProjectV2ItemById`
*   `updateProjectV2ItemFieldValue`
*   reading project field definitions
*   reading option IDs for single-select / iteration fields
*   reading current project item state for reconciliation

Your design explicitly says Project field IDs and option IDs must be resolved at runtime from `github_field_registry.json`, and that item add + field update are separate calls.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

### D. Event / reconcile channel

This is how GitHub talks back.

There are two forms:

#### Event-triggered

Examples:

*   issue opened
*   PR opened
*   PR merged
*   check suite completed

These come into:

*   GitHub Actions event payloads
*   or your own webhook receiver

Your current workflow inventory already shows event-driven pieces like project item sync, milestone completion sync, phase sync, branch handling, and remote sync.

github\_project\_management\_proce…

#### Level-triggered reconciliation

This is the more important one.

Instead of trusting webhooks alone, your design requires scheduled reconciliation:

*   observe current GitHub state
*   compare to desired state from plan/package
*   correct drift
*   emit report

That “observe → diff → act → report” controller is the real backbone.

CLAUDE

compass\_artifact\_wf-4a39ee83-b5…

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

3\. What the CLI actually does behind the scenes
------------------------------------------------

The CLI should not be a dumb wrapper around `gh issue create`.

It should behave like an **orchestrated client** with a stable sequence:

```
1. Read plan / user intent
2. Normalize into internal command
3. Resolve GitHub IDs and mappings
4. Call REST/GraphQL
5. Record linkage locally
6. Verify result
7. Emit evidence/log
```

That is the correct behind-the-scenes behavior.

* * *

4\. The actual submission flow
------------------------------

Here is the practical flow for creating work from a CLI app.

### Case: create a new step as a GitHub issue

```
CLI command
  → load plan package / step definition
  → read step_issue_linkage.json
  → if no linked issue exists:
       REST: create issue
       GraphQL: add issue to Project
       GraphQL: set StepID, Phase, PlanHash, ProjectionVersion, Status
       REST: assign milestone if needed
       write step_id ↔ issue_number ↔ project_item_id to linkage file
  → return success + identifiers
```

That is already the intended architecture in your process design.

PROC-DESIGN-GITHUB-AUTOMATION-S…

ChatGPT-Template to GitHub Mapp…

* * *

### Case: create a sub-issue

Your CLI should:

1.  determine whether the design allows sub-issues for that step
2.  create the child issue
3.  link it to the parent
4.  add/update it in the project if your policy says sub-issues are also project items

Your SSOT design still flags sub-issue policy as an open design decision, which means your CLI should not guess this. It must follow the chosen policy once defined.

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

### Case: assign or create a milestone

Your CLI should:

1.  determine the delivery grouping from the plan
2.  REST: create milestone if absent
3.  REST: assign issue(s) to milestone
4.  not treat milestone as phase

Your mapping documents are clear that milestones are **delivery checkpoints**, while phases belong in the Project Phase field.

CLAUDE

ChatGPT-Template to GitHub Mapp…

* * *

5\. What GitHub sends back to your applications
-----------------------------------------------

GitHub talks back in three ways.

### 1\. API responses

After REST/GraphQL calls, GitHub returns:

*   issue number / node ID
*   project item ID
*   updated field values
*   errors / rate limit data

Your CLI should capture and persist these immediately.

* * *

### 2\. GitHub Actions event payloads

When things happen in GitHub, workflows receive event payloads.

Your own workflow bundle already assumes this pattern:

*   project item sync reacts to issue/PR lifecycle events
*   milestone completion reacts to close/reopen
*   branch handler reacts to PR events
*   phase sync reacts to plan file changes
*   scheduled orchestrator performs periodic control functions.
    github\_project\_management\_proce…
    ChatGPT-GitHub Automation Files

* * *

### 3\. Reconciliation observations

On a schedule, your app queries GitHub again and compares:

*   desired plan state
*   observed issue/PR/project/milestone/check state

That is how drift is caught:

*   orphan issues
*   missing items
*   wrong phase
*   wrong status
*   missing evidence
*   unauthorized manual changes.
    CLAUDE
    PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

6\. Authentication: how the CLI should authenticate
---------------------------------------------------

Do **not** design this around PATs as the normal path.

Your architecture already made the right call:

*   Projects access should use a **GitHub App installation token**
*   `GITHUB_TOKEN` cannot access Projects
*   PATs are exception-only

That rule is explicit in your SSOT and hardening delta.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

### Practical auth split

#### For local CLI use

You have two realistic choices:

**Option A — CLI calls a small internal service**

*   best for control
*   service owns GitHub App auth
*   CLI never handles app private keys directly

**Option B — CLI mints GitHub App installation tokens directly**

*   workable
*   but more operationally fragile
*   requires secure private key handling on the user machine

For your system, **Option A is better** if you want clean behind-the-scenes PM behavior.

* * *

7\. What should live in the CLI versus in GitHub Actions
--------------------------------------------------------

This is the split you want.

### CLI owns

*   user-facing commands
*   reading plan/package
*   local validation
*   deciding intent
*   packaging a request
*   showing useful output

### Actions / orchestrator own

*   authoritative GitHub field mutation
*   event handling
*   reconciliation
*   phase advancement
*   drift correction
*   evidence sealing

Your own design documents repeatedly point toward a central orchestrator and thin workflows rather than stuffing logic into many disconnected scripts.

ChatGPT-GitHub Automation Files

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

8\. The cleanest architecture for your goal
-------------------------------------------

Since you want to work through CLI apps while GitHub quietly powers project management displays, the best design is:

```
User
  ↓
CLI Application
  ↓
Local command model / plan package
  ↓
GitHub Integration Layer
    ├─ REST client
    ├─ GraphQL client
    ├─ Auth client
    ├─ Linkage registry client
    └─ Reconcile client
  ↓
GitHub
    ├─ Issues
    ├─ Milestones
    ├─ PRs
    ├─ Project items / fields
    ├─ Checks
    └─ Comments / evidence
```

That gives the user:

*   CLI-first workflow
*   GitHub board visibility
*   milestones
*   sub-issues
*   review tracking
*   progress charts

without requiring the user to manually maintain GitHub state.

* * *

9\. The minimum internal components your CLI stack needs
--------------------------------------------------------

You do **not** need one giant app. You need a small set of integration components.

### Required components

#### 1\. GitHub auth client

Issues installation token requests and refresh.

#### 2\. Field registry loader

Reads `github_field_registry.json` so nothing hardcodes Project field IDs.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

#### 3\. Issue/milestone REST client

Creates and updates:

*   issues
*   milestones
*   comments
*   labels when needed

#### 4\. Project GraphQL client

Adds project items and updates fields.

#### 5\. Linkage registry client

Reads/writes:

*   `step_issue_linkage.json`
*   projection registry
*   override registry if you keep it.
    CLAUDE
    PROC-DESIGN-GITHUB-AUTOMATION-S…

#### 6\. Reconciliation client

Queries GitHub and compares it to desired state.

* * *

10\. What the user experience should look like
----------------------------------------------

This is the practical outcome.

The user runs something like:

```
mycli plan sync
mycli step create STEP-042
mycli issue open STEP-042
mycli milestone ensure MILESTONE-ALPHA
mycli status reconcile
```

Behind the scenes, the CLI:

*   reads the plan
*   resolves IDs
*   creates/updates GitHub artifacts
*   records stable mappings
*   lets GitHub display the work naturally in Projects

So the user mostly lives in:

*   the CLI for control
*   GitHub for visibility and collaboration

That is the right division.

* * *

11\. Straight answer
--------------------

Your CLI applications should communicate with GitHub through:

*   **git transport** for code movement
*   **REST API** for issues, milestones, comments, and some PR operations
*   **GraphQL API** for Projects v2 items and field mutations
*   **event payloads + scheduled reconciliation** for feedback and state correction

And the proper architecture is:

*   CLI = command surface
*   GitHub = execution/project-management surface
*   Actions/orchestrator = behind-the-scenes state engine

That matches your current subsystem direction almost exactly.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

ChatGPT-Template to GitHub Mapp…

The next useful step is to define the **exact command-to-API mapping** for each CLI operation, such as `create_step`, `create_subissue`, `assign_milestone`, `sync_phase`, and `reconcile_drift`.

## Response:
4/16/2026, 11:56:59 PM

> **Searching for API specs in official docs**
>
> I need to refer to official documentation for the exact API command-to-API mapping, especially for GraphQL mutations. The snippets in the files are helpful but might not cover everything, so I’ll search specifically for the latest details in trusted GitHub or OpenAI resources to ensure accuracy.
>
> **Searching official GitHub docs for API endpoints**
>
> [REST API endpoints for issues - GitHub Docs](https://docs.github.com/en/rest/issues/issues)
>
> **Searching for open lines in the relevant area**
>
> [REST API endpoints for issues - GitHub Docs](https://docs.github.com/en/rest/issues/issues)
>
> **Searching for project API details to update fields**
>
> I need to add more details about updating a project item field value and handling sub-issues. I also want to explore if there's an idempotent method for dealing with item IDs. I’ll search the docs to make sure I'm using the API correctly for managing project fields and finding IDs.
>
> **Searching for API documentation on project updates**
>
> [Using the API to manage Projects - GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
>
> Thought for 28s

Below is the exact **command-to-API mapping** I would use for the GitHub-facing CLI layer.

This assumes the architecture you already defined:

*   GitHub is the **execution surface**
*   plan/package is the authority
*   Projects field IDs come from `config/github_field_registry.json`
*   step linkage is stored in `config/step_issue_linkage.json`
*   Projects writes use **GitHub App installation tokens**, not `GITHUB_TOKEN`, and not PATs as the normal path.
    CLAUDE
    PROC-DESIGN-GITHUB-AUTOMATION-S…

It also matches GitHub’s current API model:

*   **REST** for issues, milestones, and sub-issues
*   **GraphQL** for Projects v2 item add/update
*   Project node IDs, field IDs, option IDs, and iteration IDs must be resolved before mutation. [GitHub Docs+3GitHub Docs+3GitHub Docs+3](https://docs.github.com/en/rest/issues/issues)

* * *

0\. Common runtime contract for all commands
============================================

Every CLI command that mutates GitHub should follow this internal sequence:

```
load config → authenticate → resolve IDs → validate intent → call REST/GraphQL → persist linkage/evidence → verify → return result
```

Shared preflight
----------------

1.  Load:
    *   `config/github_field_registry.json`
    *   `config/step_issue_linkage.json`
    *   optional `config/github_override_registry.json`
2.  Mint GitHub App installation token
3.  Verify required IDs exist
4.  Validate the requested mutation against the plan and governance laws
5.  Execute API calls
6.  Write updated local registry/linkage artifacts
7.  Return machine-readable result

Your own SSOT explicitly requires runtime field resolution, fail-closed behavior if the registry is missing, and one named writer for automation-only fields.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

1\. `create_step`
=================

Purpose
-------

Create the GitHub issue that represents one step contract, add it to the project, set its project fields, and record the stable linkage.

CLI contract
------------

```
mycli create_step --step-id STEP-001 --repo owner/repo
```

Inputs
------

*   `step_id`
*   repo owner/repo
*   step data from plan/package:
    *   title
    *   body/contract markdown
    *   phase
    *   milestone\_group
    *   plan\_hash
    *   projection\_version

Preconditions
-------------

*   `step_id` must exist in the plan
*   `step_id` must not already be linked unless `--update-existing` is explicitly passed
*   field registry must already contain:
    *   project node ID
    *   Phase field ID + option IDs
    *   Status field ID + option IDs
    *   StepID field ID
    *   PlanHash field ID
    *   ProjectionVersion field ID

This matches your laws `LAW-GH-002`, `LAW-WORK-001`, and the projection phase in the process design.

PROC-DESIGN-GITHUB-AUTOMATION-S…

API sequence
------------

### Call 1 — REST: create issue

Use the REST “Create an issue” endpoint. It accepts GitHub App installation tokens and requires Issues write permission. [GitHub Docs](https://docs.github.com/en/rest/issues/issues)

```
POST /repos/{owner}/{repo}/issues
```

### Minimum body

```
{
  "title": "[STEP-001] <contract_summary>",
  "body": "<rendered step contract markdown>",
  "labels": ["planned-work"]
}
```

### Call 2 — GraphQL: add issue to project

Use `addProjectV2ItemById`. GitHub documents this as the mutation that links an existing content item to a Project. [GitHub Docs+1](https://docs.github.com/en/graphql/reference/mutations)

```
mutation {
  addProjectV2ItemById(input: {
    projectId: "PROJECT_ID",
    contentId: "ISSUE_NODE_ID"
  }) {
    item { id }
  }
}
```

### Call 3 — GraphQL: set StepID

Use `updateProjectV2ItemFieldValue`. GitHub documents this for project field mutation. [GitHub Docs+1](https://docs.github.com/en/graphql/reference/mutations)

For StepID as text:

```
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PROJECT_ID",
    itemId: "ITEM_ID",
    fieldId: "STEPID_FIELD_ID",
    value: { text: "STEP-001" }
  }) {
    projectV2Item { id }
  }
}
```

### Call 4 — GraphQL: set Phase

For a single-select field, GitHub requires `singleSelectOptionId`. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

```
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PROJECT_ID",
    itemId: "ITEM_ID",
    fieldId: "PHASE_FIELD_ID",
    value: { singleSelectOptionId: "PHASE_OPTION_ID" }
  }) {
    projectV2Item { id }
  }
}
```

### Call 5 — GraphQL: set Status

Same mutation pattern as Phase, usually defaulting to `Todo` or `Backlog`. GitHub’s built-in workflows can also set status automatically, but your CLI should only write Status if your ownership model says it is the writer for this transition.

### Call 6 — GraphQL: set PlanHash

Text field:

```
value: { text: "<sha256>" }
```

### Call 7 — GraphQL: set ProjectionVersion

Text or number field, depending on your field definition:

```
value: { text: "12" }
```

or

```
value: { number: 12 }
```

### Call 8 — REST: ensure/assign milestone if `milestone_group` exists

Use the REST milestones endpoint. “Create a milestone” accepts GitHub App installation tokens and Issues/Pull requests write permission. [GitHub Docs](https://docs.github.com/en/rest/issues/milestones)

If milestone missing:

```
POST /repos/{owner}/{repo}/milestones
```

Then assign the issue by updating the issue’s milestone through the Issues REST endpoint, because milestone is an issue property, not a project item field. GitHub explicitly says `updateProjectV2ItemFieldValue` cannot change Milestone. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

### Local writes

Update:

```
config/step_issue_linkage.json
{
  "STEP-001": {
    "issue_number": 123,
    "issue_node_id": "...",
    "project_item_id": "...",
    "repo": "owner/repo",
    "project_id": "...",
    "project_number": 5,
    "milestone": "MVP-Alpha",
    "projected_at": "2026-04-16T..."
  }
}
```

Returned result
---------------

```
{
  "command": "create_step",
  "step_id": "STEP-001",
  "issue_number": 123,
  "project_item_id": "PVTI_...",
  "milestone": "MVP-Alpha",
  "status": "created"
}
```

* * *

2\. `create_subissue`
=====================

Purpose
-------

Create a child issue and attach it under a parent issue.

CLI contract
------------

```
mycli create_subissue --parent-step STEP-001 --child-step STEP-001A --repo owner/repo
```

Inputs
------

*   parent issue reference:
    *   parent `step_id` or explicit `issue_number`
*   child step data
*   repo owner/repo

Preconditions
-------------

*   parent issue must already exist
*   child step must either:
    *   already have a GitHub issue created, or
    *   be created first by the command
*   sub-issue policy must allow this relationship

API sequence
------------

### Call 1 — if child issue missing: REST create issue

Same REST create issue endpoint as `create_step`. [GitHub Docs](https://docs.github.com/en/rest/issues/issues)

### Call 2 — REST: add sub-issue

GitHub now has a dedicated REST sub-issues API. “Add sub-issue” accepts GitHub App installation tokens and Issues write permission. It requires:

*   parent `issue_number`
*   child `sub_issue_id`
*   optional `replace_parent`. [GitHub Docs](https://docs.github.com/en/rest/issues/sub-issues)

```
POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues
```

Body:

```
{
  "sub_issue_id": 456789012,
  "replace_parent": false
}
```

Note: the API expects the child issue **ID**, not the issue number. [GitHub Docs](https://docs.github.com/en/rest/issues/sub-issues)

### Optional Calls 3+ — GraphQL project item alignment

If child issues are also tracked as project items:

*   `addProjectV2ItemById`
*   `updateProjectV2ItemFieldValue` for StepID, Phase, Status, etc. [GitHub Docs+1](https://docs.github.com/en/graphql/reference/mutations)

### Local writes

Update linkage registry with parent-child relation:

```
{
  "STEP-001A": {
    "issue_number": 124,
    "parent_step_id": "STEP-001",
    "parent_issue_number": 123
  }
}
```

Returned result
---------------

```
{
  "command": "create_subissue",
  "parent_issue_number": 123,
  "child_issue_number": 124,
  "status": "linked"
}
```

* * *

3\. `assign_milestone`
======================

Purpose
-------

Ensure a milestone exists and assign one or more issues to it.

CLI contract
------------

```
mycli assign_milestone --milestone MVP-Alpha --steps STEP-001 STEP-002 --repo owner/repo
```

Inputs
------

*   milestone title
*   optional description / due date
*   issue numbers or step IDs
*   repo owner/repo

Preconditions
-------------

*   milestone grouping must be valid under the plan
*   issues must already exist

Your mapping docs are explicit that milestones are **delivery checkpoints**, not lifecycle phases.

CLAUDE

ChatGPT-Template to GitHub Mapp…

API sequence
------------

### Call 1 — REST: get/list milestone if you need lookup

Use milestones REST endpoints.

### Call 2 — REST: create milestone if absent

```
POST /repos/{owner}/{repo}/milestones
```

GitHub documents this endpoint and token requirements. [GitHub Docs](https://docs.github.com/en/rest/issues/milestones)

Body:

```
{
  "title": "MVP-Alpha",
  "description": "Delivery checkpoint for MVP alpha",
  "due_on": "2026-05-15T00:00:00Z"
}
```

### Call 3 — REST: patch each issue to set milestone

Because milestone is an issue property, not a project item field, assign it through the Issues REST endpoint, not through `updateProjectV2ItemFieldValue`. GitHub explicitly documents that Milestone must be changed via issue/PR mutations. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

Body:

```
{
  "milestone": 7
}
```

### Optional project sync

No Project field write is required unless you also mirror milestone grouping into a custom project field.

Returned result
---------------

```
{
  "command": "assign_milestone",
  "milestone": "MVP-Alpha",
  "milestone_number": 7,
  "updated_issues": [123, 124]
}
```

* * *

4\. `sync_phase`
================

Purpose
-------

Project the plan’s current phase structure into GitHub without letting GitHub become the source of truth.

CLI contract
------------

```
mycli sync_phase --phase PH-02 --plan path/to/plan.json
```

Inputs
------

*   plan/package
*   target phase or all phases
*   linkage file
*   field registry

Preconditions
-------------

*   field registry valid
*   plan valid
*   phase option exists in project
*   `LAW-GH-003` respected: direct phase advancement must not be event-based guesswork

Your SSOT says phase writes are composite and must be backed by evaluator output, not by a single event.

PROC-DESIGN-GITHUB-AUTOMATION-S…

Two distinct modes
------------------

### Mode A — projection sync

Used when you are aligning issues to the plan’s declared phase placement.

### Mode B — phase advancement

Used only when the evaluator has produced `phase_transition_decision.json`.

Do not mix them.

* * *

Mode A — projection sync API sequence
-------------------------------------

For each linked step issue:

### Call 1 — GraphQL: ensure item is in project

```
addProjectV2ItemById
```

[GitHub Docs+1](https://docs.github.com/en/graphql/reference/mutations)

### Call 2 — GraphQL: update Phase field

Use `singleSelectOptionId` from registry. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

### Call 3 — GraphQL: update PlanHash / ProjectionVersion

Use text/number field mutation. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

### Call 4 — optional GraphQL: update Status if your ownership model allows

Only if this command is the named writer.

* * *

Mode B — advancement sync API sequence
--------------------------------------

Only run after evaluator artifact exists:

*   `phase_advancement_report.json`
*   `phase_transition_decision.json`

Your architecture delta requires that phase transitions occur only through the evaluator and decision artifact.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

Then:

1.  query current project item state
2.  compare current Phase vs desired next Phase
3.  mutate only if decision says `advance=true`
4.  record evidence artifact location and timestamp

Returned result
---------------

```
{
  "command": "sync_phase",
  "phase": "PH-02",
  "updated_items": 14,
  "skipped_items": 32,
  "mode": "projection"
}
```

* * *

5\. `reconcile_drift`
=====================

Purpose
-------

Observe current GitHub state, compare it to desired state from plan and local registries, classify drift, and correct only safe cases.

CLI contract
------------

```
mycli reconcile_drift --project 5 --repo owner/repo
```

Inputs
------

*   plan/package
*   field registry
*   linkage file
*   project ID / number
*   optional override registry

Preconditions
-------------

*   field registry valid
*   app auth valid
*   reconciliation rules loaded

Your architecture explicitly defines this as the governing primitive: **observe → diff → act → report**, level-triggered rather than edge-triggered.

CLAUDE

compass\_artifact\_wf-4a39ee83-b5…

PROC-DESIGN-GITHUB-AUTOMATION-S…

Drift classes to implement
--------------------------

Use the taxonomy already defined in your GitHub subsystem:

*   Allowed
*   Violation
*   Orphan
*   Missing
*   Override.
    CLAUDE

Read path
---------

### Read 1 — GraphQL: project items and fields

Query:

*   all project items
*   StepID
*   Phase
*   Status
*   PlanHash
*   ProjectionVersion
*   EvidenceState
*   GateStatus

GitHub documents that you first need the project node ID, then field IDs/options/iterations. [GitHub Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

### Read 2 — REST: issue state

For each linked issue, read:

*   open/closed
*   milestone
*   labels if needed
*   assignees if needed

### Read 3 — optional REST/Checks APIs

Read PR/check state if your reconciliation logic includes gate passage.

* * *

Diff rules
----------

### Missing

Plan says step exists, but no linked issue/project item exists.

**Action**

*   call `create_step` flow

### Orphan

Issue/project item exists with no valid StepID or no linkage entry.

**Action**

*   no automatic destructive correction
*   classify as Orphan
*   optionally open a flag issue or emit report only

This aligns directly with `LAW-WORK-001`.

PROC-DESIGN-GITHUB-AUTOMATION-S…

### Violation

Automation-only field differs from desired value and no approved override exists.

**Action**

*   GraphQL `updateProjectV2ItemFieldValue` to correct field
*   record correction in reconciliation report

### Override

Diff exists, but override registry authorizes it.

**Action**

*   do not correct
*   emit report entry only

### Allowed

Diff is in GitHub-owned field such as assignee/comment/review thread.

**Action**

*   no correction

Your ownership model explicitly splits plan-owned, GitHub-owned, and automation-only data.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

Write path
----------

For safe corrective writes:

### GraphQL corrections

Use:

*   `addProjectV2ItemById`
*   `updateProjectV2ItemFieldValue` for Phase, Status, StepID, PlanHash, ProjectionVersion, EvidenceState, GateStatus. [GitHub Docs+1](https://docs.github.com/en/graphql/reference/mutations)

### REST corrections

Use:

*   PATCH issue for milestone
*   comments for evidence notices
*   optional issue creation for missing steps. [GitHub Docs+1](https://docs.github.com/en/rest/issues/issues)

### Local write

Write:

*   `reconciliation_report.json`
*   updated linkage file if any missing items were created
*   updated projection registry if you keep it

Returned result
---------------

```
{
  "command": "reconcile_drift",
  "summary": {
    "allowed": 18,
    "violation": 3,
    "missing": 2,
    "orphan": 1,
    "override": 4
  },
  "corrected": [
    {"step_id": "STEP-002", "field": "Status", "from": "Backlog", "to": "In Progress"},
    {"step_id": "STEP-007", "action": "created_issue"}
  ],
  "report": "artifacts/reconciliation_report.json"
}
```

* * *

6\. The exact ownership split by command
========================================

`create_step`
-------------

Allowed to write:

*   issue creation
*   project item creation
*   StepID
*   Phase
*   Status only if designated
*   PlanHash
*   ProjectionVersion
*   milestone assignment

`create_subissue`
-----------------

Allowed to write:

*   child issue creation
*   parent/child relationship
*   child project item projection if policy allows

`assign_milestone`
------------------

Allowed to write:

*   milestone creation
*   issue milestone assignment only

`sync_phase`
------------

Allowed to write:

*   Phase
*   PlanHash
*   ProjectionVersion
*   optionally Status if this command owns that transition

`reconcile_drift`
-----------------

Allowed to write:

*   only safe corrections of automation-only fields
*   missing step creation if policy allows
*   never write back into the plan

That unidirectional rule is non-negotiable in your SSOT.

PROC-DESIGN-GITHUB-AUTOMATION-S…

* * *

7\. The exact protocol choice for each command
==============================================

*   `create_step`  
    REST issue create → GraphQL add-to-project → GraphQL field writes → REST milestone patch
*   `create_subissue`  
    REST issue create if needed → REST add sub-issue → GraphQL project sync if needed
*   `assign_milestone`  
    REST create milestone if needed → REST patch issues
*   `sync_phase`  
    GraphQL read current state → GraphQL Phase/metadata updates
*   `reconcile_drift`  
    GraphQL + REST read sweep → classify drift → GraphQL/REST corrective writes → report

* * *

8\. Straight recommendation
===========================

Implement these as **separate commands over a shared GitHub integration library**:

*   `GitHubAuthClient`
*   `GitHubIssuesClient`
*   `GitHubMilestonesClient`
*   `GitHubProjectsClient`
*   `LinkageRegistry`
*   `ReconciliationEngine`

Do not bury this logic directly in ad hoc CLI command files. The command layer should be thin; the integration layer should own:

*   token minting
*   ID resolution
*   mutation guards
*   retries / backoff
*   evidence output

Your own architecture already points in that direction: thin workflow shells, central policy, explicit program specs, and reconciliation-centered control.

CLAUDE

PROC-DESIGN-GITHUB-AUTOMATION-S…

The next useful step is to convert this into a **machine-readable command spec** for each operation, with request schema, preconditions, API call sequence, local artifact writes, and failure codes.

## Response:
4/17/2026, 2:09:29 AM

The machine‑readable command spec has been generated in JSON format and is available below:

[command\_spec.json](https://chatgpt.com/backend-api/estuary/content?id=file-ArLMvYucmeoZ8eVB2YvEjW&ts=493457&p=fs&cid=1&sig=7f53918b196764fec4e0d914cd1eda348a3ee38b9b3dda514fae2363c466bcb9&v=0)

In this spec you’ll find:

*   A **request schema** for each CLI operation (`create_step`, `create_subissue`, `assign_milestone`, `sync_phase`, and `reconcile_drift`) that defines the required and optional fields.
*   **Preconditions** that must be satisfied before the command can run (for example, ensuring a step ID exists in the plan or verifying that field registries are loaded).
*   A step‑by‑step **API call sequence** mapping each CLI action to the appropriate GitHub REST or GraphQL endpoint (for instance, `addProjectV2ItemById` must be called before updating any project fields[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects#:~:text=You%20cannot%20add%20and%20update,to%20update%20the%20item), and `updateProjectV2ItemFieldValue` cannot change milestone or assignees[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects#:~:text=You%20cannot%20use%20,may%20use%20the%20following%20mutations)).
*   A list of **local artifact writes** such as updates to `config/step_issue_linkage.json` or generation of reconciliation reports.
*   Enumerated **failure codes** describing predictable error conditions for each operation.

These command specifications are structured to integrate cleanly with GitHub’s API model—for example, adding items to Projects V2 via GraphQL then updating their fields, and using the sub‑issue REST endpoint with a `sub_issue_id` parameter when creating hierarchical relationships[docs.github.com](https://docs.github.com/en/rest/issues/sub-issues#:~:text=).

Feel free to import and adapt this JSON file directly into your CLI implementation.

## Response:
4/17/2026, 7:10:29 AM

Thought for 14s

Yes, hooks and automation should be added.

The system is **partially set up**, but it is **not yet complete enough to reliably move itself forward without user intervention**.

What already exists
-------------------

You already have the beginnings of the right event-driven chain:

*   `project_item_sync` reacts to issue and PR lifecycle events and updates project items and fields.
    Template to GitHub Mapping
*   `milestone_completion` reacts to close/reopen events and updates milestone-related progress.
    Template to GitHub Mapping
*   `splinter_phase_sync` watches plan/phase file changes and syncs them into GitHub Projects.
    Template to GitHub Mapping
*   `branch-handler` is intended to enforce PR discipline such as issue linkage and merge gating.
    github\_project\_management\_proce…
*   a `scheduled-orchestrator` exists as the seed of a central controller.
    ChatGPT-Branch · GitHub Automat…

So the answer is not “nothing exists.” Some of the right hooks are already present.

What is missing
---------------

The current setup still has major gaps.

Your own architecture docs say the GitHub layer is still missing the hardening pieces that make it self-moving and self-correcting:

*   field bootstrap registry
*   phase advancement evaluator
*   drift reconciliation loop
*   explicit sync governance rules
*   deterministic step↔issue linkage
*   enforcement that all work originates from the plan.
    CLAUDE
    Second Architecture Delta for G…

The most important missing piece is this:

**completion of an issue or milestone is not enough by itself to safely advance the process.**

Your hardening delta explicitly says phase advancement is **composite**, not event-based. It must be decided by a **Phase Advancement Evaluator** using:

*   open/closed issue state
*   required checks
*   PR merge state
*   evidence markers
*   optional milestone completion.
    Second Architecture Delta for G…

And that evaluator must run:

*   on key events
*   **and on a schedule**, so missed events do not leave the system stuck.
    Second Architecture Delta for G…

Straight answer on “is the system already set up to recognize these and make the appropriate changes?”
------------------------------------------------------------------------------------------------------

**Not fully.**

It is set up to recognize **some** events:

*   issue / PR lifecycle
*   milestone-related close/reopen patterns
*   phase file changes.
    github\_project\_management\_proce…
    Template to GitHub Mapping

But it is **not yet fully set up** to:

*   deterministically decide when a phase should advance
*   reconcile missed events
*   classify drift and repair it
*   move work forward automatically based on full completion criteria
*   guarantee that milestone completion triggers the right downstream actions every time.
    CLAUDE
    PROC-DESIGN-GITHUB-AUTOMATION-S…

The hooks/automation you should add
-----------------------------------

You should add these, in this order:

### 1\. `bootstrap-github-fields.yml`

This is required before everything else so workflows can resolve field IDs safely. Your docs explicitly require it.

ChatGPT-GitHub Automation Files

PROC-DESIGN-GITHUB-AUTOMATION-S…

### 2\. `GH_PROJECTION_GENERATE` + `GH_PROJECTION_APPLY`

These are needed so the CLI/app can create and maintain issues, milestones, and project items deterministically.

ChatGPT-GitHub Automation Files

✳ Find misplaced files in Gov\_R…

### 3\. `ssot-drift-reconciliation.yml`

This is the self-healing loop. It should run every 15 minutes or similar, and on push, to:

*   detect missing steps
*   detect orphan issues
*   detect unauthorized field edits
*   recreate or correct state when safe.
    ChatGPT-GitHub Automation Files
    ✳ Find misplaced files in Gov\_R…
    PROC-DESIGN-GITHUB-AUTOMATION-S…

### 4\. `phase-advancement-evaluator.yml`

This is the hook that should advance the process when work is actually complete. It should not be replaced by a simple “issue closed” trigger.

ChatGPT-GitHub Automation Files

Second Architecture Delta for G…

### 5\. Evidence-sealing post-step

After all required gates pass, the system should:

*   post evidence comment to linked issue
*   set `EvidenceState = Sealed`
*   set `GateStatus = Passed`.
    PROC-DESIGN-GITHUB-AUTOMATION-S…

### 6\. End-of-iteration / backlog hygiene automation

This is not fully formalized yet, but your recommended operating model already points toward:

*   stuck-item detection
*   backlog hygiene
*   missing-field enforcement
*   rollup metrics
*   periodic scans.
    ChatGPT-Branch · GitHub Automat…
    ChatGPT-GitHub Automation Files

The correct trigger model
-------------------------

You need both:

### Event-driven hooks

For immediate reactions:

*   issue opened/closed
*   PR opened/ready\_for\_review/merged
*   check suite completed
*   plan file changed

### Scheduled hooks

For convergence:

*   reconciliation every 15 minutes
*   field bootstrap daily
*   phase evaluation every 15 minutes or on key events.
    CLAUDE
    PROC-DESIGN-GITHUB-AUTOMATION-S…
    PROC-DESIGN-GITHUB-AUTOMATION-S…

That is the only reliable model. Your research synthesis is explicit that robust systems must be **level-triggered**, not just edge-triggered.

compass\_artifact\_wf-4a39ee83-b5…

Bottom line
-----------

*   **Yes**, more hooks/automation should be added.
*   **Yes**, some of the right event hooks already exist.
*   **No**, the system is not yet fully set up to automatically recognize completion and always make the correct next-state changes.
*   The two most important missing automations are:
    *   **phase-advancement-evaluator**
    *   **ssot-drift-reconciliation**

Those are the pieces that turn the current workflow set from “helpful scripts” into a true self-moving system.

ChatGPT-GitHub Automation Files

CLAUDE

The next useful step is an **event-to-transition matrix** showing exactly which GitHub event or scheduled job updates which field, artifact, or phase state.

## Response:
4/17/2026, 12:14:07 PM

Here are the requested workflows and automations, set up as GitHub Actions. Each workflow uses a GitHub App installation token (because the default `GITHUB_TOKEN` cannot access Projects) and follows GitHub’s recommended patterns for working with Projects via GraphQL[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token). The files are attached for easy import into your repository’s `.github/workflows/` directory.

1.  **`bootstrap-github-fields.yml`** – queries the organization project to discover all field identifiers and option IDs, writes them to `config/github_field_registry.json`, and commits the result back to the repository. This must run before any other workflow so that subsequent steps can reference the correct field IDs[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).  
    Attachment: [bootstrap-github-fields.yml](https://chatgpt.com/backend-api/estuary/content?id=file-Foy1sRXbFRdFeLrSojUPaX&ts=493457&p=fs&cid=1&sig=01364dba331034ffc9456a818512934240002ee4f654aa596f5a886d35bcdda7&v=0)
2.  **`gh-projection-generate.yml`** – reads your plan (e.g., `plan.json`) and generates a deterministic projection manifest under `projections/projection_manifest.json`. The manifest lists the issues, project items and milestones that need to exist to represent the plan. It commits the manifest for later review.  
    Attachment: [gh-projection-generate.yml](https://chatgpt.com/backend-api/estuary/content?id=file-5AKMHVjkVWQgsPZGz5x7M8&ts=493457&p=fs&cid=1&sig=db152413dd2f33fffa2e93d66da325d74dd6389e7e7a55a4161cc202a773be58&v=0)
3.  **`gh-projection-apply.yml`** – reads the projection manifest and applies it to GitHub. It’s structured to create issues, add them to the project with `addProjectV2ItemById`, then set their fields via `updateProjectV2ItemFieldValue`[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token). A placeholder shows where to implement the logic for creating issues and updating milestones, noting that milestones must be set via the REST API rather than GraphQL[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).  
    Attachment: [gh-projection-apply.yml](https://chatgpt.com/backend-api/estuary/content?id=file-36gHzQHAFScT7JUvDRKLSJ&ts=493457&p=fs&cid=1&sig=6fd6a64665a7be066cb72fb52eafe0ba926100c9bd42b9d6d21e21a56b669c5a&v=0)
4.  **`ssot-drift-reconciliation.yml`** – runs every 15 minutes and on pushes to the main branch. It compares the canonical plan and local registries with the current state of GitHub, detects missing or orphaned items, and corrects automation‑owned fields using GraphQL updates[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token). A placeholder is provided for the reconciliation logic.
    Attachment: [ssot-drift-reconciliation.yml](https://chatgpt.com/backend-api/estuary/content?id=file-Ct4GgubtPLaHNWWNRsPxFg&ts=493457&p=fs&cid=1&sig=e2184f5b33360b2d8660d4c870890a83c3c56084828ec6ddbb9dd425401c8c5e&v=0)
5.  **`phase-advancement-evaluator.yml`** – periodically evaluates whether a phase should advance by inspecting step completion, gate status and evidence, then writes a `phase_transition_decision.json` and updates the Phase fields if appropriate[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).  
    Attachment: [phase-advancement-evaluator.yml](https://chatgpt.com/backend-api/estuary/content?id=file-4oHpGtAuTfHpfEDT2rScME&ts=493457&p=fs&cid=1&sig=27aec0d0c292a4443ab6894c45cf4df70f100dfe4572cc7a456734dba385b60a&v=0)
6.  **`evidence-seal.yml`** – runs after a CI workflow completes successfully. It posts an evidence comment to the linked issue and sets the project item’s `EvidenceState` and `GateStatus` fields to “Sealed” and “Passed” via GraphQL[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).  
    Attachment: [evidence-seal.yml](https://chatgpt.com/backend-api/estuary/content?id=file-KjrDeiK78JDEwjYmwGdRGx&ts=493457&p=fs&cid=1&sig=dcc33479aa54d5c04afc423cc3a00990a597e75a6cfe3fe924eab527614f6569&v=0)
7.  **`backlog-hygiene.yml`** – a daily hygiene job that checks for stuck items, enforces required fields, rolls up metrics and prepares the board for the next iteration. It provides hooks to implement backlog‑cleanup logic and uses the same GraphQL mutation pattern for field updates[docs.github.com](https://docs.github.com/en/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).  
    Attachment: [backlog-hygiene.yml](https://chatgpt.com/backend-api/estuary/content?id=file-8rM6VKrenjmHkFFVHLUpdZ&ts=493457&p=fs&cid=1&sig=716906fb522de167ff39d158b2f610a4a5608d3abde4b57508f1c5e4bf2cd594&v=0)

Each workflow contains TODO comments indicating where your CLI or custom scripts should be called. Together, these automations provide a consistent bootstrap, projection, reconciliation, phase advancement, evidence sealing and hygiene framework, aligned with GitHub’s project API and your deterministic SSOT design.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)