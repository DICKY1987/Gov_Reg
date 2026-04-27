```json
{
  "manifest_validation": "FAIL",
  "validation_result": {
    "reason": "The manifest is a strong governance inventory, but it is not yet a complete deterministic execution-control model.",
    "determinism_score": 78,
    "required_target_score": 100,
    "primary_failure": "It identifies conflicts and authority layers, but does not fully define machine-enforceable entry states, exit states, guards, transition rules, fallback paths, and canonical decision-storage semantics for every process and subprocess."
  },
  "gaps_identified": [
    {
      "gap_id": "GAP-001",
      "severity": "critical",
      "category": "single_source_of_truth",
      "finding": "The manifest admits competing documentation and unresolved authority conflicts.",
      "deterministic_failure_mode": "Different executors can choose different source documents and still appear compliant.",
      "required_correction": "Add a canonical_authority_resolution object with precedence, supersession, allowed references, blocked references, and fail-closed conflict behavior."
    },
    {
      "gap_id": "GAP-002",
      "severity": "critical",
      "category": "identity_model",
      "finding": "Structured DOC-* identity and numeric/P_ runtime identity remain unreconciled.",
      "deterministic_failure_mode": "Artifact lookup, ledger joins, registry projection, and audit replay can bind to different identifiers.",
      "required_correction": "Declare one canonical runtime identity model and one optional human-display alias model. Add migration_map, alias_policy, duplicate_id_policy, and validator gates."
    },
    {
      "gap_id": "GAP-003",
      "severity": "critical",
      "category": "decision_storage",
      "finding": "Decision storage is split across JSONL, SQLite, ad hoc JSON, and Markdown decision logs.",
      "deterministic_failure_mode": "Replay, audit, and automated validation cannot know which decision record is authoritative.",
      "required_correction": "Define one canonical DecisionEvent schema and one canonical write path. Other stores must be projections with declared derivation rules."
    },
    {
      "gap_id": "GAP-004",
      "severity": "critical",
      "category": "entry_exit_contracts",
      "finding": "The v3.3 files contain phase and step contracts, but the manifest does not require every process and subprocess to declare start_state, terminal_states, entry_guard, exit_criteria, and transition_events.",
      "deterministic_failure_mode": "A subprocess can be invoked or completed by implication instead of a mechanically checked boundary.",
      "required_correction": "Add process_state_machine and subprocess_contract objects to the planning JSON schema."
    },
    {
      "gap_id": "GAP-005",
      "severity": "high",
      "category": "state_transition_completeness",
      "finding": "State transitions exist, but invalid_transitions can remain empty and entry/exit actions are not formalized.",
      "deterministic_failure_mode": "Skipped states, ambiguous recovery, and unmodeled transitions remain possible.",
      "required_correction": "Require exhaustive allowed_transitions, forbidden_transitions, terminal_states, entry_actions, exit_actions, guard_expression, and evidence_output per transition."
    },
    {
      "gap_id": "GAP-006",
      "severity": "high",
      "category": "situational_determinism",
      "finding": "Situational behavior rules exist, but they are not yet equivalent to a formal decision table with hit policy, priority, exclusivity, and conflict resolution.",
      "deterministic_failure_mode": "Multiple rules can match, or no rule can match, without a provably deterministic outcome.",
      "required_correction": "Add DMN-style decision tables with hit_policy = UNIQUE or PRIORITY, explicit default = FAIL_CLOSED, and mandatory decision evidence."
    },
    {
      "gap_id": "GAP-007",
      "severity": "high",
      "category": "verification_commands",
      "finding": "Some ground-truth levels and template scaffolds allow empty command arrays or placeholders.",
      "deterministic_failure_mode": "A plan can look structurally valid while lacking executable verification.",
      "required_correction": "Concrete plan instances must reject empty commands unless the item is explicitly NOT_AUTOMATABLE with manual evidence."
    },
    {
      "gap_id": "GAP-008",
      "severity": "high",
      "category": "fallback_policy",
      "finding": "Fallback policy is declared, but authorized fallback behavior is not fully modeled as transition + evidence + terminal state.",
      "deterministic_failure_mode": "Fallback can become an ad hoc escape hatch.",
      "required_correction": "Each fallback must declare trigger_condition, source_state, target_state, allowed_action, evidence_path, owner, reversibility, and retry budget."
    },
    {
      "gap_id": "GAP-009",
      "severity": "high",
      "category": "parallel_execution",
      "finding": "The current model handles concurrency mostly through file conflict rules, not a full concurrency formalism.",
      "deterministic_failure_mode": "Deadlocks, missing joins, resource contention, and orphaned parallel branches can escape simple file-overlap checks.",
      "required_correction": "Use a Petri-net-style execution model for parallel phases: places, transitions, tokens, resource locks, join rules, deadlock checks, and soundness validation."
    },
    {
      "gap_id": "GAP-010",
      "severity": "medium",
      "category": "probabilistic_ai_boundary",
      "finding": "The manifest does not explicitly isolate probabilistic AI output from deterministic execution authority.",
      "deterministic_failure_mode": "An LLM recommendation can silently become an execution decision.",
      "required_correction": "Add probabilistic_boundary_policy: AI may classify, propose, or summarize, but only schema-valid deterministic rules may route, mutate, merge, or complete work."
    },
    {
      "gap_id": "GAP-011",
      "severity": "medium",
      "category": "retry_and_circuit_breaker",
      "finding": "Retry and circuit-breaker decision categories are acknowledged but not fully completed in the decision-elimination guide.",
      "deterministic_failure_mode": "Failure recovery can diverge by executor or run.",
      "required_correction": "Define retry_state_machine and circuit_breaker_state_machine with closed states, transition guards, budgets, evidence, and terminal outcomes."
    },
    {
      "gap_id": "GAP-012",
      "severity": "medium",
      "category": "generated_artifact_governance",
      "finding": "Generated artifacts are recognized, but the manifest itself does not enforce source-to-projection rebuild discipline.",
      "deterministic_failure_mode": "Generated indexes, inventories, or evidence can drift from source documents.",
      "required_correction": "Add generated_projection_policy with source_hash, generator_id, generator_logic_hash, output_hash, and rebuild_gate."
    }
  ],
  "research_comparison": {
    "similar_approaches": [
      {
        "approach": "Decision Model and Notation (DMN)",
        "fit": "Strong fit for deterministic decision tables, rule evaluation, input-data binding, and auditable decision services.",
        "manifest_gap": "The manifest lacks formal hit policies, rule-table exclusivity, executable decision expressions, and explicit decision service boundaries.",
        "recommendation": "Adopt a DMN-like decision_table object for routing, pattern selection, fallback selection, permission tiering, and manual-escalation decisions."
      },
      {
        "approach": "Deterministic-first AI architecture",
        "fit": "Strong fit for separating probabilistic interpretation from deterministic orchestration.",
        "manifest_gap": "The manifest does not explicitly declare that AI output cannot directly mutate state or select execution paths unless converted into schema-valid deterministic facts.",
        "recommendation": "Use AI only before deterministic gates or inside bounded interpretation steps; execution must be rule-bound, logged, and replayable."
      },
      {
        "approach": "Finite State Machines / Statecharts",
        "fit": "Superior fit for lifecycle control of plans, phases, steps, artifacts, gates, retries, fallbacks, and circuit breakers.",
        "manifest_gap": "Current lifecycle modeling lacks full entry actions, exit actions, guards, terminal states, and exhaustive invalid-transition rules.",
        "recommendation": "Use FSM/statechart objects for every lifecycle-bearing entity."
      },
      {
        "approach": "Petri Nets / Workflow Nets",
        "fit": "Superior fit for parallel workstreams, resource locks, fork/join behavior, deadlock detection, liveness, boundedness, and workflow soundness.",
        "manifest_gap": "Current concurrency rules are file-conflict based and do not formally prove workflow soundness.",
        "recommendation": "Use Petri-net-style execution_graph objects for simultaneous independent workstreams."
      }
    ],
    "superior_recommendations": [
      {
        "rank": 1,
        "model": "Hybrid DMN + FSM + Petri Net control plane",
        "decision": "recommended",
        "why": "DMN handles deterministic decisions; FSM handles lifecycle; Petri nets handle parallel workflow correctness. No single model covers all three cleanly."
      },
      {
        "rank": 2,
        "model": "FSM-only",
        "decision": "acceptable for serial execution",
        "why": "FSMs are excellent for explicit entry/exit paths but become awkward for high-concurrency workflows."
      },
      {
        "rank": 3,
        "model": "DMN-only",
        "decision": "not sufficient",
        "why": "DMN is good for decision logic, not full orchestration lifecycle or parallel resource-flow proof."
      },
      {
        "rank": 4,
        "model": "Petri-net-only",
        "decision": "too heavy as the only model",
        "why": "Petri nets are excellent for concurrency verification but overkill for simple rule selection and human-readable decision policies."
      }
    ]
  },
  "json_alignment_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "DeterministicExecutionControlPlaneRequirements",
    "type": "object",
    "required": [
      "canonical_authority_resolution",
      "decision_model",
      "process_state_machines",
      "subprocess_contracts",
      "execution_graph",
      "decision_ledger_contract",
      "probabilistic_boundary_policy",
      "evidence_contract"
    ],
    "properties": {
      "canonical_authority_resolution": {
        "type": "object",
        "required": [
          "canonical_sources",
          "precedence_order",
          "conflict_policy",
          "supersession_policy"
        ],
        "properties": {
          "conflict_policy": {
            "const": "FAIL_CLOSED"
          }
        }
      },
      "decision_model": {
        "type": "object",
        "required": [
          "decision_tables",
          "hit_policy_allowed_values",
          "default_no_match_action",
          "decision_evidence_path"
        ],
        "properties": {
          "hit_policy_allowed_values": {
            "type": "array",
            "contains": {
              "enum": [
                "UNIQUE",
                "PRIORITY",
                "FIRST"
              ]
            }
          },
          "default_no_match_action": {
            "const": "FAIL_CLOSED"
          }
        }
      },
      "process_state_machines": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "machine_id",
            "entity_type",
            "initial_state",
            "terminal_states",
            "states",
            "transitions",
            "invalid_transitions_policy"
          ],
          "properties": {
            "invalid_transitions_policy": {
              "const": "FAIL_CLOSED"
            },
            "transitions": {
              "type": "array",
              "items": {
                "type": "object",
                "required": [
                  "transition_id",
                  "from",
                  "to",
                  "event",
                  "guard",
                  "entry_action",
                  "exit_action",
                  "evidence_path"
                ]
              }
            }
          }
        }
      },
      "subprocess_contracts": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "subprocess_id",
            "parent_process_id",
            "entry_condition",
            "exit_condition",
            "inputs",
            "outputs",
            "invariants",
            "failure_modes",
            "rollback",
            "evidence"
          ]
        }
      },
      "execution_graph": {
        "type": "object",
        "required": [
          "graph_type",
          "places",
          "transitions",
          "tokens",
          "resource_locks",
          "deadlock_check",
          "soundness_check"
        ],
        "properties": {
          "graph_type": {
            "enum": [
              "PETRI_NET",
              "WORKFLOW_NET"
            ]
          }
        }
      },
      "decision_ledger_contract": {
        "type": "object",
        "required": [
          "canonical_storage",
          "schema_id",
          "append_only",
          "atomic_write",
          "required_fields"
        ],
        "properties": {
          "append_only": {
            "const": true
          },
          "atomic_write": {
            "const": true
          }
        }
      },
      "probabilistic_boundary_policy": {
        "type": "object",
        "required": [
          "ai_allowed_roles",
          "ai_forbidden_roles",
          "promotion_to_execution_rule"
        ],
        "properties": {
          "promotion_to_execution_rule": {
            "const": "ONLY_SCHEMA_VALIDATED_DETERMINISTIC_FACTS_CAN_AFFECT_EXECUTION"
          }
        }
      },
      "evidence_contract": {
        "type": "object",
        "required": [
          "per_transition_evidence",
          "per_decision_evidence",
          "per_mutation_evidence",
          "hash_algorithm",
          "replay_requirements"
        ],
        "properties": {
          "hash_algorithm": {
            "const": "SHA256"
          }
        }
      }
    }
  }
}
```

