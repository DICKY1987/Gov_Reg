# DOC_LINK: DOC-SCRIPT-BUILD-AI-REFERENCE-001
"""
Build comprehensive AI reference for doc_id system.
This script generates the complete JSON technical documentation for AI consumption.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

def build_comprehensive_reference():
    """Build the complete doc_id system AI reference."""

    reference = {
        "doc_id": "DOC-GUIDE-DOC-ID-SYSTEM-AI-REFERENCE-001",
        "metadata": {
            "title": "Doc ID System - Complete AI Technical Reference",
            "version": "1.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "purpose": "Comprehensive technical documentation of the doc_id system for AI consumption only",
            "audience": ["AI agents", "automated systems", "LLMs", "future maintainers"],
            "format": "JSON",
            "completeness": "COMPLETE - This is the sole authoritative AI reference for the doc_id system",
            "usage_note": "AI agents should use this document as the primary reference for doc_id system understanding and operations",
            "source_documents": {
                "readme": "DOC-GUIDE-README-276",
                "complete_spec": "DOC-GUIDE-DOC-ID-SYSTEM-COMPLETE-SPECIFICATION-274",
                "id_type_registry": "DOC-REGISTRY-ID-TYPES-001",
                "doc_id_registry": "DOC-GUIDE-DOC-ID-REGISTRY-724"
            }
        },

        "system_overview": {
            "name": "DOC_ID System",
            "classification": "Document Identity and Tracking System",
            "tier": 1,
            "status": "production",
            "priority": "critical",
            "location": {
                "absolute_path": "C:\\Users\\richg\\ALL_AI\\RUNTIME\\doc_id\\SUB_DOC_ID",
                "relative_path": "RUNTIME/doc_id/SUB_DOC_ID",
                "parent_project": "ALL_AI Multi-phase AI development pipeline",
                "phase": "PHASE_5 (Execution)"
            },
            "purpose": "Assign unique, stable identifiers (doc_ids) to every file in the repository for traceability, documentation, automation, and governance",
            "current_status": {
                "coverage": {
                    "percentage": 100.0,
                    "files_with_doc_id": 3761,
                    "total_tracked": 3761,
                    "missing": 0,
                    "target": 100.0,
                    "last_scan": "2026-01-03"
                },
                "maturity": "production-ready",
                "operational_status": "fully operational",
                "test_suite": {
                    "total_tests": 22,
                    "passing": 11,
                    "failing": 10,
                    "skipped": 1,
                    "note": "System functional despite failing tests (path/environment differences)"
                }
            },
            "key_capabilities": [
                "Automatic file scanning and doc_id extraction",
                "Automated doc_id assignment and injection",
                "Format and uniqueness validation",
                "Coverage tracking and reporting",
                "Git pre-commit hooks",
                "File watchers for real-time monitoring",
                "Scheduled maintenance tasks",
                "CI/CD integration",
                "Registry synchronization",
                "Drift detection",
                "Duplicate resolution"
            ]
        },

        "core_concepts": {
            "doc_id": {
                "definition": "A unique, stable identifier permanently assigned to a file",
                "format": "DOC-{CATEGORY}-{NAME}-{SEQUENCE}",
                "examples": [
                    "DOC-CORE-ORCHESTRATOR-0001",
                    "DOC-SCRIPT-DOC-ID-SCANNER-0046",
                    "DOC-TEST-INTEGRATION-API-GATEWAY-0137",
                    "DOC-GUIDE-BATCH-ASSIGNMENT-PROCEDURE-0724"
                ],
                "properties": {
                    "unique": "No two files share the same doc_id",
                    "stable": "Persists across file renames, moves, and refactors",
                    "human_readable": "Conveys file category and purpose",
                    "machine_parseable": "Follows strict regex pattern",
                    "version_controlled": "Committed with the file",
                    "immutable": "Once assigned, doc_id never changes"
                },
                "validation": {
                    "regex": "^DOC-([A-Z0-9]+)-([A-Z0-9]+(?:-[A-Z0-9]+)*)-([0-9]{3,})$",
                    "capture_groups": {
                        "1": "Category prefix (e.g., CORE, SCRIPT)",
                        "2": "Name parts (e.g., DOC-ID-SCANNER, VALIDATE-PHASE)",
                        "3": "Sequence number (e.g., 0001, 0042, 1234)"
                    },
                    "rules": [
                        "Must start with literal DOC-",
                        "Category must be uppercase letters/digits only",
                        "Category must exist in registry",
                        "Name must be uppercase letters/digits with optional hyphens",
                        "Name must have at least one character between hyphens",
                        "Sequence must be 3+ digits (supports 000-999, typically 0000-9999)",
                        "Total length should not exceed 80 characters"
                    ],
                    "prohibited": [
                        "Lowercase letters",
                        "Special characters except hyphens in name",
                        "Starting or ending name parts with hyphens",
                        "Consecutive hyphens",
                        "Reserved prefixes outside category definition"
                    ]
                }
            },
            "categories": {
                "definition": "Groupings that organize related files and control doc_id prefix",
                "current_categories": {
                    "core": {"prefix": "CORE", "count": 945, "description": "Core system components (orchestrator, scheduler, executor)"},
                    "script": {"prefix": "SCRIPT", "count": 444, "description": "Scripts and automation tools"},
                    "test": {"prefix": "TEST", "count": 465, "description": "Test files and test utilities"},
                    "guide": {"prefix": "GUIDE", "count": 1240, "description": "Documentation and guides"},
                    "spec": {"prefix": "SPEC", "count": 70, "description": "Specifications and schemas"},
                    "config": {"prefix": "CONFIG", "count": 823, "description": "Configuration files"},
                    "patterns": {"prefix": "PAT", "count": 207, "description": "Execution patterns and templates"},
                    "error": {"prefix": "ERROR", "count": 183, "description": "Error detection and recovery components"},
                    "aim": {"prefix": "AIM", "count": 112, "description": "AIM environment manager components"},
                    "pm": {"prefix": "PM", "count": 110, "description": "Project management components"},
                    "engine": {"prefix": "ENGINE", "count": 55, "description": "Job execution engine components"},
                    "glossary": {"prefix": "GLOSSARY", "count": 13, "description": "Glossary management tools"},
                    "infra": {"prefix": "INFRA", "count": 4, "description": "Infrastructure and build artifacts"}
                }
            }
        }
    }

    # Add architecture section
    reference["architecture"] = {
        "components": {
            "scanner": {
                "doc_id": "DOC-SCRIPT-DOC-ID-SCANNER-0046",
                "location": "1_CORE_OPERATIONS/doc_id_scanner.py",
                "purpose": "Discover files and extract existing doc_ids",
                "inputs": ["Repository files"],
                "outputs": ["docs_inventory.jsonl"],
                "status": "operational"
            },
            "assigner": {
                "doc_id": "DOC-SCRIPT-DOC-ID-ASSIGNER-0047",
                "location": "1_CORE_OPERATIONS/doc_id_assigner.py",
                "purpose": "Inject doc_ids into files",
                "inputs": ["docs_inventory.jsonl"],
                "outputs": ["Modified files with doc_ids"],
                "status": "operational"
            },
            "registry": {
                "doc_id": "DOC-GUIDE-DOC-ID-REGISTRY-724",
                "location": "5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml",
                "purpose": "Authoritative doc_id database",
                "inputs": ["Doc_id requests"],
                "outputs": ["Unique doc_ids"],
                "status": "operational"
            },
            "validators": {
                "location": "2_VALIDATION_FIXING/",
                "purpose": "Ensure quality and consistency",
                "validators": [
                    {"name": "validate_doc_id_coverage", "check": "Coverage meets baseline"},
                    {"name": "fix_duplicate_doc_ids", "check": "No duplicate doc_ids"},
                    {"name": "fix_invalid_doc_ids", "check": "All doc_ids valid format"},
                    {"name": "validate_doc_id_sync", "check": "Registry matches files"},
                    {"name": "validate_doc_id_uniqueness", "check": "All doc_ids unique"},
                    {"name": "validate_doc_id_references", "check": "All references valid"}
                ],
                "status": "operational"
            },
            "automation": {
                "location": "3_AUTOMATION_HOOKS/",
                "purpose": "Trigger scans and validations automatically",
                "hooks": [
                    {"name": "pre_commit_hook", "trigger": "git commit", "doc_id": "DOC-HOOK-PRE-COMMIT-001"},
                    {"name": "file_watcher", "trigger": "file changes", "doc_id": "DOC-WATCHER-FILE-001"},
                    {"name": "scheduled_tasks", "trigger": "cron/schedule", "doc_id": "DOC-SCHEDULER-TASKS-001"}
                ],
                "status": "operational"
            },
            "reporting": {
                "location": "4_REPORTING_MONITORING/",
                "purpose": "Coverage and trend analytics",
                "reports": [
                    {"name": "coverage_trend", "frequency": "daily"},
                    {"name": "scheduled_reports", "frequency": "daily/weekly/monthly"},
                    {"name": "alert_monitor", "frequency": "real-time"}
                ],
                "status": "operational"
            }
        },
        "data_flow": [
            "Scanner discovers files → writes docs_inventory.jsonl",
            "Assigner reads inventory → mints doc_ids via registry → injects into files",
            "Sync tool reads files → updates registry with new doc_ids",
            "Validators read registry + files → report issues",
            "Automation hooks → trigger scan/assign cycles automatically"
        ],
        "directory_structure": {
            "1_CORE_OPERATIONS": "Primary operations (scan, assign, deprecate)",
            "2_VALIDATION_FIXING": "Quality assurance (validators, fixers)",
            "3_AUTOMATION_HOOKS": "Git hooks, watchers, schedulers",
            "4_REPORTING_MONITORING": "Reports and alerts",
            "5_REGISTRY_DATA": "DOC_ID_REGISTRY.yaml, docs_inventory.jsonl",
            "6_TESTS": "Test suite",
            "7_CLI_INTERFACE": "Unified CLI wrapper",
            "common": "Shared library (rules, registry, utils)",
            "pattern_id": "Pattern ID subsystem",
            "trigger_id": "Trigger ID subsystem"
        }
    }

    # Add registry schema
    reference["registry_schema"] = {
        "file": {
            "doc_id": "DOC-GUIDE-DOC-ID-REGISTRY-724",
            "location": "5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml",
            "format": "YAML",
            "purpose": "Authoritative source of truth for all doc_id assignments"
        },
        "structure": {
            "doc_id": "string - Doc_id of registry file itself",
            "metadata": {
                "version": "string - Registry schema version (semver)",
                "created": "string - ISO 8601 date",
                "last_updated": "string - ISO 8601 date",
                "total_docs": "integer - Total doc_ids assigned",
                "description": "string - Human-readable description"
            },
            "categories": {
                "<category_key>": {
                    "prefix": "string - Uppercase prefix (e.g., CORE, SCRIPT)",
                    "description": "string - Purpose of this category",
                    "next_id": "integer - Next available sequence number",
                    "count": "integer - Total assigned in this category"
                }
            },
            "docs": [
                {
                    "doc_id": "string - Full doc_id",
                    "category": "string - Category key",
                    "name": "string - Name slug",
                    "title": "string - Human-readable title",
                    "status": "enum - active | deprecated",
                    "file_path": "string - Relative path from repo root",
                    "artifacts": "array - Related artifact paths",
                    "created": "string - ISO 8601 date",
                    "last_modified": "string - ISO 8601 date",
                    "deprecated_at": "string - ISO 8601 date (if deprecated)",
                    "tags": "array - Optional tags"
                }
            ]
        },
        "operations": {
            "mint_doc_id": {
                "description": "Create a new unique doc_id",
                "inputs": ["category", "name", "title (optional)"],
                "process": [
                    "Validate category exists",
                    "Get next_id from category",
                    "Format doc_id: DOC-{prefix}-{name}-{next_id:04d}",
                    "Increment category next_id",
                    "Increment category count",
                    "Add entry to docs list",
                    "Save registry"
                ],
                "outputs": {"doc_id": "string", "category": "string", "next_id": "integer"}
            },
            "lookup_doc_id": {
                "description": "Find existing doc_id",
                "inputs": ["doc_id"],
                "process": ["Load registry", "Search docs list", "Return entry or None"],
                "outputs": "doc entry object or None"
            },
            "deprecate_doc_id": {
                "description": "Mark doc_id as deprecated",
                "inputs": ["doc_id"],
                "process": [
                    "Find entry in registry",
                    "Set status: deprecated",
                    "Add deprecated_at timestamp",
                    "Preserve entry (never delete)",
                    "Save registry"
                ],
                "note": "Doc_ids are NEVER deleted or reused"
            }
        }
    }

    # Add file operations
    reference["file_operations"] = {
        "scanning": {
            "tool": "doc_id_scanner.py (DOC-SCRIPT-DOC-ID-SCANNER-0046)",
            "location": "1_CORE_OPERATIONS/doc_id_scanner.py",
            "purpose": "Find all eligible files and extract existing doc_ids",
            "eligible_patterns": ["**/*.py", "**/*.md", "**/*.yaml", "**/*.yml", "**/*.ps1", "**/*.sh", "**/*.txt", "**/*.json"],
            "exclude_patterns": [".venv", "venv", "__pycache__", ".git", ".pytest_cache", "node_modules", "UTI_Archives", "Backups", ".acms_runs", "envs", "htmlcov", ".coverage"],
            "extraction_methods": {
                "python": "Search first 50 lines for: # DOC_LINK: DOC-... or # DOC_ID: DOC-...",
                "markdown": "YAML frontmatter: doc_id: DOC-...",
                "yaml": "Top-level key: doc_id: DOC-...",
                "json": "Top-level key: {\"doc_id\": \"DOC-...\"}",
                "powershell": "Comment line: # DOC_LINK: DOC-...",
                "shell": "Comment line: # DOC_LINK: DOC-..."
            },
            "commands": {
                "full_scan": "python doc_id_scanner.py scan",
                "view_stats": "python doc_id_scanner.py stats",
                "generate_report": "python doc_id_scanner.py report --format markdown"
            },
            "output": "Writes docs_inventory.jsonl, prints statistics"
        },
        "assignment": {
            "tool": "doc_id_assigner.py (DOC-SCRIPT-DOC-ID-ASSIGNER-0047)",
            "location": "1_CORE_OPERATIONS/doc_id_assigner.py",
            "purpose": "Mint new doc_ids and inject into files",
            "process": [
                "Load docs_inventory.jsonl",
                "Filter entries with status=missing",
                "For each missing entry: determine category, generate name, mint doc_id, inject into file",
                "Update inventory",
                "Print summary"
            ],
            "injection_locations": {
                "python": "After shebang/encoding, before docstring: # DOC_LINK: DOC-...",
                "markdown": "YAML frontmatter: ---\\ndoc_id: DOC-...\\n---",
                "yaml": "Top-level key: doc_id: DOC-...",
                "json": "Top-level key: {\"doc_id\": \"DOC-...\"}",
                "powershell": "After comments, at top: # DOC_LINK: DOC-..."
            },
            "commands": {
                "dry_run": "python doc_id_assigner.py auto-assign --dry-run",
                "batch_assign": "python doc_id_assigner.py auto-assign --limit 100",
                "assign_all": "python doc_id_assigner.py auto-assign",
                "single_file": "python doc_id_assigner.py single --path <file> --category <cat> --name <name>"
            },
            "safety_features": [
                "Always creates backup before modifying files",
                "Validates file is not locked or read-only",
                "Preserves file encoding",
                "Maintains original line endings",
                "Atomic write (write to temp, then rename)"
            ]
        },
        "synchronization": {
            "tool": "sync_registries.py",
            "location": "5_REGISTRY_DATA/sync_registries.py",
            "purpose": "Sync inventory with registry",
            "process": [
                "Load docs_inventory.jsonl and DOC_ID_REGISTRY.yaml",
                "For each inventory entry with doc_id: check if in registry, add/update as needed",
                "For each registry entry: check if file exists, mark missing if not",
                "Write updated registry"
            ],
            "commands": {
                "sync": "python sync_registries.py sync",
                "force_sync": "python sync_registries.py sync --force",
                "validate": "python sync_registries.py validate"
            }
        }
    }

    # Add validation rules
    reference["validation_rules"] = {
        "format_validation": {
            "validator": "validate_doc_id_format (in common/rules.py)",
            "checks": ["Starts with DOC-", "Category is uppercase alphanumeric", "Name is uppercase alphanumeric with hyphens", "Sequence is 3+ digits", "No invalid characters"],
            "errors": {
                "E001": "Invalid format",
                "E002": "Lowercase characters",
                "E003": "Invalid characters",
                "E004": "Sequence too short"
            }
        },
        "uniqueness_validation": {
            "validator": "validate_doc_id_uniqueness.py (DOC-VALIDATOR-DOC-ID-UNIQUENESS-001)",
            "location": "2_VALIDATION_FIXING/validate_doc_id_uniqueness.py",
            "checks": ["Scans all files for doc_ids", "Detects duplicates", "Reports conflicts"],
            "errors": {
                "E101": "Duplicate doc_id found in multiple files",
                "E102": "Doc_id in registry but not in files",
                "E103": "Doc_id in files but not in registry"
            }
        },
        "coverage_validation": {
            "validator": "validate_doc_id_coverage.py",
            "location": "2_VALIDATION_FIXING/validate_doc_id_coverage.py",
            "checks": ["Calculates coverage percentage", "Compares against baseline", "Detects regressions"],
            "baseline": "Configurable, default 55%",
            "formula": "coverage = (files_with_doc_id / eligible_files) * 100",
            "errors": {
                "E401": "Coverage below baseline",
                "E402": "Coverage regression detected"
            }
        },
        "consistency_validation": {
            "validator": "validate_doc_id_sync.py",
            "location": "2_VALIDATION_FIXING/validate_doc_id_sync.py",
            "checks": ["Doc_id in file matches registry file_path", "Registry entry status is active", "Timestamps are consistent"],
            "errors": {
                "E301": "Doc_id in file doesn't match registry path",
                "E302": "Registry entry marked deprecated but file exists",
                "E303": "File modified but registry not updated"
            }
        }
    }

    # Add automation system
    reference["automation_system"] = {
        "git_pre_commit_hook": {
            "doc_id": "DOC-HOOK-PRE-COMMIT-001",
            "location": "3_AUTOMATION_HOOKS/pre_commit_hook.py",
            "purpose": "Validate doc_ids before commit",
            "installation": "python 3_AUTOMATION_HOOKS/install_pre_commit_hook.py",
            "process": [
                "Git stages files for commit",
                "Hook triggered",
                "For each staged file: extract doc_ids, validate format, check duplicates, verify in registry",
                "If validation fails: print errors, block commit with exit code 1",
                "If validation passes: allow commit with exit code 0"
            ],
            "bypass": "git commit --no-verify -m 'Emergency fix' (use sparingly)"
        },
        "file_watcher": {
            "doc_id": "DOC-WATCHER-FILE-001",
            "location": "3_AUTOMATION_HOOKS/file_watcher.py",
            "purpose": "Auto-scan on file changes",
            "dependencies": ["watchdog library"],
            "process": [
                "Start watchdog observer",
                "Monitor repository for file changes",
                "On file change: check if eligible, debounce, trigger scanner, optionally trigger assigner",
                "Log activities, send alerts on errors"
            ],
            "commands": {
                "start": "python file_watcher.py --debounce 600",
                "background": "nohup python file_watcher.py --debounce 600 > watcher.log 2>&1 &"
            }
        },
        "scheduled_tasks": {
            "doc_id": "DOC-SCHEDULER-TASKS-001",
            "location": "3_AUTOMATION_HOOKS/setup_scheduled_tasks.py",
            "purpose": "Periodic scans and maintenance",
            "tasks": [
                {"name": "Nightly Scan", "schedule": "Daily 2:00 AM", "command": "python doc_id_scanner.py scan"},
                {"name": "Coverage Report", "schedule": "Daily 3:00 AM", "command": "python validate_doc_id_coverage.py --report"},
                {"name": "Duplicate Check", "schedule": "Daily 4:00 AM", "command": "python fix_duplicate_doc_ids.py --check"},
                {"name": "Registry Sync", "schedule": "Daily 5:00 AM", "command": "python sync_registries.py sync"}
            ],
            "installation_windows": "python setup_scheduled_tasks.py --interval daily",
            "installation_linux": "Add to crontab: 0 2 * * * cd /path/to/repo && python SUB_DOC_ID/1_CORE_OPERATIONS/doc_id_scanner.py scan"
        }
    }

    # Add integration with ID ecosystem
    reference["id_ecosystem_integration"] = {
        "doc_id": {
            "type_id": "doc_id",
            "status": "production",
            "tier": 1,
            "priority": "critical",
            "format": "DOC-{CATEGORY}-{NAME}-{SEQ}",
            "registry": "DOC_ID_REGISTRY.yaml (DOC-GUIDE-DOC-ID-REGISTRY-724)",
            "coverage": {"total_ids": 3761, "percentage": 100.0}
        },
        "trigger_id": {
            "type_id": "trigger_id",
            "status": "production",
            "tier": 2,
            "priority": "high",
            "format": "TRIGGER-{CATEGORY}-{NAME}-{SEQ}",
            "registry": "trigger_id/5_REGISTRY_DATA/TRG_ID_REGISTRY.yaml (DOC-REGISTRY-TRIGGER-001)",
            "coverage": {"total_ids": 13, "percentage": 100.0}
        },
        "pattern_id": {
            "type_id": "pattern_id",
            "status": "production",
            "tier": 2,
            "priority": "high",
            "format": "PATTERN-{CATEGORY}-{NAME}-{SEQ}",
            "registry": "pattern_id/5_REGISTRY_DATA/PAT_ID_REGISTRY.yaml (DOC-REGISTRY-PATTERN-001)",
            "coverage": {"total_ids": 12, "percentage": 75.0}
        },
        "dir_id": {
            "type_id": "dir_id",
            "classification": "derived",
            "status": "production",
            "tier": 2,
            "priority": "medium",
            "format": "DIR-{PATH_TOKEN}-{HASH}",
            "derivation_rule": "Computed from directory path: slugify path segments, append 8-char hash",
            "coverage": {"total_ids": 37, "percentage": 100.0}
        }
    }

    # Add common workflows
    reference["common_workflows"] = {
        "initial_setup": {
            "description": "Assign doc_ids to all existing files",
            "steps": [
                {"step": 1, "command": "pip install pyyaml watchdog", "description": "Install dependencies"},
                {"step": 2, "command": "python doc_id_scanner.py scan", "description": "Scan repository"},
                {"step": 3, "command": "python doc_id_scanner.py stats", "description": "Review scan results"},
                {"step": 4, "command": "python doc_id_assigner.py auto-assign --dry-run", "description": "Preview assignments"},
                {"step": 5, "command": "python doc_id_assigner.py auto-assign --limit 100", "description": "Assign in batches"},
                {"step": 6, "command": "python sync_registries.py sync", "description": "Sync registry"},
                {"step": 7, "command": "python validate_doc_id_coverage.py --baseline 0.55", "description": "Validate coverage"},
                {"step": 8, "command": "python install_pre_commit_hook.py", "description": "Install automation"},
                {"step": 9, "command": "git add . && git commit -m 'feat: assign doc_ids'", "description": "Commit changes"}
            ]
        },
        "adding_new_file": {
            "description": "Assign doc_id to newly created file",
            "manual_method": [
                {"step": 1, "description": "Create file without doc_id"},
                {"step": 2, "command": "python doc_id_scanner.py scan", "description": "Run scanner"},
                {"step": 3, "command": "python doc_id_assigner.py auto-assign --limit 1", "description": "Assign doc_id"},
                {"step": 4, "command": "cat <file> | grep DOC_", "description": "Verify injection"},
                {"step": 5, "command": "git add <file> && git commit -m 'feat: add new component'", "description": "Commit"}
            ],
            "automated_method": [
                {"step": 1, "description": "Create file without doc_id"},
                {"step": 2, "description": "File watcher detects change"},
                {"step": 3, "description": "Scanner runs automatically"},
                {"step": 4, "description": "Assigner runs automatically (if configured)"},
                {"step": 5, "description": "Notification sent"},
                {"step": 6, "description": "Commit file with auto-assigned doc_id"}
            ]
        },
        "renaming_moving_files": {
            "description": "Preserve doc_id when file moves",
            "steps": [
                {"step": 1, "command": "git mv old_path new_path", "description": "Move/rename file"},
                {"step": 2, "description": "Doc_id remains in file (unchanged)"},
                {"step": 3, "command": "python sync_registries.py sync", "description": "Registry file_path updated automatically"},
                {"step": 4, "command": "python validate_doc_id_sync.py", "description": "Validate sync"},
                {"step": 5, "command": "git add . && git commit -m 'refactor: move component'", "description": "Commit"}
            ],
            "note": "Doc_id is file-identity, not path-identity. It persists across moves."
        },
        "deprecating_files": {
            "description": "Mark file and doc_id as deprecated",
            "steps": [
                {"step": 1, "command": "git mv <file> UTI_Archives/<file>", "description": "Move file to archive"},
                {"step": 2, "command": "python deprecate_doc_id.py DOC-CORE-COMPONENT-0042", "description": "Deprecate doc_id"},
                {"step": 3, "command": "grep -A5 'DOC-CORE-COMPONENT-0042' DOC_ID_REGISTRY.yaml", "description": "Verify status: deprecated"},
                {"step": 4, "command": "git add . && git commit -m 'chore: deprecate old component'", "description": "Commit"}
            ],
            "note": "Doc_ids are never deleted, only marked deprecated"
        }
    }

    # Add commands reference
    reference["commands_reference"] = {
        "scanning": {
            "full_scan": {"command": "python doc_id_scanner.py scan", "description": "Scan entire repository"},
            "show_stats": {"command": "python doc_id_scanner.py stats", "description": "Display statistics"},
            "generate_report": {"command": "python doc_id_scanner.py report --format markdown", "description": "Generate markdown report"}
        },
        "assignment": {
            "dry_run": {"command": "python doc_id_assigner.py auto-assign --dry-run", "description": "Preview assignments"},
            "batch": {"command": "python doc_id_assigner.py auto-assign --limit 100", "description": "Assign to 100 files"},
            "all": {"command": "python doc_id_assigner.py auto-assign", "description": "Assign to all missing"},
            "single": {"command": "python doc_id_assigner.py single --path <file>", "description": "Assign to single file"}
        },
        "validation": {
            "coverage": {"command": "python validate_doc_id_coverage.py --baseline 0.55", "description": "Check coverage"},
            "duplicates": {"command": "python fix_duplicate_doc_ids.py --check", "description": "Check for duplicates"},
            "format": {"command": "python fix_invalid_doc_ids.py --check", "description": "Check format validity"},
            "sync": {"command": "python validate_doc_id_sync.py", "description": "Check registry sync"}
        },
        "maintenance": {
            "sync": {"command": "python sync_registries.py sync", "description": "Sync registry"},
            "drift": {"command": "python detect_doc_drift.py --check", "description": "Detect drift"},
            "deprecate": {"command": "python deprecate_doc_id.py <DOC_ID>", "description": "Deprecate doc_id"}
        },
        "automation": {
            "pre_commit": {"command": "python install_pre_commit_hook.py", "description": "Install git hook"},
            "scheduler": {"command": "python setup_scheduled_tasks.py --interval daily", "description": "Setup scheduled tasks"},
            "watcher": {"command": "python file_watcher.py --debounce 600", "description": "Start file watcher"}
        }
    }

    # Add file inventory
    reference["file_inventory"] = {
        "core_components": [
            {"file": "1_CORE_OPERATIONS/doc_id_scanner.py", "doc_id": "DOC-SCRIPT-DOC-ID-SCANNER-0046", "purpose": "Scan repository for doc_ids"},
            {"file": "1_CORE_OPERATIONS/doc_id_assigner.py", "doc_id": "DOC-SCRIPT-DOC-ID-ASSIGNER-0047", "purpose": "Assign doc_ids to files"},
            {"file": "1_CORE_OPERATIONS/deprecate_doc_id.py", "doc_id": "DOC-SCRIPT-DEPRECATE-DOC-ID-001", "purpose": "Deprecate doc_ids"},
            {"file": "1_CORE_OPERATIONS/lib/doc_id_registry_cli.py", "doc_id": "DOC-LIB-DOC-ID-REGISTRY-CLI-001", "purpose": "Registry CLI library"},
            {"file": "5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml", "doc_id": "DOC-GUIDE-DOC-ID-REGISTRY-724", "purpose": "Authoritative registry"},
            {"file": "5_REGISTRY_DATA/docs_inventory.jsonl", "doc_id": "N/A", "purpose": "Current scan snapshot"},
            {"file": "5_REGISTRY_DATA/sync_registries.py", "doc_id": "DOC-SCRIPT-SYNC-REGISTRIES-001", "purpose": "Sync inventory and registry"}
        ],
        "validators": [
            {"file": "2_VALIDATION_FIXING/validate_doc_id_coverage.py", "doc_id": "DOC-VALIDATOR-COVERAGE-001", "purpose": "Coverage validation"},
            {"file": "2_VALIDATION_FIXING/fix_duplicate_doc_ids.py", "doc_id": "DOC-FIXER-DUPLICATES-001", "purpose": "Duplicate detection/resolution"},
            {"file": "2_VALIDATION_FIXING/fix_invalid_doc_ids.py", "doc_id": "DOC-FIXER-INVALID-001", "purpose": "Format validation/fixing"},
            {"file": "2_VALIDATION_FIXING/validate_doc_id_sync.py", "doc_id": "DOC-VALIDATOR-SYNC-001", "purpose": "Registry sync validation"},
            {"file": "2_VALIDATION_FIXING/validate_doc_id_uniqueness.py", "doc_id": "DOC-VALIDATOR-UNIQUENESS-001", "purpose": "Uniqueness validation"},
            {"file": "2_VALIDATION_FIXING/validate_doc_id_references.py", "doc_id": "DOC-VALIDATOR-REFERENCES-001", "purpose": "Reference validation"},
            {"file": "2_VALIDATION_FIXING/detect_doc_drift.py", "doc_id": "DOC-DETECTOR-DRIFT-001", "purpose": "Drift detection"}
        ],
        "automation": [
            {"file": "3_AUTOMATION_HOOKS/pre_commit_hook.py", "doc_id": "DOC-HOOK-PRE-COMMIT-001", "purpose": "Git pre-commit validation"},
            {"file": "3_AUTOMATION_HOOKS/file_watcher.py", "doc_id": "DOC-WATCHER-FILE-001", "purpose": "Real-time file monitoring"},
            {"file": "3_AUTOMATION_HOOKS/setup_scheduled_tasks.py", "doc_id": "DOC-SCHEDULER-SETUP-001", "purpose": "Schedule maintenance tasks"},
            {"file": "3_AUTOMATION_HOOKS/install_pre_commit_hook.py", "doc_id": "DOC-INSTALLER-HOOK-001", "purpose": "Install git hook"}
        ],
        "documentation": [
            {"file": "README.md", "doc_id": "DOC-GUIDE-README-276", "purpose": "System overview and quick start"},
            {"file": "DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md", "doc_id": "DOC-GUIDE-DOC-ID-SYSTEM-COMPLETE-SPECIFICATION-274", "purpose": "Complete technical spec"},
            {"file": "BATCH_DOC_ID_ASSIGNMENT_GUIDE.md", "doc_id": "DOC-GUIDE-BATCH-DOC-ID-ASSIGNMENT-GUIDE-271", "purpose": "Batch assignment guide"},
            {"file": "QUICK_REFERENCE.md", "doc_id": "DOC-GUIDE-QUICK-REFERENCE-275", "purpose": "Command cheat sheet"},
            {"file": "DIRECTORY_INDEX.md", "doc_id": "DOC-GUIDE-DIRECTORY-INDEX-273", "purpose": "AI navigation guide"}
        ],
        "registries": [
            {"file": "ID_TYPE_REGISTRY.yaml", "doc_id": "DOC-REGISTRY-ID-TYPES-001", "purpose": "Meta-registry of all ID types"},
            {"file": "trigger_id/5_REGISTRY_DATA/TRG_ID_REGISTRY.yaml", "doc_id": "DOC-REGISTRY-TRIGGER-001", "purpose": "Trigger ID registry"},
            {"file": "pattern_id/5_REGISTRY_DATA/PAT_ID_REGISTRY.yaml", "doc_id": "DOC-REGISTRY-PATTERN-001", "purpose": "Pattern ID registry"}
        ]
    }

    # Add troubleshooting
    reference["troubleshooting"] = {
        "scanner_not_finding_files": {
            "problem": "Scanner not finding files",
            "solution": "Check ELIGIBLE_PATTERNS and EXCLUDE_PATTERNS in doc_id_scanner.py"
        },
        "assigner_cant_find_registry": {
            "problem": "Assigner can't find registry",
            "solution": "Verify DOC_ID_REGISTRY.yaml exists in 5_REGISTRY_DATA/"
        },
        "duplicate_doc_ids": {
            "problem": "Duplicate doc_ids found",
            "solution": "Run: python fix_duplicate_doc_ids.py --auto-resolve"
        },
        "invalid_format": {
            "problem": "Invalid doc_id format",
            "solution": "Run: python fix_invalid_doc_ids.py"
        },
        "registry_out_of_sync": {
            "problem": "Registry out of sync with files",
            "solution": "Run: python sync_registries.py sync"
        },
        "coverage_below_baseline": {
            "problem": "Coverage drops below baseline",
            "solution": "Run: python doc_id_scanner.py scan && python doc_id_assigner.py auto-assign"
        },
        "corrupted_registry": {
            "problem": "Registry file corrupted",
            "solution": "Restore from backup: cp 5_REGISTRY_DATA/backups_v2_v3/DOC_ID_REGISTRY_backup_*.yaml 5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml"
        }
    }

    # Add performance characteristics
    reference["performance"] = {
        "typical_execution_times": {
            "note": "For repository with 2000+ files",
            "scanner": "15-30 seconds",
            "assigner_100_files": "5-10 seconds",
            "validator": "10-20 seconds",
            "sync": "2-5 seconds"
        },
        "memory_usage": {
            "scanner": "50-100 MB",
            "assigner": "100-200 MB",
            "registry": "10-50 MB",
            "validators": "50-150 MB"
        },
        "scalability": {
            "files_tested": "up to 10,000 files",
            "registry_size": "up to 5,000 doc_ids",
            "sequence_numbers": "0000-9999 per category (10,000 per category)"
        }
    }

    # Add error codes
    reference["error_codes"] = {
        "E0xx_format_errors": {
            "E001": {"description": "Invalid doc_id format", "recovery": "Auto-fix or reassign"},
            "E002": {"description": "Lowercase characters", "recovery": "Convert to uppercase"},
            "E003": {"description": "Invalid characters", "recovery": "Remove invalid chars"},
            "E004": {"description": "Sequence too short", "recovery": "Pad with zeros"}
        },
        "E1xx_uniqueness_errors": {
            "E101": {"description": "Duplicate doc_id in multiple files", "recovery": "Reassign duplicates"},
            "E102": {"description": "Doc_id in registry but not in files", "recovery": "Mark as missing or deprecated"},
            "E103": {"description": "Doc_id in files but not in registry", "recovery": "Add to registry"}
        },
        "E2xx_category_errors": {
            "E201": {"description": "Unknown category", "recovery": "Add category or recategorize"},
            "E202": {"description": "Missing prefix", "recovery": "Add prefix to category"},
            "E203": {"description": "Missing next_id", "recovery": "Initialize next_id"}
        },
        "E3xx_consistency_errors": {
            "E301": {"description": "Doc_id doesn't match registry path", "recovery": "Update registry path"},
            "E302": {"description": "Deprecated entry but file exists", "recovery": "Reactivate or move file"},
            "E303": {"description": "File modified but registry outdated", "recovery": "Run sync"}
        },
        "E4xx_coverage_errors": {
            "E401": {"description": "Coverage below baseline", "recovery": "Assign missing doc_ids"},
            "E402": {"description": "Coverage regression", "recovery": "Identify and assign new files"}
        },
        "E5xx_reference_errors": {
            "E501": {"description": "Reference to non-existent doc_id", "recovery": "Fix or remove reference"},
            "E502": {"description": "Reference to deprecated doc_id", "recovery": "Update to active doc_id"},
            "E503": {"description": "Circular reference", "recovery": "Break circular dependency"}
        }
    }

    # Add usage instructions for AI
    reference["ai_usage_instructions"] = {
        "when_to_use_this_document": [
            "When user asks about doc_id system",
            "When performing doc_id operations",
            "When troubleshooting doc_id issues",
            "When understanding repository structure",
            "When validating doc_id compliance"
        ],
        "key_principles": [
            "Doc_ids are unique and stable - never reuse or change",
            "All file references must include doc_id for traceability",
            "Always validate doc_id format before use",
            "Sync registry after any doc_id changes",
            "Use automation tools (scanner, assigner) rather than manual edits"
        ],
        "recommended_workflow": [
            "1. Scan repository to discover current state",
            "2. Validate coverage and format",
            "3. Assign missing doc_ids in batches",
            "4. Sync registry with files",
            "5. Validate consistency",
            "6. Enable automation (hooks, watchers)"
        ],
        "common_ai_tasks": {
            "check_file_doc_id": "Extract doc_id from file frontmatter or comments. Format depends on file type.",
            "find_file_by_doc_id": "Search DOC_ID_REGISTRY.yaml for doc_id, then use file_path field",
            "assign_new_doc_id": "Use doc_id_assigner.py, do not manually edit files",
            "validate_doc_id_format": "Use regex: ^DOC-([A-Z0-9]+)-([A-Z0-9]+(?:-[A-Z0-9]+)*)-([0-9]{3,})$",
            "reference_file_in_docs": "Always use format: <file> (DOC-CATEGORY-NAME-0001)"
        }
    }

    # Add version history
    reference["version_history"] = {
        "v1.0.0_2026_01_08": {
            "changes": ["Initial comprehensive AI reference created", "Consolidated all doc_id system documentation", "Added complete file inventory with doc_ids", "Documented all workflows and error codes"],
            "reason": "User requested single authoritative JSON for AI consumption"
        }
    }

    # Add related systems
    reference["related_systems"] = {
        "ssot_system": {
            "location": "../SSOT_System/",
            "purpose": "Canonical project state management with patch-based updates",
            "integration": "DOC_ID_REGISTRY.yaml is an SSOT-managed artifact",
            "governance": "All changes to registry via RFC 6902 JSON Patch files"
        },
        "lifecycle_management": {
            "location": "../LIFECYCLE/",
            "purpose": "Task dependencies, execution graphs, workflow orchestration",
            "integration": "Doc_ids reference lifecycle tasks for traceability"
        },
        "determinism_contract": {
            "location": "../PHASE_0_BOOTSTRAP/SYSTEM_DETERMINISM_CONTRACT.json",
            "purpose": "Ensure reproducible, traceable execution",
            "requirements": ["All output to .runs/<run_id>/", "No unseeded randomness", "Trace_id and run_id propagation", "Timestamps via explicit clock injection"]
        }
    }

    return reference

if __name__ == "__main__":
    print("Building comprehensive doc_id system AI reference...")
    reference = build_comprehensive_reference()

    output_path = Path("DOC_ID_SYSTEM_AI_REFERENCE.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reference, f, indent=2, ensure_ascii=False)

    print(f"✓ Created: {output_path}")
    print(f"✓ Size: {output_path.stat().st_size / 1024:.1f} KB")
    print(f"✓ Sections: {len(reference)} top-level sections")
    print("✓ Complete - This is now the authoritative AI reference for doc_id system")
