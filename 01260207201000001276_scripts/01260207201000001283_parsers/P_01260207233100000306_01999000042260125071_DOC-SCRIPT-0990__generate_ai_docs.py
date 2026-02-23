#!/usr/bin/env python3
"""
FILE_ID: 01999000042260125071
Migrated from: C:\Users\richg\ALL_AI\mapp_py\DOC-SCRIPT-0990__generate_ai_docs.py
"""

# DOC_ID: DOC-SCRIPT-0990
"""Generate comprehensive AI-consumable system documentation."""
import json
from pathlib import Path

documentation = {
    "doc_id": "DOC-MAPP-PY-SYSTEM-AI-001",
    "document_type": "COMPREHENSIVE_SYSTEM_DOCUMENTATION",
    "intended_audience": "AI_AGENTS_ONLY",
    "format_version": "1.0.0",
    "generated_date": "2026-01-08T23:00:00Z",

    "system_metadata": {
        "system_name": "mapp_py",
        "full_name": "Multi-dimensional Analysis and Python Provenance - Python Introspection Layer",
        "version": "1.0.0",
        "status": "PRODUCTION_READY",
        "created_date": "2026-01-08",
        "work_id": "WORK-MAPP-PY-001",
        "phases_completed": [0, 1, 2, 3, 4, 5, 6, 7],
        "location": {
            "absolute_path": "C:\\Users\\richg\\ALL_AI\\mapp_py",
            "relative_to_root": "mapp_py",
            "git_repository": "C:\\Users\\richg\\ALL_AI"
        },
        "primary_purpose": "Python file comparison and similarity analysis for automated codebase triage",
        "capabilities": [
            "AST-based structural similarity analysis",
            "TF-IDF semantic similarity analysis",
            "Import dependency overlap detection",
            "CLI argument and environment variable I/O surface analysis",
            "Multi-dimensional weighted scoring",
            "Evidence generation for triage decision engine"
        ],
        "test_metrics": {
            "total_tests": 118,
            "test_pass_rate_percent": 100.0,
            "code_coverage_percent": 87.41,
            "unit_tests": 89,
            "integration_tests_pipeline": 19,
            "integration_tests_provenance": 10,
            "bdd_specifications": 9
        },
        "governance_compliance": {
            "five_layer_model_compliant": True,
            "layer_1_process": {
                "work_id_tracking": True,
                "runbook_execution": True,
                "change_management": "sequential_commits"
            },
            "layer_2_quality": {
                "bdd_first_development": True,
                "test_coverage_percent": 87.41,
                "stable_id_system": "R-MAPP-PY-001 through R-MAPP-PY-008"
            },
            "layer_3_infrastructure": {
                "no_drift_policy": True,
                "manifest_driven": True,
                "dir_manifest_present": True,
                "dir_contract_present": True
            },
            "layer_4_observability": {
                "trace_id_propagation": True,
                "run_id_tracking": True,
                "component_ids": "MAPP_PY_* namespace",
                "observable_logger": True
            },
            "layer_5_knowledge": {
                "ssot_updated": True,
                "ssot_patch": "0006_register_mapp_py_subsystem.patch.json",
                "documentation_complete": True,
                "bdd_specs_count": 9
            }
        }
    },

    "integrated_system": {
        "name": "AI_CLI_PROVENANCE_SOLUTION",
        "location": "C:\\Users\\richg\\ALL_AI\\AI_CLI_PROVENANCE_SOLUTION",
        "relationship_type": "EVIDENCE_PROVIDER",
        "integration_status": "FULLY_OPERATIONAL",
        "integration_date": "2026-01-08",
        "integration_phase": "Phase 7",
        "rules_enabled": {
            "R_RED_001": {
                "rule_name": "DUPLICATE_SET_CANDIDATE",
                "status": "ENABLED",
                "evidence_provided": [
                    "evidence.similarity.structural",
                    "evidence.similarity.semantic",
                    "evidence.context.dependency_overlap.jaccard"
                ],
                "thresholds": {
                    "structural_min": 0.92,
                    "semantic_min": 0.85,
                    "dependency_overlap_min": 0.60
                }
            },
            "R_RED_003": {
                "rule_name": "SIMILAR_SCRIPT_CANDIDATE",
                "status": "ENABLED",
                "evidence_provided": [
                    "evidence.similarity.structural",
                    "evidence.similarity.semantic",
                    "evidence.context.dependency_overlap.jaccard",
                    "evidence.io.surface_overlap.jaccard"
                ],
                "thresholds": {
                    "structural_min": 0.92,
                    "semantic_min": 0.85,
                    "dependency_overlap_min": 0.60,
                    "io_surface_overlap_min": 0.50
                }
            },
            "R_OBS_002": {
                "rule_name": "OBSOLETE_CANDIDATE",
                "status": "PARTIAL_ENABLED",
                "evidence_provided": [
                    "evidence.redundancy.best_match.exists",
                    "evidence.redundancy.best_match.min_similarity",
                    "evidence.redundancy.best_match.min_confidence",
                    "evidence.redundancy.best_match.canonical_candidate"
                ],
                "note": "Provides redundancy criteria only; full rule requires graph analysis from other sources"
            }
        },
        "integration_artifacts": {
            "bridge_module": "integration_bridge.py",
            "bridge_class": "MappPyIntegrationBridge",
            "evidence_schema": "EVIDENCE_SCHEMA_EXTENDED.yaml",
            "rule_config": "py_identify_solution.yml"
        }
    },

    "doc_id_policy": {
        "description": "Stable identifier assignment policy for mapp_py system",
        "id_types": {
            "DOC_IDS": {
                "pattern": "DOC-[SUBSYSTEM]-[TOKEN]-[###]",
                "example": "DOC-MAPP-PY-SYSTEM-AI-001",
                "purpose": "Unique identifier for documentation artifacts",
                "registry": "data/id_registry.json"
            },
            "SPEC_IDS": {
                "pattern": "R-MAPP-PY-###",
                "example": "R-MAPP-PY-001",
                "purpose": "BDD specification stable identifiers",
                "registry": "specs/behaviors/*.yaml",
                "count": 9,
                "range": "R-MAPP-PY-001 through R-MAPP-PY-009"
            },
            "COMPONENT_IDS": {
                "pattern": "MAPP_PY_[TOKEN]",
                "examples": [
                    "MAPP_PY_PARSER",
                    "MAPP_PY_COMPARATOR",
                    "MAPP_PY_IO_ANALYZER",
                    "MAPP_PY_INTEGRATION_BRIDGE"
                ],
                "purpose": "Observable component identifiers for distributed tracing",
                "type_registry_entry": {
                    "id_type": "COMPONENT_ID",
                    "type_number": 49,
                    "registered_in": "ID_TYPE_REGISTRY.yaml"
                }
            },
            "WORK_IDS": {
                "pattern": "WORK-MAPP-PY-###[-PHASE-#]",
                "examples": [
                    "WORK-MAPP-PY-001",
                    "WORK-MAPP-PY-001-PHASE-7"
                ],
                "purpose": "Work tracking and commit linkage"
            }
        },
        "ssot_integration": {
            "patch_file": "0006_register_mapp_py_subsystem.patch.json",
            "patch_type": "RFC_6902_JSON_PATCH",
            "operations": "add",
            "target_file": "SSOT_CURRENT_APPROACH.json",
            "registration_complete": True
        }
    },

    "architecture": {
        "design_pattern": "PIPELINE_WITH_ORCHESTRATOR",
        "layers": [
            {
                "layer_name": "Input Layer",
                "components": ["cli.py", "integration_bridge.py"],
                "responsibility": "Accept file paths, parameters, and orchestrate analysis"
            },
            {
                "layer_name": "Orchestration Layer",
                "components": ["file_comparator.py"],
                "responsibility": "Coordinate multi-dimensional analysis and aggregate results"
            },
            {
                "layer_name": "Analysis Layer",
                "components": [
                    "python_ast_parser.py",
                    "component_extractor.py",
                    "structural_similarity.py",
                    "semantic_similarity.py",
                    "dependency_analyzer.py",
                    "io_surface_analyzer.py"
                ],
                "responsibility": "Perform specialized analysis on Python files"
            },
            {
                "layer_name": "Utility Layer",
                "components": ["component_id_generator.py"],
                "responsibility": "Support functions like ID generation"
            },
            {
                "layer_name": "Output Layer",
                "components": ["ComparisonResult", "IntegratedEvidence"],
                "responsibility": "Format and return evidence compatible with triage system"
            }
        ],
        "data_flow": {
            "primary_workflow": "file_paths -> parse -> extract -> analyze (4 dimensions) -> aggregate -> evidence",
            "workflow_steps": [
                {
                    "step": 1,
                    "action": "Parse Python files to AST",
                    "component": "python_ast_parser.py",
                    "input": "file paths",
                    "output": "astroid.Module AST trees + source code"
                },
                {
                    "step": 2,
                    "action": "Extract components",
                    "component": "component_extractor.py",
                    "input": "AST trees",
                    "output": "list of functions, classes, methods"
                },
                {
                    "step": 3,
                    "action": "Analyze 4 dimensions",
                    "components": [
                        "structural_similarity.py",
                        "semantic_similarity.py",
                        "dependency_analyzer.py",
                        "io_surface_analyzer.py"
                    ],
                    "input": "components, AST trees, source code",
                    "output": "4 similarity scores (0.0-1.0)"
                },
                {
                    "step": 4,
                    "action": "Aggregate and decide",
                    "component": "file_comparator.py",
                    "input": "4 dimension scores",
                    "output": "weighted aggregate score, decision (SIMILAR|REVIEW_NEEDED|DIFFERENT)"
                },
                {
                    "step": 5,
                    "action": "Generate evidence",
                    "component": "integration_bridge.py",
                    "input": "ComparisonResult",
                    "output": "IntegratedEvidence (schema-compliant JSON)"
                }
            ]
        },
        "comparison_dimensions": {
            "dimension_1": {
                "name": "structural_similarity",
                "weight": 0.35,
                "algorithm": "Jaccard index on AST node types",
                "implementation": "structural_similarity.py",
                "output_field": "evidence.similarity.structural",
                "range": "0.0 to 1.0"
            },
            "dimension_2": {
                "name": "semantic_similarity",
                "weight": 0.30,
                "algorithm": "TF-IDF vectorization + cosine similarity",
                "implementation": "semantic_similarity.py",
                "output_field": "evidence.similarity.semantic",
                "range": "0.0 to 1.0"
            },
            "dimension_3": {
                "name": "dependency_overlap",
                "weight": 0.20,
                "algorithm": "Jaccard index on import statements",
                "implementation": "dependency_analyzer.py",
                "output_field": "evidence.context.dependency_overlap.jaccard",
                "range": "0.0 to 1.0"
            },
            "dimension_4": {
                "name": "io_surface_overlap",
                "weight": 0.15,
                "algorithm": "Jaccard index on CLI args + environment variables",
                "implementation": "io_surface_analyzer.py",
                "output_field": "evidence.io.surface_overlap.jaccard",
                "range": "0.0 to 1.0"
            },
            "aggregation": {
                "formula": "weighted_sum",
                "computation": "sum(dimension_score * weight for all dimensions)",
                "output": "aggregate_score (0.0 to 1.0)"
            },
            "decision_thresholds": {
                "SIMILAR": "aggregate_score >= 0.75",
                "REVIEW_NEEDED": "0.40 <= aggregate_score < 0.75",
                "DIFFERENT": "aggregate_score < 0.40"
            }
        }
    }
}

# Save to file
output_path = Path(__file__).parent / "MAPP_PY_SYSTEM_DOCUMENTATION_AI.json"
output_path.write_text(json.dumps(documentation, indent=2), encoding='utf-8')
print(f"Generated: {output_path}")
print(f"Size: {len(json.dumps(documentation))} bytes")