## Executive summary

**Verdict: FAIL for 100% deterministic adherence.** The manifest is valuable, but it is not yet the deterministic control plane. It says the corpus is “not one clean single source of truth,” identifies competing identity models, and identifies split decision-storage models. Those are hard blockers for deterministic replay and audit because two compliant-looking executors could follow different authority paths. 

The v3.3 project files are much stronger than the manifest itself. They already define source-of-truth files, generated artifacts, validators, gate runners, pattern runners, phase runners, mutation runners, and handoff runners. They also establish major invariants: no implied behavior, pattern-first execution, configuration-driven behavior, semantic path keys, and artifact intent before execution. 

The biggest architectural gap is formal modeling. Your current system has **pieces of an FSM**: lifecycle states, allowed transitions, run-status states, mutation-ledger states, atomic updates, and lock requirements. But it still needs full state-machine semantics: entry actions, exit actions, transition events, guards, invalid-transition exhaustiveness, and terminal states. The instruction document already tells agents to define lifecycle states and avoid ambiguous/skipped transitions, but the template still needs stricter schema-level enforcement. 

DMN is the right comparison point for deterministic decisions. OMG describes DMN as a notation for precise business decisions and rules, and Red Hat documents that executable DMN uses DRDs, decision logic, decision tables, and FEEL at higher conformance levels. Your manifest should borrow DMN-style **decision tables with hit policies** for routing, fallback, permission, pattern selection, and escalation. ([OMG][1])

