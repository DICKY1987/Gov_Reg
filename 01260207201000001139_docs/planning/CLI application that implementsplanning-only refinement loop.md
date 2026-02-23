{
  "plan_metadata": {
    "name": "phase_a_plan_refine_cli",
    "version": "1.0.0",
    "created_at": "2026-02-17T00:00:00-06:00",
    "timezone": "America/Chicago",
    "purpose": "Concrete implementation plan (JSON) for a CLI that executes Phase A (planning-only refinement loop): init → context → skeleton → lint → loop. Produces a deterministic, schema-valid structural plan package via bounded RFC-6902 patch refinement.",
    "executive_summary": {
      "what_this_is": "A machine-usable JSON spec for implementing a Phase A planning-only refinement CLI with deterministic artifact production, hashing/envelopes, linting, and a bounded patch-only refinement loop.",
      "what_a_developer_gets": [
        "Full CLI command/flag contract (init/context/skeleton/lint/loop)",
        "JSON-Schema definitions for all Phase A artifacts and envelopes",
        "Run directory layout, per-step behaviors, validations, LIV checks, hashing rules, and termination logic",
        "Sample artifact instances and patch examples",
        "Unit test checklist and known hazards + mitigations",
        "Schema evolution policy with compatibility matrix + fail-closed rules"
      ],
      "key_design_choices": [
        "Artifact-first: every output is an artifact with a hash + optional ArtifactEnvelope",
        "Fail-closed: missing inputs, hash mismatches, or schema mismatch stop the pipeline",
        "Deterministic hashing using JSON canonicalization (RFC 8785 JCS) + SHA-256",
        "Patch-only refinement: plan changes occur only via RFC 6902 JSON Patch documents"
      ],
      "limitations": "Project repo docs referenced in the request are not accessible via connected sources in this environment; Phase A requirements are implemented as stated in the user-provided specification excerpt plus external primary standards (RFCs / official docs) for patching, canonicalization, schemas, CLI parsing hazards, and shell heredocs."
    },
    "placeholders": {
      "repo_root": "<REPO_ROOT>",
      "runs_dir": ".acms_runs",
      "schemas_dir": "<REPO_ROOT>/schemas",
      "policy_overrides_path": "<OPTIONAL_POLICY_OVERRIDES.json>"
    },
    "run_id": {
      "pattern": "phaseA_{YYYYMMDDTHHMMSSZ}_{uuid4}",
      "generation_rules": [
        "Timestamp MUST be UTC in basic format: YYYYMMDDTHHMMSSZ.",
        "UUID MUST be generated via uuid.uuid4()."
      ],
      "citations": [
        "citeturn1search0"
      ]
    },
    "determinism_contract": {
      "plan_package_must_satisfy": [
        "Schema correctness (plan validates against frozen plan schema snapshot).",
        "No missing required components (hard_defects empty).",
        "No dependency cycles (cycles report empty).",
        "No overlapping write scopes (overlap report empty or explicitly waived by policy).",
        "No nondeterministic instructions / ambiguity remaining in hard-defect class."
      ],
      "notes": [
        "JSON objects are unordered per JSON specification; hashing requires canonicalization for reproducibility."
      ],
      "citations": [
        "citeturn3search0",
        "citeturn1search4"
      ]
    },
    "hashing_rules": {
      "algorithm": "sha256",
      "hash_of": [
        "Canonical JSON bytes for JSON artifacts (RFC 8785 JCS).",
        "Raw bytes for non-JSON artifacts (if any)."
      ],
      "canonicalization": {
        "scheme": "RFC 8785 JCS",
        "requirements": [
          "No whitespace between JSON tokens.",
          "Deterministic property sorting.",
          "No duplicate property names.",
          "Preserve Unicode string data as-is."
        ]
      },
      "citations": [
        "citeturn1search3",
        "citeturn1search4",
        "citeturn3search4"
      ]
    }
  },
  "cli_spec": {
    "binary_name": "plan_refine_cli",
    "cli_style": {
      "subcommands": [
        "init",
        "context",
        "skeleton",
        "lint",
        "loop"
      ],
      "output_format": "JSON artifacts written to run directory; stdout is reserved for human logs unless --json-stdout is set."
    },
    "exit_codes": {
      "0": "Success (PASS or non-loop subcommand completed).",
      "2": "Usage/CLI parsing error (argparse).",
      "10": "Validation error (schema invalid, missing required input, or policy violation).",
      "11": "LIV failure (hash mismatch / provenance mismatch).",
      "12": "Loop termination failure (MAX_ITERATIONS_REACHED or OSCILLATION_DETECTED).",
      "13": "Internal error (unexpected exception)."
    },
    "global_flags": [
      {
        "flag": "--repo-root",
        "short": "-R",
        "type": "path",
        "required": false,
        "default": "<cwd>",
        "argparse_dest": "repo_root",
        "help": "Repository root used for context inventory and relative paths."
      },
      {
        "flag": "--runs-dir",
        "short": null,
        "type": "path",
        "required": false,
        "default": ".acms_runs",
        "argparse_dest": "runs_dir",
        "help": "Directory where run folders are created."
      },
      {
        "flag": "--run-id",
        "short": null,
        "type": "string",
        "required": false,
        "default": "<auto:pattern>",
        "argparse_dest": "run_id",
        "help": "Run identifier. If omitted, generated from pattern in plan_metadata.run_id.pattern."
      },
      {
        "flag": "--strict",
        "short": null,
        "type": "bool",
        "required": false,
        "default": true,
        "argparse_dest": "strict",
        "help": "Fail-closed on any policy/schema/LIV violations."
      },
      {
        "flag": "--json-stdout",
        "short": null,
        "type": "bool",
        "required": false,
        "default": false,
        "argparse_dest": "json_stdout",
        "help": "Emit a small JSON summary of produced artifacts to stdout."
      },
      {
        "flag": "--log-level",
        "short": null,
        "type": "string",
        "required": false,
        "default": "INFO",
        "choices": [
          "DEBUG",
          "INFO",
          "WARN",
          "ERROR"
        ],
        "argparse_dest": "log_level",
        "help": "Logging verbosity."
      }
    ],
    "commands": {
      "init": {
        "summary": "Create planning identity and freeze policy/schema snapshot for the run.",
        "flags": [
          {
            "flag": "--planner-version",
            "short": null,
            "type": "string",
            "required": false,
            "default": "0.0.0",
            "argparse_dest": "planner_version",
            "help": "Planner implementation version string (for reproducibility)."
          },
          {
            "flag": "--policy-version",
            "short": null,
            "type": "string",
            "required": false,
            "default": "0.0.0",
            "argparse_dest": "policy_version",
            "help": "Policy snapshot version string."
          },
          {
            "flag": "--schema-version",
            "short": null,
            "type": "string",
            "required": false,
            "default": "2020-12",
            "argparse_dest": "schema_version",
            "help": "JSON Schema dialect/version for artifact schemas.",
            "citations": [
              "citeturn0search1"
            ]
          },
          {
            "flag": "--max-iters-default",
            "short": null,
            "type": "int",
            "required": false,
            "default": 6,
            "argparse_dest": "max_iters_default",
            "help": "Default max iterations for loop subcommand when --max-iters is omitted."
          },
          {
            "flag": "--out-envelope",
            "short": null,
            "type": "bool",
            "required": false,
            "default": true,
            "argparse_dest": "out_envelope",
            "help": "Also write ArtifactEnvelope files alongside each artifact. NOTE: argparse converts internal '-' to '_' in dest.",
            "citations": [
              "citeturn2search0"
            ]
          }
        ],
        "inputs": [],
        "outputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "planning_run_manifest.envelope.json",
          "planning_policy_snapshot.envelope.json"
        ],
        "behavior": [
          "Generate run_id if not provided.",
          "Create run directory layout (run_layout).",
          "Write planning_run_manifest.json with run identity, policy/schema refs, and placeholders for context refs.",
          "Write planning_policy_snapshot.json with required sections, defect taxonomy, determinism constraints, and loop limits.",
          "Compute sha256 for each artifact (hashing_rules) and write envelopes if enabled."
        ],
        "validations": [
          "Fail if run directory already exists unless --force is added (optional extension).",
          "Policy snapshot MUST be treated immutable after creation."
        ]
      },
      "context": {
        "summary": "Write deterministic context bundle grounded in repo inventory with a signature.",
        "flags": [
          {
            "flag": "--include-globs",
            "short": null,
            "type": "string_list",
            "required": false,
            "default": [
              "**/*.json",
              "**/*.md",
              "**/*.py"
            ],
            "argparse_dest": "include_globs",
            "help": "Glob patterns included in inventory counts/hashes (implementation-defined)."
          },
          {
            "flag": "--exclude-globs",
            "short": null,
            "type": "string_list",
            "required": false,
            "default": [
              ".git/**",
              ".acms_runs/**",
              "node_modules/**",
              "dist/**",
              "build/**"
            ],
            "argparse_dest": "exclude_globs",
            "help": "Glob patterns excluded from inventory counts/hashes."
          },
          {
            "flag": "--git",
            "short": null,
            "type": "bool",
            "required": false,
            "default": true,
            "argparse_dest": "git",
            "help": "If true, include git commit SHA and dirty status in signature when repo is git-backed."
          }
        ],
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json"
        ],
        "outputs": [
          "context_bundle.json",
          "context_bundle_signature.json",
          "context_bundle.envelope.json",
          "context_bundle_signature.envelope.json",
          "planning_run_manifest.json (updated: context refs only)"
        ],
        "behavior": [
          "Load and LIV-verify planning_run_manifest.json and planning_policy_snapshot.json.",
          "Inventory repo: summary, relevant directories, discovered templates/workstreams/gates/registries (implementation-defined, but deterministic by ordered traversal).",
          "Write context_bundle.json with inventory results and references.",
          "Write context_bundle_signature.json with commit_sha (if available), file_count, root_tree_hash (or manifest hash), and generated_at.",
          "Update planning_run_manifest.json to include context_bundle and signature references only; preserve prior manifest as planning_run_manifest.prev_{timestamp}.json."
        ],
        "validations": [
          "Inventory traversal order MUST be deterministic (e.g., sorted paths).",
          "If git flag is true and git is available, commit_sha MUST be populated; else set git_available=false."
        ]
      },
      "skeleton": {
        "summary": "Generate structural plan skeleton with all required sections present; validate against plan schema snapshot.",
        "flags": [
          {
            "flag": "--feature-id",
            "short": null,
            "type": "string",
            "required": true,
            "default": null,
            "argparse_dest": "feature_id",
            "help": "Stable identifier for the planned feature/change."
          },
          {
            "flag": "--objective",
            "short": null,
            "type": "string",
            "required": true,
            "default": null,
            "argparse_dest": "objective",
            "help": "Primary objective for the plan."
          },
          {
            "flag": "--allow-tbd",
            "short": null,
            "type": "bool",
            "required": false,
            "default": true,
            "argparse_dest": "allow_tbd",
            "help": "If true, required sections may have placeholder values (e.g., \"TBD\")."
          },
          {
            "flag": "--plan-schema-id",
            "short": null,
            "type": "string",
            "required": false,
            "default": "urn:phaseA:plan_skeleton:v1",
            "argparse_dest": "plan_schema_id",
            "help": "Plan schema ID to validate against."
          }
        ],
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "context_bundle.json",
          "context_bundle_signature.json"
        ],
        "outputs": [
          "plan_skeleton.json",
          "plan_skeleton_schema_validation.json",
          "plan_skeleton.envelope.json",
          "plan_skeleton_schema_validation.envelope.json"
        ],
        "behavior": [
          "LIV verify all inputs.",
          "Generate a minimal plan object including ALL required sections (even if TBD).",
          "Persist plan_skeleton.json under run artifacts path.",
          "Validate plan against internal plan schema snapshot; write plan_skeleton_schema_validation.json with valid/errors.",
          "Envelope + hash outputs."
        ],
        "validations": [
          "If allow_tbd=false, fail if any required field is 'TBD' or null.",
          "Schema validation MUST run and its result artifact MUST be emitted even on failure."
        ]
      },
      "lint": {
        "summary": "Analyze plan for schema validity, determinism defects, dependency cycles, and scope overlaps. Does not modify plan.",
        "flags": [
          {
            "flag": "--plan-path",
            "short": null,
            "type": "path",
            "required": false,
            "default": "<run>/artifacts/phase/PHASE_A/skeleton/plan_skeleton.json",
            "argparse_dest": "plan_path",
            "help": "Explicit plan JSON path to lint; defaults to plan_skeleton.json."
          },
          {
            "flag": "--fail-on-soft",
            "short": null,
            "type": "bool",
            "required": false,
            "default": false,
            "argparse_dest": "fail_on_soft",
            "help": "If true, treat soft defects as hard for gating."
          }
        ],
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "context_bundle.json",
          "context_bundle_signature.json",
          "<plan_path>"
        ],
        "outputs": [
          "plan_lint_report.json",
          "plan_dependency_graph.json",
          "plan_cycles_report.json",
          "plan_scope_overlap_report.json",
          "plan_lint_report.envelope.json",
          "plan_dependency_graph.envelope.json",
          "plan_cycles_report.envelope.json",
          "plan_scope_overlap_report.envelope.json"
        ],
        "behavior": [
          "LIV verify stable inputs and plan.",
          "Schema validate plan: if invalid, record INVALID_SCHEMA as hard defect.",
          "Build dependency graph from plan workstreams/tasks dependencies.",
          "Detect cycles from graph; emit plan_cycles_report.json; record DEPENDENCY_CYCLE as hard defect if any cycle found.",
          "Analyze write scopes per workstream/task; detect overlaps; emit plan_scope_overlap_report.json; record SCOPE_OVERLAP as hard defect unless waived.",
          "Analyze determinism: missing components, missing acceptance tests, ambiguous scopes or ambiguous instructions; emit plan_lint_report.json."
        ],
        "validations": [
          "Lint MUST NOT mutate plan.",
          "All lint companion artifacts MUST be emitted even when defects exist."
        ]
      },
      "loop": {
        "summary": "Bounded patch-only refinement loop: lint → patch → apply → validate → re-lint until PASS or termination.",
        "flags": [
          {
            "flag": "--max-iters",
            "short": null,
            "type": "int",
            "required": false,
            "default": "<from policy snapshot or init default>",
            "argparse_dest": "max_iters",
            "help": "Maximum refinement loop iterations."
          },
          {
            "flag": "--plan-path",
            "short": null,
            "type": "path",
            "required": false,
            "default": "<run>/artifacts/phase/PHASE_A/skeleton/plan_skeleton.json",
            "argparse_dest": "plan_path",
            "help": "Initial plan path to refine."
          },
          {
            "flag": "--planner-mode",
            "short": null,
            "type": "string",
            "required": false,
            "default": "manual",
            "choices": [
              "manual",
              "rule_based",
              "llm"
            ],
            "argparse_dest": "planner_mode",
            "help": "Patch generation mode. 'manual' expects --patch-in each iter; other modes generate patch deterministically per implementation."
          },
          {
            "flag": "--patch-in",
            "short": null,
            "type": "path",
            "required": false,
            "default": null,
            "argparse_dest": "patch_in",
            "help": "When planner-mode=manual, read RFC-6902 patch from this file for the current iteration."
          },
          {
            "flag": "--oscillation-window",
            "short": null,
            "type": "int",
            "required": false,
            "default": 3,
            "argparse_dest": "oscillation_window",
            "help": "Detect repeated defect fingerprints within this window and terminate with OSCILLATION_DETECTED."
          }
        ],
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "context_bundle.json",
          "context_bundle_signature.json",
          "<plan_path>"
        ],
        "outputs": [
          "refinement_round_{n}.json",
          "plan_delta_patch_{n}.json",
          "refined_plan_{n}.json",
          "refinement_termination_record.json"
        ],
        "behavior": [
          "LIV verify all stable inputs once at loop start; verify plan each iteration.",
          "For n in 1..max_iters: run lint on current plan to produce defects and companion artifacts.",
          "If no hard defects: emit refinement_termination_record.json with reason=NO_HARD_DEFECTS; exit 0.",
          "Else obtain patch (manual: read --patch-in; other: generate).",
          "Validate patch against RFC-6902 schema; apply patch to current plan using JSON Pointer paths (RFC 6901).",
          "Schema-validate patched plan; if invalid, record hard defect PATCH_RESULT_INVALID_SCHEMA and continue (or fail immediately if policy says so).",
          "Write refined_plan_{n}.json and refinement_round_{n}.json recording hashes and inputs/outputs.",
          "Detect oscillation: if hard-defect fingerprint repeats within oscillation_window, terminate with OSCILLATION_DETECTED.",
          "If max_iters reached with remaining hard defects: terminate with MAX_ITERATIONS_REACHED."
        ],
        "validations": [
          "Only RFC-6902 patches are permitted plan mutations in loop.",
          "Each iteration MUST write: patch file, round record, refined plan, and updated lint artifacts.",
          "Termination record MUST always be emitted (PASS or FAIL)."
        ],
        "citations": [
          "citeturn0search4",
          "citeturn3search3"
        ]
      }
    },
    "tables": {
      "cli_commands_table": [
        {
          "command": "init",
          "produces": "manifest + policy snapshot",
          "inputs": "none",
          "primary_gate": "run dir created; snapshots written"
        },
        {
          "command": "context",
          "produces": "context bundle + signature",
          "inputs": "manifest + policy snapshot",
          "primary_gate": "signature computed; manifest updated (context refs only)"
        },
        {
          "command": "skeleton",
          "produces": "plan skeleton + schema validation",
          "inputs": "manifest + policy + context + signature",
          "primary_gate": "schema validation valid=true"
        },
        {
          "command": "lint",
          "produces": "lint + graph + cycles + overlap",
          "inputs": "plan + stable inputs",
          "primary_gate": "artifacts emitted; hard defects computed"
        },
        {
          "command": "loop",
          "produces": "per-round patch + records + termination",
          "inputs": "plan + stable inputs",
          "primary_gate": "PASS or termination (max iters/oscillation)"
        }
      ]
    },
    "argparse_hazards_note": {
      "statement": "Argparse converts internal '-' in long option names to '_' in Namespace attributes unless dest is set explicitly. This is a known source of bugs (e.g., --out-envelope becomes args.out_envelope).",
      "citations": [
        "citeturn2search0"
      ]
    }
  },
  "artifact_schemas": {
    "schema_dialect": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "version": "2020-12",
      "citations": [
        "citeturn0search0",
        "citeturn0search1"
      ]
    },
    "$defs": {
      "ISODateTime": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
      },
      "Sha256Hex": {
        "type": "string",
        "pattern": "^[a-f0-9]{64}$"
      },
      "JsonPointer": {
        "type": "string",
        "description": "JSON Pointer string per RFC 6901.",
        "pattern": "^(\\/([^~]|~0|~1)*)*$",
        "citations": [
          "citeturn3search3"
        ]
      },
      "ArtifactRef": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "path",
          "sha256"
        ],
        "properties": {
          "path": {
            "type": "string"
          },
          "sha256": {
            "$ref": "#/$defs/Sha256Hex"
          },
          "schema_id": {
            "type": [
              "string",
              "null"
            ]
          },
          "content_type": {
            "type": [
              "string",
              "null"
            ]
          }
        }
      },
      "Defect": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "code",
          "severity",
          "message"
        ],
        "properties": {
          "code": {
            "type": "string",
            "enum": [
              "MISSING_COMPONENT",
              "INVALID_SCHEMA",
              "NO_ACCEPTANCE_TESTS",
              "SCOPE_AMBIGUOUS",
              "NON_DETERMINISTIC_INSTRUCTIONS",
              "DEPENDENCY_CYCLE",
              "SCOPE_OVERLAP",
              "PATCH_APPLY_FAILED",
              "PATCH_RESULT_INVALID_SCHEMA",
              "UNRESOLVED_TBD"
            ]
          },
          "severity": {
            "type": "string",
            "enum": [
              "hard",
              "soft"
            ]
          },
          "message": {
            "type": "string"
          },
          "location": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "json_pointer": {
                "$ref": "#/$defs/JsonPointer"
              },
              "artifact_path": {
                "type": "string"
              }
            }
          },
          "evidence": {
            "type": "object"
          },
          "remediation_hint": {
            "type": [
              "string",
              "null"
            ]
          }
        }
      }
    },
    "artifacts": {
      "planning_run_manifest.json": {
        "schema_id": "urn:phaseA:planning_run_manifest:v1",
        "content_type": "application/json",
        "produced_by": "init (A1) and context (A2; limited updates)",
        "consumed_by": "context/skeleton/lint/loop",
        "purpose": "Run identity + frozen version refs + context refs (whitelisted updates).",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:planning_run_manifest:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "run_id",
            "repo_root",
            "runs_dir",
            "created_at",
            "planner_version",
            "policy_version",
            "schema_version"
          ],
          "properties": {
            "run_id": {
              "type": "string",
              "minLength": 1
            },
            "repo_root": {
              "type": "string",
              "minLength": 1
            },
            "runs_dir": {
              "type": "string",
              "minLength": 1
            },
            "created_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "planner_version": {
              "type": "string"
            },
            "policy_version": {
              "type": "string"
            },
            "schema_version": {
              "type": "string"
            },
            "policy_snapshot": {
              "description": "Reference to the frozen planning_policy_snapshot.json artifact.",
              "$ref": "#/$defs/ArtifactRef"
            },
            "context_bundle": {
              "description": "Reference to context_bundle.json. May be null immediately after init.",
              "anyOf": [
                {
                  "$ref": "#/$defs/ArtifactRef"
                },
                {
                  "type": "null"
                }
              ]
            },
            "context_bundle_signature": {
              "description": "Reference to context_bundle_signature.json. May be null immediately after init.",
              "anyOf": [
                {
                  "$ref": "#/$defs/ArtifactRef"
                },
                {
                  "type": "null"
                }
              ]
            },
            "context_hash": {
              "description": "Optional convenience hash, typically equals context_bundle_signature.sha256 or context_bundle.sha256 (project-defined).",
              "anyOf": [
                {
                  "$ref": "#/$defs/Sha256Hex"
                },
                {
                  "type": "null"
                }
              ]
            },
            "plan_schema": {
              "description": "Identifier used to validate plan artifacts (plan_skeleton.json and refined_plan_n.json).",
              "type": [
                "string",
                "null"
              ]
            },
            "notes": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "planning_policy_snapshot.json": {
        "schema_id": "urn:phaseA:planning_policy_snapshot:v1",
        "content_type": "application/json",
        "produced_by": "init (A1)",
        "consumed_by": "context/skeleton/lint/loop",
        "purpose": "Frozen policy snapshot: required sections, defect taxonomy, determinism constraints, loop limits, schema registry.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:planning_policy_snapshot:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "policy_id",
            "policy_version",
            "created_at",
            "required_plan_sections",
            "defect_taxonomy",
            "loop_limits",
            "determinism_constraints",
            "gating_rules",
            "schema_registry"
          ],
          "properties": {
            "policy_id": {
              "type": "string",
              "minLength": 1
            },
            "policy_version": {
              "type": "string"
            },
            "created_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "required_plan_sections": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string"
              },
              "description": "List of required top-level keys that MUST exist in plan_skeleton.json (may be 'TBD' if allowed)."
            },
            "defect_taxonomy": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "code",
                  "default_severity",
                  "description",
                  "classification"
                ],
                "properties": {
                  "code": {
                    "type": "string"
                  },
                  "default_severity": {
                    "type": "string",
                    "enum": [
                      "hard",
                      "soft"
                    ]
                  },
                  "classification": {
                    "type": "string",
                    "enum": [
                      "schema",
                      "completeness",
                      "determinism",
                      "dependency",
                      "scope",
                      "process"
                    ]
                  },
                  "description": {
                    "type": "string"
                  },
                  "example_locations": {
                    "type": "array",
                    "items": {
                      "$ref": "#/$defs/JsonPointer"
                    }
                  }
                }
              }
            },
            "loop_limits": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "max_iterations",
                "oscillation_repeat_limit"
              ],
              "properties": {
                "max_iterations": {
                  "type": "integer",
                  "minimum": 1,
                  "maximum": 50
                },
                "oscillation_repeat_limit": {
                  "type": "integer",
                  "minimum": 1,
                  "maximum": 20
                },
                "max_patch_ops": {
                  "type": "integer",
                  "minimum": 1,
                  "maximum": 1000
                }
              }
            },
            "determinism_constraints": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "no_dependency_cycles",
                "no_scope_overlaps",
                "no_ambiguous_instructions"
              ],
              "properties": {
                "no_dependency_cycles": {
                  "type": "boolean"
                },
                "no_scope_overlaps": {
                  "type": "boolean"
                },
                "no_ambiguous_instructions": {
                  "type": "boolean"
                },
                "require_acceptance_tests": {
                  "type": "boolean"
                },
                "allow_tbd_placeholders": {
                  "type": "boolean"
                }
              }
            },
            "gating_rules": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "pass_condition",
                "fail_closed"
              ],
              "properties": {
                "pass_condition": {
                  "type": "string",
                  "enum": [
                    "NO_HARD_DEFECTS"
                  ]
                },
                "fail_closed": {
                  "type": "boolean"
                },
                "treat_soft_defects_as_hard": {
                  "type": "boolean"
                },
                "scope_overlap_waiver_policy": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "allowed",
                    "requires_justification"
                  ],
                  "properties": {
                    "allowed": {
                      "type": "boolean"
                    },
                    "requires_justification": {
                      "type": "boolean"
                    },
                    "waiver_format": {
                      "type": "string"
                    }
                  }
                }
              }
            },
            "schema_registry": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "artifact_schemas",
                "plan_schema"
              ],
              "properties": {
                "artifact_schemas": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "schema_id",
                      "artifact",
                      "version",
                      "compatibility_family"
                    ],
                    "properties": {
                      "schema_id": {
                        "type": "string"
                      },
                      "artifact": {
                        "type": "string"
                      },
                      "version": {
                        "type": "string"
                      },
                      "compatibility_family": {
                        "type": "string"
                      }
                    }
                  }
                },
                "plan_schema": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "schema_id",
                    "version",
                    "compatibility_family"
                  ],
                  "properties": {
                    "schema_id": {
                      "type": "string"
                    },
                    "version": {
                      "type": "string"
                    },
                    "compatibility_family": {
                      "type": "string"
                    }
                  }
                }
              }
            },
            "notes": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "context_bundle.json": {
        "schema_id": "urn:phaseA:context_bundle:v1",
        "content_type": "application/json",
        "produced_by": "context (A2)",
        "consumed_by": "skeleton/lint/loop",
        "purpose": "Inventory-first context grounding: repo summary, templates/workstreams/gates/registries, key paths and optional recent changes.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:context_bundle:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "repo_root",
            "repo_summary",
            "inventory",
            "paths"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "repo_root": {
              "type": "string"
            },
            "repo_summary": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "name",
                "description"
              ],
              "properties": {
                "name": {
                  "type": "string"
                },
                "description": {
                  "type": "string"
                },
                "language_stack": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              }
            },
            "inventory": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "templates",
                "workstreams",
                "gates",
                "registries"
              ],
              "properties": {
                "templates": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "workstreams": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "gates": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "registries": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              }
            },
            "paths": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "templates_roots",
                "workstreams_roots",
                "gates_roots",
                "registry_roots"
              ],
              "properties": {
                "templates_roots": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "workstreams_roots": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "gates_roots": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "registry_roots": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              }
            },
            "recent_changes": {
              "type": "array",
              "description": "Optional list of recent commits or change summaries (implementation-defined).",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "summary"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "summary": {
                    "type": "string"
                  },
                  "timestamp": {
                    "anyOf": [
                      {
                        "$ref": "#/$defs/ISODateTime"
                      },
                      {
                        "type": "null"
                      }
                    ]
                  }
                }
              }
            },
            "notes": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "context_bundle_signature.json": {
        "schema_id": "urn:phaseA:context_bundle_signature:v1",
        "content_type": "application/json",
        "produced_by": "context (A2)",
        "consumed_by": "skeleton/lint/loop",
        "purpose": "Deterministic context signature: commit SHA + tree hash + file count + include/exclude globs + context bundle hash.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:context_bundle_signature:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "repo_root",
            "git_available",
            "commit_sha",
            "dirty",
            "file_count",
            "root_tree_hash",
            "context_bundle_sha256"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "repo_root": {
              "type": "string"
            },
            "git_available": {
              "type": "boolean"
            },
            "commit_sha": {
              "type": [
                "string",
                "null"
              ],
              "description": "If git_available=true, MUST be non-null."
            },
            "dirty": {
              "type": [
                "boolean",
                "null"
              ],
              "description": "If git_available=true, indicates if working tree has uncommitted changes."
            },
            "file_count": {
              "type": "integer",
              "minimum": 0
            },
            "root_tree_hash": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "include_globs": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "exclude_globs": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "context_bundle_sha256": {
              "$ref": "#/$defs/Sha256Hex"
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_skeleton.json": {
        "schema_id": "urn:phaseA:plan_skeleton:v1",
        "content_type": "application/json",
        "produced_by": "skeleton (A3) and loop (A5; refined_plan_n derivations)",
        "consumed_by": "lint/loop",
        "purpose": "Structurally complete plan object with required sections present; basis for lint and patch-only refinement.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_skeleton:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "feature_id",
            "objective",
            "constraints",
            "workstreams",
            "global_requirements",
            "risks",
            "deferred_items"
          ],
          "properties": {
            "feature_id": {
              "type": "string",
              "minLength": 1
            },
            "objective": {
              "type": "string",
              "minLength": 1
            },
            "constraints": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "Hard constraints the plan must respect (e.g., compatibility, performance budgets, policy constraints)."
            },
            "global_requirements": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "requirement",
                  "acceptance_criteria"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "requirement": {
                    "type": "string"
                  },
                  "acceptance_criteria": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                }
              }
            },
            "workstreams": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "summary",
                  "writes_scopes",
                  "depends_on",
                  "acceptance_tests"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "summary": {
                    "type": "string"
                  },
                  "writes_scopes": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "Explicit write scope declarations (paths/globs) to support overlap detection."
                  },
                  "depends_on": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "acceptance_tests": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "Measurable checks that must pass for this workstream."
                  },
                  "tasks": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "id",
                        "summary",
                        "writes_scopes",
                        "depends_on",
                        "acceptance_tests"
                      ],
                      "properties": {
                        "id": {
                          "type": "string"
                        },
                        "summary": {
                          "type": "string"
                        },
                        "writes_scopes": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          }
                        },
                        "depends_on": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          }
                        },
                        "acceptance_tests": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "risks": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "risk",
                  "mitigation"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "risk": {
                    "type": "string"
                  },
                  "mitigation": {
                    "type": "string"
                  },
                  "severity": {
                    "type": "string",
                    "enum": [
                      "low",
                      "medium",
                      "high"
                    ],
                    "default": "medium"
                  }
                }
              }
            },
            "deferred_items": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "Explicitly out-of-scope or deferred items."
            },
            "metadata": {
              "type": "object",
              "additionalProperties": true,
              "properties": {
                "created_at": {
                  "$ref": "#/$defs/ISODateTime"
                },
                "schema_id": {
                  "type": "string"
                },
                "schema_version": {
                  "type": "string"
                },
                "context_signature_sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_skeleton_schema_validation.json": {
        "schema_id": "urn:phaseA:plan_schema_validation:v1",
        "content_type": "application/json",
        "produced_by": "skeleton (A3) and loop (A5; after patch apply)",
        "consumed_by": "lint/loop (as evidence)",
        "purpose": "Evidence artifact proving the plan validates (or not) against a frozen schema snapshot.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_schema_validation:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "plan_sha256",
            "schema_id",
            "schema_version",
            "valid",
            "errors"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "plan_sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "schema_id": {
              "type": "string"
            },
            "schema_version": {
              "type": "string"
            },
            "valid": {
              "type": "boolean"
            },
            "errors": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": true,
                "properties": {
                  "path": {
                    "$ref": "#/$defs/JsonPointer"
                  },
                  "message": {
                    "type": "string"
                  }
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_lint_report.json": {
        "schema_id": "urn:phaseA:plan_lint_report:v1",
        "content_type": "application/json",
        "produced_by": "lint (A4) and loop (A5 each iteration)",
        "consumed_by": "loop (A5)",
        "purpose": "Critic output: structured hard/soft defects; includes pointers and evidence references. Does not modify plan.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_lint_report:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "plan_sha256",
            "hard_defects",
            "soft_defects",
            "summary"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "plan_sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "policy_snapshot_sha256": {
              "anyOf": [
                {
                  "$ref": "#/$defs/Sha256Hex"
                },
                {
                  "type": "null"
                }
              ]
            },
            "hard_defects": {
              "type": "array",
              "items": {
                "$ref": "#/$defs/Defect"
              }
            },
            "soft_defects": {
              "type": "array",
              "items": {
                "$ref": "#/$defs/Defect"
              }
            },
            "summary": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "hard_count",
                "soft_count",
                "defect_codes"
              ],
              "properties": {
                "hard_count": {
                  "type": "integer",
                  "minimum": 0
                },
                "soft_count": {
                  "type": "integer",
                  "minimum": 0
                },
                "defect_codes": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              }
            },
            "analysis_metadata": {
              "type": "object",
              "additionalProperties": true,
              "properties": {
                "dependency_graph_sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "cycles_report_sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "scope_overlap_report_sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_dependency_graph.json": {
        "schema_id": "urn:phaseA:plan_dependency_graph:v1",
        "content_type": "application/json",
        "produced_by": "lint (A4) and loop (A5 each iteration)",
        "consumed_by": "lint/loop (cycle detection and evidence)",
        "purpose": "Dependency representation of plan nodes to support cycle detection and gating.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_dependency_graph:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "plan_sha256",
            "nodes",
            "edges"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "plan_sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "nodes": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "kind"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "kind": {
                    "type": "string",
                    "enum": [
                      "workstream",
                      "task"
                    ]
                  },
                  "writes_scopes": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "acceptance_tests": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                }
              }
            },
            "edges": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "from",
                  "to",
                  "type"
                ],
                "properties": {
                  "from": {
                    "type": "string"
                  },
                  "to": {
                    "type": "string"
                  },
                  "type": {
                    "type": "string",
                    "enum": [
                      "depends_on"
                    ]
                  }
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_cycles_report.json": {
        "schema_id": "urn:phaseA:plan_cycles_report:v1",
        "content_type": "application/json",
        "produced_by": "lint (A4) and loop (A5 each iteration)",
        "consumed_by": "loop (A5 gating)",
        "purpose": "Cycle detection evidence; cycles must be empty for PASS if policy.no_dependency_cycles=true.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_cycles_report:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "plan_sha256",
            "cycle_count",
            "cycles"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "plan_sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "cycle_count": {
              "type": "integer",
              "minimum": 0
            },
            "cycles": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "nodes"
                ],
                "properties": {
                  "nodes": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                      "type": "string"
                    }
                  },
                  "explanation": {
                    "type": [
                      "string",
                      "null"
                    ]
                  }
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_scope_overlap_report.json": {
        "schema_id": "urn:phaseA:plan_scope_overlap_report:v1",
        "content_type": "application/json",
        "produced_by": "lint (A4) and loop (A5 each iteration)",
        "consumed_by": "loop (A5 gating)",
        "purpose": "Overlapping write scopes evidence; overlaps must be empty or waived for PASS per policy.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_scope_overlap_report:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "plan_sha256",
            "overlap_count",
            "overlaps"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "plan_sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "overlap_count": {
              "type": "integer",
              "minimum": 0
            },
            "overlaps": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "scope",
                  "writers",
                  "normalized_scope"
                ],
                "properties": {
                  "scope": {
                    "type": "string",
                    "description": "Original scope declaration (path/glob)."
                  },
                  "normalized_scope": {
                    "type": "string",
                    "description": "Canonicalized scope used for comparisons."
                  },
                  "writers": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                      "type": "string"
                    }
                  },
                  "risk": {
                    "type": "string",
                    "enum": [
                      "nondeterminism",
                      "merge_conflict",
                      "unknown"
                    ],
                    "default": "nondeterminism"
                  },
                  "waived": {
                    "type": "boolean",
                    "default": false,
                    "description": "True if overlap is explicitly waived by policy and justification is recorded."
                  },
                  "waiver_justification": {
                    "type": [
                      "string",
                      "null"
                    ]
                  }
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "refinement_round_{n}.json": {
        "schema_id": "urn:phaseA:refinement_round:v1",
        "content_type": "application/json",
        "produced_by": "loop (A5 per iter)",
        "consumed_by": "audit/replay tooling",
        "purpose": "Per-iteration record: input hashes, defect fingerprint, patch hash, output hash, and termination checkpoint metadata.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:refinement_round:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "round",
            "generated_at",
            "input_plan",
            "lint_report",
            "patch",
            "output_plan",
            "termination_checkpoint"
          ],
          "properties": {
            "round": {
              "type": "integer",
              "minimum": 1
            },
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "input_plan": {
              "$ref": "#/$defs/ArtifactRef"
            },
            "lint_report": {
              "$ref": "#/$defs/ArtifactRef"
            },
            "patch": {
              "$ref": "#/$defs/ArtifactRef"
            },
            "output_plan": {
              "$ref": "#/$defs/ArtifactRef"
            },
            "hard_defect_fingerprint": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "termination_checkpoint": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "pass_condition_met",
                "hard_defects_remaining"
              ],
              "properties": {
                "pass_condition_met": {
                  "type": "boolean"
                },
                "hard_defects_remaining": {
                  "type": "integer",
                  "minimum": 0
                },
                "termination_reason_if_any": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "notes": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_delta_patch_{n}.json": {
        "schema_id": "urn:phaseA:json_patch_rfc6902:v1",
        "content_type": "application/json-patch+json",
        "produced_by": "loop (A5 per iter; planner output)",
        "consumed_by": "loop (A5 patch apply)",
        "purpose": "RFC-6902 JSON Patch operations applied to plan. This is the only permitted mutation mechanism for plan refinement.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:json_patch_rfc6902:v1",
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "op",
              "path"
            ],
            "properties": {
              "op": {
                "type": "string",
                "enum": [
                  "add",
                  "remove",
                  "replace",
                  "move",
                  "copy",
                  "test"
                ]
              },
              "path": {
                "$ref": "#/$defs/JsonPointer"
              },
              "from": {
                "$ref": "#/$defs/JsonPointer"
              },
              "value": {}
            },
            "allOf": [
              {
                "if": {
                  "properties": {
                    "op": {
                      "const": "add"
                    }
                  }
                },
                "then": {
                  "required": [
                    "value"
                  ]
                }
              },
              {
                "if": {
                  "properties": {
                    "op": {
                      "const": "replace"
                    }
                  }
                },
                "then": {
                  "required": [
                    "value"
                  ]
                }
              },
              {
                "if": {
                  "properties": {
                    "op": {
                      "const": "test"
                    }
                  }
                },
                "then": {
                  "required": [
                    "value"
                  ]
                }
              },
              {
                "if": {
                  "properties": {
                    "op": {
                      "enum": [
                        "move",
                        "copy"
                      ]
                    }
                  }
                },
                "then": {
                  "required": [
                    "from"
                  ]
                }
              }
            ]
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "refinement_termination_record.json": {
        "schema_id": "urn:phaseA:refinement_termination_record:v1",
        "content_type": "application/json",
        "produced_by": "loop (A5)",
        "consumed_by": "downstream phases / audit tooling",
        "purpose": "Single authoritative termination artifact recording PASS/FAIL reason and pointers to final plan and lint report.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:refinement_termination_record:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "generated_at",
            "reason",
            "iterations",
            "max_allowed",
            "final_plan",
            "final_lint_report"
          ],
          "properties": {
            "generated_at": {
              "$ref": "#/$defs/ISODateTime"
            },
            "reason": {
              "type": "string",
              "enum": [
                "NO_HARD_DEFECTS",
                "MAX_ITERATIONS_REACHED",
                "OSCILLATION_DETECTED"
              ]
            },
            "iterations": {
              "type": "integer",
              "minimum": 0
            },
            "max_allowed": {
              "type": "integer",
              "minimum": 1
            },
            "final_plan": {
              "$ref": "#/$defs/ArtifactRef"
            },
            "final_lint_report": {
              "$ref": "#/$defs/ArtifactRef"
            },
            "oscillation_details": {
              "type": [
                "object",
                "null"
              ],
              "additionalProperties": false,
              "properties": {
                "window": {
                  "type": "integer",
                  "minimum": 1
                },
                "repeated_fingerprint": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "occurrences": {
                  "type": "integer",
                  "minimum": 2
                }
              }
            },
            "notes": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      },
      "plan_delta_request.json": {
        "schema_id": "urn:phaseA:plan_delta_request:v1",
        "content_type": "application/json",
        "produced_by": "loop (optional; expansion admission)",
        "consumed_by": "loop (admission gate) / planner",
        "purpose": "Structured request to add new plan nodes/scope during refinement; must be admitted only if it does not violate determinism constraints.",
        "schema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "urn:phaseA:plan_delta_request:v1",
          "type": "object",
          "additionalProperties": false,
          "required": [
            "source_workstream",
            "reason",
            "evidence",
            "proposed_new_nodes",
            "blocking"
          ],
          "properties": {
            "source_workstream": {
              "type": "string"
            },
            "reason": {
              "type": "string"
            },
            "evidence": {
              "type": "string"
            },
            "blocking": {
              "type": "boolean"
            },
            "proposed_new_nodes": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "kind",
                  "summary",
                  "writes_scopes",
                  "depends_on",
                  "acceptance_tests"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "kind": {
                    "type": "string",
                    "enum": [
                      "workstream",
                      "task"
                    ]
                  },
                  "summary": {
                    "type": "string"
                  },
                  "writes_scopes": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "depends_on": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "acceptance_tests": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          },
          "$defs": {
            "ISODateTime": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
            },
            "Sha256Hex": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$"
            },
            "JsonPointer": {
              "type": "string",
              "description": "JSON Pointer string per RFC 6901.",
              "pattern": "^(\\/([^~]|~0|~1)*)*$"
            },
            "ArtifactRef": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "sha256"
              ],
              "properties": {
                "path": {
                  "type": "string"
                },
                "sha256": {
                  "$ref": "#/$defs/Sha256Hex"
                },
                "schema_id": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "content_type": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "Defect": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "code",
                "severity",
                "message"
              ],
              "properties": {
                "code": {
                  "type": "string",
                  "enum": [
                    "MISSING_COMPONENT",
                    "INVALID_SCHEMA",
                    "NO_ACCEPTANCE_TESTS",
                    "SCOPE_AMBIGUOUS",
                    "NON_DETERMINISTIC_INSTRUCTIONS",
                    "DEPENDENCY_CYCLE",
                    "SCOPE_OVERLAP",
                    "PATCH_APPLY_FAILED",
                    "PATCH_RESULT_INVALID_SCHEMA",
                    "UNRESOLVED_TBD"
                  ]
                },
                "severity": {
                  "type": "string",
                  "enum": [
                    "hard",
                    "soft"
                  ]
                },
                "message": {
                  "type": "string"
                },
                "location": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "json_pointer": {
                      "$ref": "#/$defs/JsonPointer"
                    },
                    "artifact_path": {
                      "type": "string"
                    }
                  }
                },
                "evidence": {
                  "type": "object"
                },
                "remediation_hint": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            }
          }
        }
      }
    },
    "tables": {
      "artifact_schemas_table": [
        {
          "artifact": "planning_run_manifest.json",
          "schema_id": "urn:phaseA:planning_run_manifest:v1",
          "produced_by": "init (A1) and context (A2; limited updates)",
          "consumed_by": "context/skeleton/lint/loop",
          "purpose": "Run identity + frozen version refs + context refs (whitelisted updates)."
        },
        {
          "artifact": "planning_policy_snapshot.json",
          "schema_id": "urn:phaseA:planning_policy_snapshot:v1",
          "produced_by": "init (A1)",
          "consumed_by": "context/skeleton/lint/loop",
          "purpose": "Frozen policy snapshot: required sections, defect taxonomy, determinism constraints, loop limits, schema registry."
        },
        {
          "artifact": "context_bundle.json",
          "schema_id": "urn:phaseA:context_bundle:v1",
          "produced_by": "context (A2)",
          "consumed_by": "skeleton/lint/loop",
          "purpose": "Inventory-first context grounding: repo summary, templates/workstreams/gates/registries, key paths and optional recent changes."
        },
        {
          "artifact": "context_bundle_signature.json",
          "schema_id": "urn:phaseA:context_bundle_signature:v1",
          "produced_by": "context (A2)",
          "consumed_by": "skeleton/lint/loop",
          "purpose": "Deterministic context signature: commit SHA + tree hash + file count + include/exclude globs + context bundle hash."
        },
        {
          "artifact": "plan_skeleton.json",
          "schema_id": "urn:phaseA:plan_skeleton:v1",
          "produced_by": "skeleton (A3) and loop (A5; refined_plan_n derivations)",
          "consumed_by": "lint/loop",
          "purpose": "Structurally complete plan object with required sections present; basis for lint and patch-only refinement."
        },
        {
          "artifact": "plan_skeleton_schema_validation.json",
          "schema_id": "urn:phaseA:plan_schema_validation:v1",
          "produced_by": "skeleton (A3) and loop (A5; after patch apply)",
          "consumed_by": "lint/loop (as evidence)",
          "purpose": "Evidence artifact proving the plan validates (or not) against a frozen schema snapshot."
        },
        {
          "artifact": "plan_lint_report.json",
          "schema_id": "urn:phaseA:plan_lint_report:v1",
          "produced_by": "lint (A4) and loop (A5 each iteration)",
          "consumed_by": "loop (A5)",
          "purpose": "Critic output: structured hard/soft defects; includes pointers and evidence references. Does not modify plan."
        },
        {
          "artifact": "plan_dependency_graph.json",
          "schema_id": "urn:phaseA:plan_dependency_graph:v1",
          "produced_by": "lint (A4) and loop (A5 each iteration)",
          "consumed_by": "lint/loop (cycle detection and evidence)",
          "purpose": "Dependency representation of plan nodes to support cycle detection and gating."
        },
        {
          "artifact": "plan_cycles_report.json",
          "schema_id": "urn:phaseA:plan_cycles_report:v1",
          "produced_by": "lint (A4) and loop (A5 each iteration)",
          "consumed_by": "loop (A5 gating)",
          "purpose": "Cycle detection evidence; cycles must be empty for PASS if policy.no_dependency_cycles=true."
        },
        {
          "artifact": "plan_scope_overlap_report.json",
          "schema_id": "urn:phaseA:plan_scope_overlap_report:v1",
          "produced_by": "lint (A4) and loop (A5 each iteration)",
          "consumed_by": "loop (A5 gating)",
          "purpose": "Overlapping write scopes evidence; overlaps must be empty or waived for PASS per policy."
        },
        {
          "artifact": "refinement_round_{n}.json",
          "schema_id": "urn:phaseA:refinement_round:v1",
          "produced_by": "loop (A5 per iter)",
          "consumed_by": "audit/replay tooling",
          "purpose": "Per-iteration record: input hashes, defect fingerprint, patch hash, output hash, and termination checkpoint metadata."
        },
        {
          "artifact": "plan_delta_patch_{n}.json",
          "schema_id": "urn:phaseA:json_patch_rfc6902:v1",
          "produced_by": "loop (A5 per iter; planner output)",
          "consumed_by": "loop (A5 patch apply)",
          "purpose": "RFC-6902 JSON Patch operations applied to plan. This is the only permitted mutation mechanism for plan refinement."
        },
        {
          "artifact": "refinement_termination_record.json",
          "schema_id": "urn:phaseA:refinement_termination_record:v1",
          "produced_by": "loop (A5)",
          "consumed_by": "downstream phases / audit tooling",
          "purpose": "Single authoritative termination artifact recording PASS/FAIL reason and pointers to final plan and lint report."
        },
        {
          "artifact": "plan_delta_request.json",
          "schema_id": "urn:phaseA:plan_delta_request:v1",
          "produced_by": "loop (optional; expansion admission)",
          "consumed_by": "loop (admission gate) / planner",
          "purpose": "Structured request to add new plan nodes/scope during refinement; must be admitted only if it does not violate determinism constraints."
        }
      ]
    }
  },
  "envelope_spec": {
    "name": "ArtifactEnvelope",
    "version": "1.0",
    "purpose": "Metadata wrapper for artifacts enabling reproducibility, provenance tracking, and lineage integrity verification (LIV).",
    "schema": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "urn:phaseA:artifact_envelope:v1",
      "type": "object",
      "additionalProperties": false,
      "required": [
        "envelope_version",
        "run_id",
        "created_at",
        "producer",
        "artifact",
        "derived_from"
      ],
      "properties": {
        "envelope_version": {
          "type": "string",
          "const": "1.0"
        },
        "run_id": {
          "type": "string"
        },
        "created_at": {
          "$ref": "#/$defs/ISODateTime"
        },
        "producer": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "tool",
            "tool_version",
            "command"
          ],
          "properties": {
            "tool": {
              "type": "string"
            },
            "tool_version": {
              "type": "string"
            },
            "command": {
              "type": "string"
            },
            "args": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        },
        "artifact": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "path",
            "content_type",
            "bytes",
            "sha256",
            "schema_id"
          ],
          "properties": {
            "path": {
              "type": "string"
            },
            "content_type": {
              "type": "string"
            },
            "bytes": {
              "type": "integer",
              "minimum": 0
            },
            "sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "schema_id": {
              "type": [
                "string",
                "null"
              ]
            },
            "schema_version": {
              "type": [
                "string",
                "null"
              ]
            },
            "schema_validation": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "performed",
                "valid"
              ],
              "properties": {
                "performed": {
                  "type": "boolean"
                },
                "valid": {
                  "type": "boolean"
                },
                "validator": {
                  "type": [
                    "string",
                    "null"
                  ]
                },
                "errors_ref": {
                  "anyOf": [
                    {
                      "$ref": "#/$defs/ArtifactRef"
                    },
                    {
                      "type": "null"
                    }
                  ]
                }
              }
            }
          }
        },
        "derived_from": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/ArtifactRef"
          },
          "description": "Upstream artifacts this artifact depends on (paths + sha256)."
        },
        "provenance": {
          "type": "object",
          "additionalProperties": true,
          "properties": {
            "repo_root": {
              "type": [
                "string",
                "null"
              ]
            },
            "commit_sha": {
              "type": [
                "string",
                "null"
              ]
            },
            "context_signature_sha256": {
              "anyOf": [
                {
                  "$ref": "#/$defs/Sha256Hex"
                },
                {
                  "type": "null"
                }
              ]
            },
            "policy_snapshot_sha256": {
              "anyOf": [
                {
                  "$ref": "#/$defs/Sha256Hex"
                },
                {
                  "type": "null"
                }
              ]
            }
          }
        }
      },
      "$defs": {
        "ISODateTime": {
          "type": "string",
          "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
        },
        "Sha256Hex": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$"
        },
        "JsonPointer": {
          "type": "string",
          "description": "JSON Pointer string per RFC 6901.",
          "pattern": "^(\\/([^~]|~0|~1)*)*$"
        },
        "ArtifactRef": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "path",
            "sha256"
          ],
          "properties": {
            "path": {
              "type": "string"
            },
            "sha256": {
              "$ref": "#/$defs/Sha256Hex"
            },
            "schema_id": {
              "type": [
                "string",
                "null"
              ]
            },
            "content_type": {
              "type": [
                "string",
                "null"
              ]
            }
          }
        },
        "Defect": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "code",
            "severity",
            "message"
          ],
          "properties": {
            "code": {
              "type": "string",
              "enum": [
                "MISSING_COMPONENT",
                "INVALID_SCHEMA",
                "NO_ACCEPTANCE_TESTS",
                "SCOPE_AMBIGUOUS",
                "NON_DETERMINISTIC_INSTRUCTIONS",
                "DEPENDENCY_CYCLE",
                "SCOPE_OVERLAP",
                "PATCH_APPLY_FAILED",
                "PATCH_RESULT_INVALID_SCHEMA",
                "UNRESOLVED_TBD"
              ]
            },
            "severity": {
              "type": "string",
              "enum": [
                "hard",
                "soft"
              ]
            },
            "message": {
              "type": "string"
            },
            "location": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "json_pointer": {
                  "$ref": "#/$defs/JsonPointer"
                },
                "artifact_path": {
                  "type": "string"
                }
              }
            },
            "evidence": {
              "type": "object"
            },
            "remediation_hint": {
              "type": [
                "string",
                "null"
              ]
            }
          }
        }
      }
    },
    "hashing": {
      "method": "sha256(canonical_json_bytes)",
      "canonicalization": "RFC 8785 JSON Canonicalization Scheme (JCS) for JSON artifacts.",
      "citations": [
        "citeturn1search3",
        "citeturn1search4",
        "citeturn3search4"
      ]
    },
    "liv_checks": {
      "definition": "Before consuming any artifact, recompute sha256 over the canonicalized JSON content and compare to envelope.sha256 (and to any referencing ArtifactRef.sha256). Fail closed on mismatch.",
      "minimal_algorithm": [
        "Read artifact bytes from disk.",
        "If JSON: parse as JSON, canonicalize per RFC 8785, re-serialize to bytes, hash bytes with SHA-256.",
        "Compare computed hash to envelope.artifact.sha256.",
        "If artifact is referenced in manifest/signature/etc: compare computed hash to that reference sha256 too.",
        "On mismatch: emit liv_failure.json and exit code 11."
      ]
    },
    "example_envelope_instance": {
      "envelope_version": "1.0",
      "run_id": "phaseA_20260217T120102Z_9d4f3a9a-99dc-4d2c-b8b5-96edab01bd66",
      "created_at": "2026-02-17T12:01:05Z",
      "producer": {
        "tool": "plan_refine_cli",
        "tool_version": "1.0.0",
        "command": "skeleton",
        "args": [
          "--feature-id",
          "FEAT-123",
          "--objective",
          "Add Phase A CLI tool"
        ]
      },
      "artifact": {
        "path": ".acms_runs/phaseA_20260217T120102Z_9d4f3a9a-99dc-4d2c-b8b5-96edab01bd66/artifacts/phase/PHASE_A/skeleton/plan_skeleton.json",
        "content_type": "application/json",
        "bytes": 2048,
        "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "schema_id": "urn:phaseA:plan_skeleton:v1",
        "schema_version": "1.0",
        "schema_validation": {
          "performed": true,
          "valid": true,
          "validator": "jsonschema (draft-2020-12)",
          "errors_ref": null
        }
      },
      "derived_from": [
        {
          "path": ".acms_runs/.../planning_policy_snapshot.json",
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "schema_id": "urn:phaseA:planning_policy_snapshot:v1",
          "content_type": "application/json"
        },
        {
          "path": ".acms_runs/.../context_bundle_signature.json",
          "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "schema_id": "urn:phaseA:context_bundle_signature:v1",
          "content_type": "application/json"
        }
      ],
      "provenance": {
        "repo_root": "<REPO_ROOT>",
        "commit_sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "context_signature_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "policy_snapshot_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    }
  },
  "run_layout": {
    "runs_dir_default": ".acms_runs",
    "run_dir_template": ".acms_runs/{run_id}/",
    "layout_example": {
      "run_id": "phaseA_20260217T120102Z_9d4f3a9a-99dc-4d2c-b8b5-96edab01bd66",
      "tree": [
        ".acms_runs/{run_id}/",
        ".acms_runs/{run_id}/state/",
        ".acms_runs/{run_id}/state/checkpoints/",
        ".acms_runs/{run_id}/state/transition_log.jsonl",
        ".acms_runs/{run_id}/artifacts/",
        ".acms_runs/{run_id}/artifacts/envelopes/",
        ".acms_runs/{run_id}/artifacts/phase/PHASE_A/init/",
        ".acms_runs/{run_id}/artifacts/phase/PHASE_A/context/",
        ".acms_runs/{run_id}/artifacts/phase/PHASE_A/skeleton/",
        ".acms_runs/{run_id}/artifacts/phase/PHASE_A/lint/",
        ".acms_runs/{run_id}/artifacts/phase/PHASE_A/loop/round_001/",
        ".acms_runs/{run_id}/evidence/",
        ".acms_runs/{run_id}/evidence/phase/PHASE_A/",
        ".acms_runs/{run_id}/logs/",
        ".acms_runs/{run_id}/logs/orchestrator.jsonl",
        ".acms_runs/{run_id}/logs/tool_calls.jsonl"
      ]
    },
    "path_conventions": {
      "artifact_paths": {
        "planning_run_manifest": "artifacts/phase/PHASE_A/init/planning_run_manifest.json",
        "planning_policy_snapshot": "artifacts/phase/PHASE_A/init/planning_policy_snapshot.json",
        "context_bundle": "artifacts/phase/PHASE_A/context/context_bundle.json",
        "context_bundle_signature": "artifacts/phase/PHASE_A/context/context_bundle_signature.json",
        "plan_skeleton": "artifacts/phase/PHASE_A/skeleton/plan_skeleton.json",
        "plan_skeleton_schema_validation": "artifacts/phase/PHASE_A/skeleton/plan_skeleton_schema_validation.json",
        "lint_outputs_dir": "artifacts/phase/PHASE_A/lint/",
        "loop_round_dir": "artifacts/phase/PHASE_A/loop/round_{NNN}/"
      },
      "envelope_paths": {
        "rule": "Write an envelope next to each artifact with suffix '.envelope.json' OR mirror under artifacts/envelopes/ with same relative path + '.envelope.json'."
      }
    }
  },
  "step_behaviors": {
    "phase": "PHASE_A",
    "steps": {
      "A1_init": {
        "command": "init",
        "inputs": [],
        "outputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json"
        ],
        "behavior_details": [
          "Freeze planning identity and rules.",
          "Create policy snapshot containing required sections, defect taxonomy, determinism constraints, loop limits, and schema registry.",
          "Ensure policy snapshot is immutable after creation; downstream commands only reference its hash."
        ],
        "validations_and_gates": [
          "Gate G1: planning_policy_snapshot.json schema-valid.",
          "Gate G2: planning_run_manifest.json schema-valid."
        ],
        "liv": {
          "required": false,
          "notes": "No prior artifacts."
        }
      },
      "A2_context": {
        "command": "context",
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json"
        ],
        "outputs": [
          "context_bundle.json",
          "context_bundle_signature.json"
        ],
        "behavior_details": [
          "Inventory-first grounding: collect repo summary, templates/workstreams/gates/registry paths.",
          "Compute deterministic signature including file_count and root_tree_hash (implementation-defined but stable).",
          "Update manifest with references to context artifacts (whitelisted fields only)."
        ],
        "validations_and_gates": [
          "Gate G3: LIV check passes for run manifest and policy snapshot.",
          "Gate G4: context_bundle_signature.json includes context_bundle_sha256 matching produced context_bundle.json."
        ],
        "liv": {
          "required": true,
          "inputs_to_verify": [
            "planning_run_manifest.json",
            "planning_policy_snapshot.json"
          ],
          "outputs_to_envelope": [
            "context_bundle.json",
            "context_bundle_signature.json",
            "planning_run_manifest.json (updated)"
          ]
        }
      },
      "A3_skeleton": {
        "command": "skeleton",
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "context_bundle.json",
          "context_bundle_signature.json"
        ],
        "outputs": [
          "plan_skeleton.json",
          "plan_skeleton_schema_validation.json"
        ],
        "behavior_details": [
          "Generate minimal-but-complete plan object containing all required sections (policy-driven) even if values are 'TBD'.",
          "Validate against the frozen plan schema snapshot and write validation proof artifact."
        ],
        "validations_and_gates": [
          "Gate G5: LIV passes for all inputs.",
          "Gate G6: plan_skeleton_schema_validation.valid=true OR (if false) record INVALID_SCHEMA and stop (strict mode)."
        ],
        "liv": {
          "required": true
        }
      },
      "A4_lint": {
        "command": "lint",
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "context_bundle.json",
          "context_bundle_signature.json",
          "<plan>"
        ],
        "outputs": [
          "plan_lint_report.json",
          "plan_dependency_graph.json",
          "plan_cycles_report.json",
          "plan_scope_overlap_report.json"
        ],
        "behavior_details": [
          "Critic pass: produces structured defects + supporting analyses.",
          "Must not rewrite the plan."
        ],
        "validations_and_gates": [
          "Gate G7: LIV passes for all inputs.",
          "Gate G8: lint artifacts written; if strict mode and INVALID_SCHEMA found, lint may still write full companion artifacts but returns exit code 10."
        ],
        "liv": {
          "required": true
        },
        "defect_rules": {
          "hard_defects_block_phase_advancement": true,
          "soft_defects_advisory": true,
          "defect_examples": [
            "MISSING_COMPONENT",
            "INVALID_SCHEMA",
            "NO_ACCEPTANCE_TESTS",
            "SCOPE_AMBIGUOUS",
            "NON_DETERMINISTIC_INSTRUCTIONS",
            "DEPENDENCY_CYCLE",
            "SCOPE_OVERLAP"
          ]
        }
      },
      "A5_loop": {
        "command": "loop",
        "inputs": [
          "planning_run_manifest.json",
          "planning_policy_snapshot.json",
          "context_bundle.json",
          "context_bundle_signature.json",
          "<plan>"
        ],
        "outputs": [
          "refinement_round_{n}.json",
          "plan_delta_patch_{n}.json",
          "refined_plan_{n}.json",
          "refinement_termination_record.json"
        ],
        "behavior_details": [
          "Repeat: lint current plan → generate/read patch → apply patch → validate schema → re-lint.",
          "All plan edits are expressed as RFC-6902 patches; no in-place editing without patch artifact.",
          "Emit per-round record and patch artifact every iteration even if patch fails."
        ],
        "validations_and_gates": [
          "Gate G9: patch document validates as RFC-6902 JSON Patch. citeturn0search4",
          "Gate G10: patch applies cleanly with JSON Pointer paths. citeturn3search3",
          "Gate G11: if policy requires schema validity, patched plan must validate; else record defect and continue or terminate per policy.",
          "Gate G12: termination record emitted on PASS or FAIL."
        ],
        "termination_rules": {
          "PASS": {
            "reason": "NO_HARD_DEFECTS",
            "condition": "len(hard_defects)==0"
          },
          "FAIL_MAX_ITERS": {
            "reason": "MAX_ITERATIONS_REACHED",
            "condition": "iterations == max_iters and len(hard_defects)>0"
          },
          "FAIL_OSCILLATION": {
            "reason": "OSCILLATION_DETECTED",
            "condition": "hard_defect_fingerprint repeats within oscillation_window >= policy.oscillation_repeat_limit"
          }
        }
      }
    },
    "oscillation_detection": {
      "fingerprint_definition": "sha256 of canonical JSON array of hard defects reduced to [code, location.json_pointer] tuples sorted lexicographically by (code, pointer).",
      "state_to_track": [
        "last_k_fingerprints (k=oscillation_window)",
        "repeat_counts per fingerprint"
      ],
      "termination": "If current fingerprint already seen at least policy.loop_limits.oscillation_repeat_limit times OR repeats within window, terminate with OSCILLATION_DETECTED.",
      "citations": [
        "citeturn1search3",
        "citeturn3search4"
      ]
    },
    "patch_only_discipline": {
      "rule": "During A5, the plan may only change by applying a plan_delta_patch_{n}.json RFC-6902 patch document to the previous plan artifact.",
      "why": [
        "Prevents silent edits; each change is explicit and replayable.",
        "Enables oscillation detection by comparing defect fingerprints across iterations.",
        "Supports auditable lineage (derived_from in envelopes)."
      ],
      "citations": [
        "citeturn0search4"
      ]
    }
  },
  "sample_artifacts": {
    "note": "Samples use placeholder hashes and paths; real implementations MUST compute sha256 per hashing_rules and populate envelopes/refs accordingly.",
    "rfc6902_note": "plan_delta_patch_{n}.json is a JSON Patch document (array of operations) per RFC 6902; operation paths use JSON Pointer syntax per RFC 6901.",
    "citations": [
      "citeturn0search4",
      "citeturn3search3"
    ],
    "instances": {
      "planning_run_manifest.json": {
        "run_id": "phaseA_20260217T120102Z_9d4f3a9a-99dc-4d2c-b8b5-96edab01bd66",
        "repo_root": "<REPO_ROOT>",
        "runs_dir": ".acms_runs",
        "created_at": "2026-02-17T12:01:02Z",
        "planner_version": "1.0.0",
        "policy_version": "1.0.0",
        "schema_version": "2020-12",
        "policy_snapshot": {
          "path": ".acms_runs/.../artifacts/phase/PHASE_A/init/planning_policy_snapshot.json",
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "schema_id": "urn:phaseA:planning_policy_snapshot:v1",
          "content_type": "application/json"
        },
        "context_bundle": null,
        "context_bundle_signature": null,
        "context_hash": null,
        "plan_schema": "urn:phaseA:plan_skeleton:v1",
        "notes": [
          "context_* refs will be filled by `context` command"
        ]
      },
      "planning_policy_snapshot.json": {
        "policy_id": "policy_phaseA_default",
        "policy_version": "1.0.0",
        "created_at": "2026-02-17T12:01:03Z",
        "required_plan_sections": [
          "feature_id",
          "objective",
          "constraints",
          "workstreams",
          "global_requirements",
          "risks",
          "deferred_items"
        ],
        "defect_taxonomy": [
          {
            "code": "MISSING_COMPONENT",
            "default_severity": "hard",
            "classification": "completeness",
            "description": "Required section absent or empty."
          },
          {
            "code": "INVALID_SCHEMA",
            "default_severity": "hard",
            "classification": "schema",
            "description": "Plan fails schema validation."
          },
          {
            "code": "NO_ACCEPTANCE_TESTS",
            "default_severity": "hard",
            "classification": "determinism",
            "description": "Workstream/task lacks measurable acceptance tests."
          },
          {
            "code": "SCOPE_AMBIGUOUS",
            "default_severity": "hard",
            "classification": "determinism",
            "description": "Write scope unclear or missing."
          },
          {
            "code": "NON_DETERMINISTIC_INSTRUCTIONS",
            "default_severity": "hard",
            "classification": "determinism",
            "description": "Ambiguous language that cannot be machine-judged."
          },
          {
            "code": "DEPENDENCY_CYCLE",
            "default_severity": "hard",
            "classification": "dependency",
            "description": "Dependency cycle exists."
          },
          {
            "code": "SCOPE_OVERLAP",
            "default_severity": "hard",
            "classification": "scope",
            "description": "Overlapping write scopes without waiver."
          }
        ],
        "loop_limits": {
          "max_iterations": 6,
          "oscillation_repeat_limit": 2,
          "max_patch_ops": 200
        },
        "determinism_constraints": {
          "no_dependency_cycles": true,
          "no_scope_overlaps": true,
          "no_ambiguous_instructions": true,
          "require_acceptance_tests": true,
          "allow_tbd_placeholders": true
        },
        "gating_rules": {
          "pass_condition": "NO_HARD_DEFECTS",
          "fail_closed": true,
          "treat_soft_defects_as_hard": false,
          "scope_overlap_waiver_policy": {
            "allowed": false,
            "requires_justification": true,
            "waiver_format": "string"
          }
        },
        "schema_registry": {
          "artifact_schemas": [
            {
              "schema_id": "urn:phaseA:planning_run_manifest:v1",
              "artifact": "planning_run_manifest.json",
              "version": "1.0",
              "compatibility_family": "phaseA_core"
            },
            {
              "schema_id": "urn:phaseA:context_bundle:v1",
              "artifact": "context_bundle.json",
              "version": "1.0",
              "compatibility_family": "phaseA_core"
            }
          ],
          "plan_schema": {
            "schema_id": "urn:phaseA:plan_skeleton:v1",
            "version": "1.0",
            "compatibility_family": "phaseA_plan"
          }
        },
        "notes": [
          "This snapshot is frozen for the run; do not modify after init."
        ]
      },
      "context_bundle.json": {
        "generated_at": "2026-02-17T12:02:10Z",
        "repo_root": "<REPO_ROOT>",
        "repo_summary": {
          "name": "<REPO_NAME>",
          "description": "Monorepo for planning/orchestration pipeline components.",
          "language_stack": [
            "python",
            "typescript"
          ]
        },
        "inventory": {
          "templates": [
            "templates/heal_templates.json"
          ],
          "workstreams": [
            "workstreams/"
          ],
          "gates": [
            "gates/"
          ],
          "registries": [
            "schemas/",
            "registries/"
          ]
        },
        "paths": {
          "templates_roots": [
            "<REPO_ROOT>/templates"
          ],
          "workstreams_roots": [
            "<REPO_ROOT>/workstreams"
          ],
          "gates_roots": [
            "<REPO_ROOT>/gates"
          ],
          "registry_roots": [
            "<REPO_ROOT>/schemas",
            "<REPO_ROOT>/registries"
          ]
        },
        "recent_changes": [
          {
            "id": "deadbeef",
            "summary": "Update planning policy snapshot schema",
            "timestamp": "2026-02-15T19:30:00Z"
          }
        ],
        "notes": [
          "Inventory content is implementation-defined but must be grounded in repo reality and deterministic."
        ]
      },
      "context_bundle_signature.json": {
        "generated_at": "2026-02-17T12:02:12Z",
        "repo_root": "<REPO_ROOT>",
        "git_available": true,
        "commit_sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "dirty": false,
        "file_count": 1240,
        "root_tree_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "include_globs": [
          "**/*.json",
          "**/*.md",
          "**/*.py"
        ],
        "exclude_globs": [
          ".git/**",
          ".acms_runs/**",
          "node_modules/**",
          "dist/**",
          "build/**"
        ],
        "context_bundle_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
      },
      "plan_skeleton.json": {
        "feature_id": "FEAT-123",
        "objective": "Implement Phase A planning-only refinement CLI with deterministic artifacts.",
        "constraints": [
          "No execution compilation in Phase A.",
          "All plan changes in loop must be RFC-6902 patches.",
          "Fail closed on schema mismatch or LIV failure."
        ],
        "global_requirements": [
          {
            "id": "GR-1",
            "requirement": "All artifacts must be hashed and (optionally) enveloped.",
            "acceptance_criteria": [
              "Each artifact has sha256 recorded in envelope or refs."
            ]
          },
          {
            "id": "GR-2",
            "requirement": "Plan must be deterministic and schema-valid.",
            "acceptance_criteria": [
              "No hard defects in lint report."
            ]
          }
        ],
        "workstreams": [
          {
            "id": "WS-CLI",
            "summary": "Implement CLI commands and wiring.",
            "writes_scopes": [
              "src/phase_a_cli/**",
              "schemas/**"
            ],
            "depends_on": [],
            "acceptance_tests": [
              "Unit tests pass: cli parsing, artifact emission, termination record always written."
            ]
          },
          {
            "id": "WS-LINT",
            "summary": "Implement plan lint and determinism analysis.",
            "writes_scopes": [
              "src/lint/**"
            ],
            "depends_on": [
              "WS-CLI"
            ],
            "acceptance_tests": [
              "lint detects missing acceptance tests and scope overlaps deterministically."
            ],
            "tasks": [
              {
                "id": "TASK-LINT-0",
                "summary": "Define defect schema and ensure stable codes.",
                "writes_scopes": [
                  "src/lint/**"
                ],
                "depends_on": [
                  "WS-CLI"
                ],
                "acceptance_tests": []
              }
            ]
          }
        ],
        "risks": [
          {
            "id": "R-1",
            "risk": "Hashing differs across platforms if JSON not canonicalized.",
            "mitigation": "Use RFC 8785 JCS for canonical JSON before hashing.",
            "severity": "high"
          }
        ],
        "deferred_items": [
          "Phase B execution compilation integration (out of scope for Phase A CLI)."
        ],
        "metadata": {
          "created_at": "2026-02-17T12:05:00Z",
          "schema_id": "urn:phaseA:plan_skeleton:v1",
          "schema_version": "1.0",
          "context_signature_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        }
      },
      "plan_skeleton_schema_validation.json": {
        "generated_at": "2026-02-17T12:05:01Z",
        "plan_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "schema_id": "urn:phaseA:plan_skeleton:v1",
        "schema_version": "1.0",
        "valid": true,
        "errors": []
      },
      "plan_dependency_graph.json": {
        "generated_at": "2026-02-17T12:06:00Z",
        "plan_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "nodes": [
          {
            "id": "WS-CLI",
            "kind": "workstream",
            "writes_scopes": [
              "src/phase_a_cli/**",
              "schemas/**"
            ],
            "acceptance_tests": [
              "Unit tests pass: cli parsing, artifact emission, termination record always written."
            ]
          },
          {
            "id": "WS-LINT",
            "kind": "workstream",
            "writes_scopes": [
              "src/lint/**"
            ],
            "acceptance_tests": [
              "lint detects missing acceptance tests and scope overlaps deterministically."
            ]
          }
        ],
        "edges": [
          {
            "from": "WS-LINT",
            "to": "WS-CLI",
            "type": "depends_on"
          }
        ]
      },
      "plan_cycles_report.json": {
        "generated_at": "2026-02-17T12:06:01Z",
        "plan_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "cycle_count": 0,
        "cycles": []
      },
      "plan_scope_overlap_report.json": {
        "generated_at": "2026-02-17T12:06:02Z",
        "plan_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "overlap_count": 0,
        "overlaps": []
      },
      "plan_lint_report.json": {
        "generated_at": "2026-02-17T12:06:03Z",
        "plan_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "policy_snapshot_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "hard_defects": [
          {
            "code": "NO_ACCEPTANCE_TESTS",
            "severity": "hard",
            "message": "Task TASK-LINT-0 in workstream WS-LINT has empty acceptance_tests.",
            "location": {
              "json_pointer": "/workstreams/1/tasks/0/acceptance_tests",
              "artifact_path": "plan_skeleton.json"
            },
            "evidence": {
              "workstream_id": "WS-LINT",
              "task_id": "TASK-LINT-0"
            },
            "remediation_hint": "Add measurable acceptance_tests array for all tasks."
          }
        ],
        "soft_defects": [],
        "summary": {
          "hard_count": 1,
          "soft_count": 0,
          "defect_codes": [
            "NO_ACCEPTANCE_TESTS"
          ]
        },
        "analysis_metadata": {
          "dependency_graph_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
          "cycles_report_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
          "scope_overlap_report_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
        }
      },
      "plan_delta_patch_1.json": [
        {
          "op": "test",
          "path": "/workstreams/1/tasks/0/id",
          "value": "TASK-LINT-0"
        },
        {
          "op": "replace",
          "path": "/workstreams/1/tasks/0/acceptance_tests",
          "value": [
            "Lint emits hard_defects[] and soft_defects[] with stable codes and pointers."
          ]
        }
      ],
      "refinement_round_1.json": {
        "round": 1,
        "generated_at": "2026-02-17T12:10:00Z",
        "input_plan": {
          "path": "plan_skeleton.json",
          "sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "schema_id": "urn:phaseA:plan_skeleton:v1",
          "content_type": "application/json"
        },
        "lint_report": {
          "path": "plan_lint_report.json",
          "sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
          "schema_id": "urn:phaseA:plan_lint_report:v1",
          "content_type": "application/json"
        },
        "patch": {
          "path": "plan_delta_patch_1.json",
          "sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
          "schema_id": "urn:phaseA:json_patch_rfc6902:v1",
          "content_type": "application/json-patch+json"
        },
        "output_plan": {
          "path": "refined_plan_1.json",
          "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "schema_id": "urn:phaseA:plan_skeleton:v1",
          "content_type": "application/json"
        },
        "hard_defect_fingerprint": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "termination_checkpoint": {
          "pass_condition_met": false,
          "hard_defects_remaining": 1,
          "termination_reason_if_any": null
        },
        "notes": [
          "Patch fixed missing task acceptance tests."
        ]
      },
      "refinement_termination_record.json": {
        "generated_at": "2026-02-17T12:30:00Z",
        "reason": "NO_HARD_DEFECTS",
        "iterations": 2,
        "max_allowed": 6,
        "final_plan": {
          "path": "refined_plan_2.json",
          "sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "schema_id": "urn:phaseA:plan_skeleton:v1",
          "content_type": "application/json"
        },
        "final_lint_report": {
          "path": "plan_lint_report.json",
          "sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
          "schema_id": "urn:phaseA:plan_lint_report:v1",
          "content_type": "application/json"
        },
        "oscillation_details": null,
        "notes": [
          "PASS: NO_HARD_DEFECTS"
        ]
      },
      "plan_delta_request.json": {
        "source_workstream": "WS-LINT",
        "reason": "Need to add scope-overlap detection for write scopes.",
        "evidence": "Lint report contains SCOPE_OVERLAP false negatives without explicit normalization.",
        "blocking": true,
        "proposed_new_nodes": [
          {
            "id": "TASK-SCOPE-1",
            "kind": "task",
            "summary": "Implement normalized scope overlap detector.",
            "writes_scopes": [
              "src/lint/scope/**"
            ],
            "depends_on": [
              "WS-LINT"
            ],
            "acceptance_tests": [
              "Overlap report lists conflicting writers with normalized_scope."
            ]
          }
        ]
      }
    },
    "rfc6902_examples": {
      "example_replace_tbd_with_explicit_acceptance": [
        {
          "op": "replace",
          "path": "/global_requirements/0/acceptance_criteria",
          "value": [
            "CLI writes planning_run_manifest.json and planning_policy_snapshot.json with envelopes."
          ]
        }
      ],
      "example_add_scope_declaration": [
        {
          "op": "add",
          "path": "/workstreams/0/writes_scopes/-",
          "value": "docs/phase_a/**"
        }
      ],
      "example_test_guard": [
        {
          "op": "test",
          "path": "/feature_id",
          "value": "FEAT-123"
        },
        {
          "op": "replace",
          "path": "/objective",
          "value": "Implement deterministic Phase A CLI spec"
        }
      ]
    }
  },
  "unit_tests": {
    "focus": "High-signal tests that catch nondeterminism, missing emissions, parsing hazards, and termination regressions.",
    "checklist": [
      {
        "id": "UT-ARGPARSE-DEST",
        "description": "Argparse hyphen-to-underscore mapping does not break attribute access (e.g., --out-envelope -> args.out_envelope).",
        "steps": [
          "Invoke CLI with --out-envelope false.",
          "Assert parsed Namespace has attribute out_envelope and not out-envelope.",
          "Assert code reads args.out_envelope or uses explicit dest."
        ],
        "expected": "No AttributeError; flag behavior correct.",
        "citations": [
          "citeturn2search0"
        ]
      },
      {
        "id": "UT-UUID4",
        "description": "run_id generation uses uuid.uuid4() correctly (no typos like uuid.uuid-4()).",
        "steps": [
          "Call run_id generator without --run-id.",
          "Assert UUID component parses as RFC4122/uuid format and function used is uuid4()."
        ],
        "expected": "run_id includes a valid uuid4 component.",
        "citations": [
          "citeturn1search0"
        ]
      },
      {
        "id": "UT-INIT-EMITS",
        "description": "init emits both manifest and policy snapshot and (if enabled) envelopes.",
        "steps": [
          "Run init.",
          "Assert required files exist and are schema-valid.",
          "Assert envelope sha256 matches recomputation."
        ],
        "expected": "Artifacts present and LIV-verifiable."
      },
      {
        "id": "UT-CONTEXT-UPDATES-MANIFEST-WHITELIST",
        "description": "context updates manifest only for whitelisted fields and preserves previous manifest version.",
        "steps": [
          "Run init then context.",
          "Assert planning_run_manifest.prev_*.json exists.",
          "Diff manifests and assert only context_* fields changed."
        ],
        "expected": "No silent mutation of frozen identity/policy fields."
      },
      {
        "id": "UT-SKELETON-REQUIRED-SECTIONS",
        "description": "skeleton produces a plan_skeleton.json containing all required sections (even if TBD).",
        "steps": [
          "Run init+context+skeleton.",
          "Validate plan_skeleton.json keys match policy required_plan_sections."
        ],
        "expected": "No missing components."
      },
      {
        "id": "UT-LINT-NONMUTATING",
        "description": "lint does not modify plan input file.",
        "steps": [
          "Hash plan before lint.",
          "Run lint.",
          "Hash plan after lint."
        ],
        "expected": "Hashes match; only lint artifacts created."
      },
      {
        "id": "UT-LIV-FAIL-CLOSED",
        "description": "LIV detects mismatched artifact hashes and fails closed.",
        "steps": [
          "Corrupt a byte in context_bundle.json after signature is written.",
          "Run skeleton or lint.",
          "Assert exit code 11."
        ],
        "expected": "Process stops with LIV failure and produces liv_failure artifact/log."
      },
      {
        "id": "UT-LOOP-TERMINATION-RECORD-ALWAYS",
        "description": "loop always writes refinement_termination_record.json (PASS or FAIL).",
        "steps": [
          "Run loop with max-iters=1 on a plan that has hard defects.",
          "Assert termination record exists with reason MAX_ITERATIONS_REACHED OR OSCILLATION_DETECTED.",
          "Run loop on fixed plan and assert NO_HARD_DEFECTS."
        ],
        "expected": "Termination record emitted in all cases."
      },
      {
        "id": "UT-RFC6902-PATCH-VALIDATION",
        "description": "Patch validation rejects malformed operations and invalid JSON Pointer paths.",
        "steps": [
          "Provide patch with op=invalid or missing path/value.",
          "Run loop/manual patch apply.",
          "Assert exit code 10 and defect PATCH_APPLY_FAILED or schema validation failure."
        ],
        "expected": "Fail closed on invalid patch.",
        "citations": [
          "citeturn0search4",
          "citeturn3search3"
        ]
      }
    ],
    "bash_heredoc_test": {
      "id": "UT-HEREDOC-QUOTING",
      "description": "If a bash script harness uses heredocs to generate JSON patches/configs, quoted delimiters prevent unintended variable expansion.",
      "steps": [
        "Generate a patch file via heredoc containing literal '$' and backticks.",
        "Use delimiter quoted as <<'EOF'.",
        "Assert generated file contains literal characters unchanged."
      ],
      "expected": "No variable expansion; patch JSON remains valid.",
      "citations": [
        "citeturn5search0"
      ]
    }
  },
  "hazards_mitigations": {
    "known_hazards": [
      {
        "id": "HZ-ARGPARSE-HYPHEN",
        "hazard": "Argparse dest mapping: flags with internal '-' produce Namespace attributes with '_' (e.g., --out-envelope -> out_envelope).",
        "impact": "Runtime AttributeError or ignored flags when code expects args.out-envelope or other invalid attribute name.",
        "mitigation": [
          "Always set dest explicitly for critical flags (dest='out_envelope').",
          "Add unit test UT-ARGPARSE-DEST.",
          "Prefer snake_case names in code; never reference hyphenated names."
        ],
        "citations": [
          "citeturn2search0"
        ]
      },
      {
        "id": "HZ-UUID4-TYPO",
        "hazard": "Typos in UUID generation (e.g., uuid.uuid-4() instead of uuid.uuid4()).",
        "impact": "Crash at runtime or non-unique run IDs.",
        "mitigation": [
          "Use Python stdlib uuid.uuid4() exclusively.",
          "Test run_id generator; validate UUID format."
        ],
        "citations": [
          "citeturn1search0"
        ]
      },
      {
        "id": "HZ-BASH-HEREDOC-EXPANSION",
        "hazard": "Bash heredoc expansion can unintentionally expand variables or command substitutions inside generated JSON (patches/manifests), corrupting JSON or changing semantics.",
        "impact": "Invalid JSON patches, wrong sha256 hashes, nondeterministic artifacts.",
        "mitigation": [
          "When using heredocs to generate files, quote the delimiter: <<'EOF' to disable expansions.",
          "Avoid mixing bash template expansion with deterministic hashing; generate JSON via a JSON serializer where possible.",
          "Add UT-HEREDOC-QUOTING."
        ],
        "citations": [
          "citeturn5search0"
        ]
      },
      {
        "id": "HZ-NONCANONICAL-JSON",
        "hazard": "Hashing JSON without canonicalization yields different bytes across serializers (whitespace, key order) and can break reproducibility.",
        "impact": "LIV false positives/negatives and inability to replay runs deterministically.",
        "mitigation": [
          "Canonicalize JSON per RFC 8785 (JCS) before hashing.",
          "Enforce 'no duplicate keys' and stable numeric formatting for hashing inputs."
        ],
        "citations": [
          "citeturn1search3turn1search4",
          "citeturn3search0"
        ]
      },
      {
        "id": "HZ-DUPLICATE-JSON-KEYS",
        "hazard": "Duplicate object keys are not prohibited by some parsers; behavior becomes parser-dependent.",
        "impact": "Different interpretation of same artifact and non-reproducible hashes/validation results.",
        "mitigation": [
          "Reject JSON objects with duplicate keys at parse time (required by RFC 8785 I-JSON profile in canonicalization).",
          "Document parser settings and enforce strict JSON parsing."
        ],
        "citations": [
          "citeturn1search3"
        ]
      },
      {
        "id": "HZ-NONDETERMINISTIC-FILE-TRAVERSAL",
        "hazard": "Filesystem traversal order can differ across OS/filesystems, making context inventories nondeterministic.",
        "impact": "context_bundle_signature changes unexpectedly, breaking run reproducibility.",
        "mitigation": [
          "Always traverse paths in sorted order.",
          "Normalize path separators and consistently exclude run outputs (e.g., .acms_runs)."
        ]
      }
    ]
  },
  "schema_evolution": {
    "goal": "Allow controlled evolution of artifact schemas and plan schema while keeping a run reproducible via a frozen snapshot.",
    "compatibility_families": [
      {
        "family": "phaseA_core",
        "description": "Core run/context artifact schemas (manifest, policy snapshot, context bundle/signature).",
        "compatibility_rules": "Minor/patch versions may add optional fields; removing/renaming required fields is breaking."
      },
      {
        "family": "phaseA_plan",
        "description": "Plan schema family for plan_skeleton and refined_plan outputs.",
        "compatibility_rules": "Required top-level keys and semantics should remain stable; additions allowed if policy updates required sections explicitly."
      }
    ],
    "compatibility_matrix": [
      {
        "schema_id": "urn:phaseA:planning_run_manifest:v1",
        "family": "phaseA_core",
        "compatible_with": [
          "urn:phaseA:planning_run_manifest:v1"
        ],
        "breaking_changes": [
          "v2 required field changes"
        ]
      },
      {
        "schema_id": "urn:phaseA:planning_policy_snapshot:v1",
        "family": "phaseA_core",
        "compatible_with": [
          "urn:phaseA:planning_policy_snapshot:v1"
        ],
        "breaking_changes": [
          "v2 removes defect taxonomy fields"
        ]
      },
      {
        "schema_id": "urn:phaseA:plan_skeleton:v1",
        "family": "phaseA_plan",
        "compatible_with": [
          "urn:phaseA:plan_skeleton:v1"
        ],
        "breaking_changes": [
          "v2 changes workstreams structure"
        ]
      }
    ],
    "fail_closed_rules": [
      "If planning_policy_snapshot.json references a schema_id not present in the local schema registry: FAIL (exit 10).",
      "If a consumed artifact declares schema_id that is not in the snapshot's allowed list: FAIL.",
      "If schema_version/dialect differs from frozen snapshot (unless explicitly allowed by compatibility matrix): FAIL.",
      "If validator cannot load the referenced meta-schema/dialect: FAIL."
    ],
    "json_schema_notes": {
      "dialect": "Use JSON Schema draft 2020-12 for artifact schemas and validation artifacts unless policy snapshot specifies otherwise.",
      "meta_schema_reference": "Artifacts may include $schema and $id fields; validators should use the 2020-12 Core + Validation specs.",
      "citations": [
        "citeturn0search0turn0search1turn0search5"
      ]
    }
  },
  "sources": {
    "required_project_sources": [
      {
        "id": "proj_two_phase_planning_architecture",
        "title": "Two-Phase Planning Architecture (Phase A / Phase B) — project repo doc",
        "status": "not accessible via file_search/api_tool in this environment",
        "how_used": "Phase A requirements implemented from user-provided excerpt describing Phase A steps and artifacts."
      },
      {
        "id": "proj_integrated_langgraph_orchestrator",
        "title": "Integrated LangGraph Orchestrator (artifact envelopes, LIV, routing) — project repo doc",
        "status": "not accessible via file_search/api_tool in this environment",
        "how_used": "Envelope + LIV patterns included as requested, aligned to artifact-first/fail-closed principles."
      },
      {
        "id": "proj_langgraph_integration_architecture",
        "title": "LangGraph Integration Architecture — project repo doc",
        "status": "not accessible via file_search/api_tool in this environment",
        "how_used": "Run layout and artifact handoff sections structured for compatibility with an orchestrator."
      },
      {
        "id": "proj_deep_research_report",
        "title": "deep-research-report (defect taxonomy, heal templates) — project repo doc",
        "status": "not accessible via file_search/api_tool in this environment",
        "how_used": "Defect taxonomy and structured defect objects included per user specification; hooks provided for heal templates."
      },
      {
        "id": "proj_errors_doc",
        "title": "errors doc (argparse, uuid4, bash heredoc) — project repo doc",
        "status": "not accessible via file_search/api_tool in this environment",
        "how_used": "Hazards and mitigations included; backed by official Python docs and bash manual citations."
      }
    ],
    "external_primary_sources": [
      {
        "id": "rfc6902",
        "title": "RFC 6902: JavaScript Object Notation (JSON) Patch",
        "citation": "citeturn0search4"
      },
      {
        "id": "rfc6901",
        "title": "RFC 6901: JavaScript Object Notation (JSON) Pointer",
        "citation": "citeturn3search3"
      },
      {
        "id": "rfc8785",
        "title": "RFC 8785: JSON Canonicalization Scheme (JCS)",
        "citation": "citeturn1search3turn1search4"
      },
      {
        "id": "rfc8259",
        "title": "RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format",
        "citation": "citeturn3search0turn3search5"
      },
      {
        "id": "json_schema_spec",
        "title": "JSON Schema Specification (draft 2020-12)",
        "citation": "citeturn0search0turn0search1turn0search5"
      },
      {
        "id": "python_argparse",
        "title": "Python argparse documentation (dest mapping hyphen→underscore)",
        "citation": "citeturn2search0"
      },
      {
        "id": "python_uuid",
        "title": "Python uuid documentation (uuid.uuid4())",
        "citation": "citeturn1search0"
      },
      {
        "id": "nist_shs",
        "title": "NIST Secure Hash Standard (FIPS 180-4 related)",
        "citation": "citeturn3search4turn3search2"
      },
      {
        "id": "bash_heredoc",
        "title": "GNU Bash Reference Manual — Here Documents",
        "citation": "citeturn5search0"
      },
      {
        "id": "mermaid_flowchart",
        "title": "Mermaid flowchart syntax",
        "citation": "citeturn3search1"
      },
      {
        "id": "mermaid_er",
        "title": "Mermaid entity-relationship diagram syntax",
        "citation": "citeturn4search0"
      }
    ]
  },
  "diagrams": {
    "phase_a_flowchart_mermaid": "flowchart TD\n  A1[init (A1)\\nplanning_run_manifest.json\\nplanning_policy_snapshot.json] --> A2[context (A2)\\ncontext_bundle.json\\ncontext_bundle_signature.json]\n  A2 --> A3[skeleton (A3)\\nplan_skeleton.json\\nplan_skeleton_schema_validation.json]\n  A3 --> A4[lint (A4)\\nplan_lint_report.json\\nplan_dependency_graph.json\\nplan_cycles_report.json\\nplan_scope_overlap_report.json]\n  A4 --> A5{loop (A5)\\nNO_HARD_DEFECTS?}\n  A5 -- yes --> PASS[Termination: NO_HARD_DEFECTS\\nrefinement_termination_record.json]\n  A5 -- no --> PATCH[Generate/Read patch\\nplan_delta_patch_n.json]\n  PATCH --> APPLY[Apply RFC-6902 JSON Patch\\nValidate schema]\n  APPLY --> RND[Write refinement_round_n.json\\nWrite refined_plan_n.json]\n  RND --> A4\n  A5 -- max iters/oscillation --> FAIL[Termination: MAX_ITERATIONS_REACHED or OSCILLATION_DETECTED\\nrefinement_termination_record.json]\n",
    "artifact_relationships_mermaid": "erDiagram\n  PLANNING_RUN_MANIFEST ||--|| PLANNING_POLICY_SNAPSHOT : references\n  PLANNING_RUN_MANIFEST ||--o| CONTEXT_BUNDLE : references\n  PLANNING_RUN_MANIFEST ||--o| CONTEXT_BUNDLE_SIGNATURE : references\n\n  CONTEXT_BUNDLE_SIGNATURE ||--|| CONTEXT_BUNDLE : signs\n\n  PLAN_SKELETON ||--|| PLAN_SCHEMA_VALIDATION : validates\n  PLAN_SKELETON ||--o{ PLAN_LINT_REPORT : linted_by\n  PLAN_LINT_REPORT ||--|| PLAN_DEPENDENCY_GRAPH : includes\n  PLAN_LINT_REPORT ||--|| PLAN_CYCLES_REPORT : includes\n  PLAN_LINT_REPORT ||--|| PLAN_SCOPE_OVERLAP_REPORT : includes\n\n  PLAN_DELTA_PATCH ||--|| REFINED_PLAN : produces\n  REFINED_PLAN ||--o{ PLAN_LINT_REPORT : re_linted_by\n\n  REFINEMENT_ROUND ||--|| PLAN_DELTA_PATCH : records\n  REFINEMENT_ROUND ||--|| PLAN_LINT_REPORT : records\n  REFINEMENT_ROUND ||--|| REFINED_PLAN : records\n\n  REFINEMENT_TERMINATION_RECORD ||--|| REFINED_PLAN : final_plan\n  REFINEMENT_TERMINATION_RECORD ||--|| PLAN_LINT_REPORT : final_lint\n",
    "mermaid_notes": {
      "flowchart_syntax_reference": "Mermaid flowcharts use nodes and edges with direction tokens (TB/TD/LR/etc).",
      "er_syntax_reference": "Mermaid ER diagrams use 'erDiagram' plus crow's-foot relation markers.",
      "citations": [
        "citeturn3search1",
        "citeturn4search0"
      ]
    }
  }
}