For deterministic-first AI architecture, the industry pattern is: deterministic orchestration controls sequencing, approvals, audit trails, and execution; probabilistic AI is bounded to interpretation/recommendation inside governed steps. That matches your direction, but the manifest should explicitly ban LLM output from directly changing execution state unless converted into schema-valid deterministic facts. ([Kubiya.ai][2])

**FSM/statecharts are superior for lifecycle control.** They are the right structure for plan, phase, step, artifact, gate, retry, fallback, rollback, and circuit-breaker behavior. State-machine diagrams model discrete behavior through finite transitions, and guards enable or disable transitions based on Boolean conditions. ([UML Diagrams][3])

**Petri nets are superior for parallel execution.** Workflow nets, a class of Petri nets, are used to model and analyze workflows; their soundness property is specifically about avoiding livelocks, deadlocks, and other workflow anomalies. That makes them a better fit than plain DAG/file-conflict logic for simultaneous independent workstreams. ([Springer][4])

The superior design is not “FSM or Petri Net.” It is:

**DMN-style decision tables + FSM lifecycle machines + Petri-net execution graph + append-only decision/evidence ledger.**

That gives you deterministic decision selection, explicit entry/exit behavior, safe parallelism, replayable audit evidence, and fail-closed governance.

[1]: https://www.omg.org/dmn/ "Decision Model and Notation™ (DMN™) | Object Management Group"
[2]: https://www.kubiya.ai/blog/deterministic-ai-architecture "Deterministic AI Architecture: Why It Matters in 2025"
[3]: https://www.uml-diagrams.org/state-machine-diagrams.html "UML State Machine Diagrams - Overview of Graphical Notation"
[4]: https://link.springer.com/article/10.1007/s00165-010-0161-4 "Soundness of workflow nets: classification, decidability, and analysis | Formal Aspects of Computing | Springer Nature Link"
