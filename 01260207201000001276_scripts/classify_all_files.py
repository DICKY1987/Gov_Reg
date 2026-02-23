import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SECTIONS = [
    "Core Governance Engine",
    "ID Management System",
    "Schemas & Contracts",
    "Scripts & Automation",
    "Validation & Testing",
    "Documentation",
    "Configuration & Policies",
    "Evidence & Gates",
    "GEU (Governance Enforcement Units)",
    "File Watcher & Path Abstraction",
    "Planning & Execution",
    "State Management",
    "CI/CD & Integration",
    "Backups & Archives",
    "Templates",
    "Monitoring & Training",
    "Patches & Migrations",
    "Deployment & Operations",
    "Unclassified",
]

SECTION_ALIASES = {
    "core governance engine": "Core Governance Engine",
    "core governance": "Core Governance Engine",
    "id management system": "ID Management System",
    "id management": "ID Management System",
    "schemas & contracts": "Schemas & Contracts",
    "schemas": "Schemas & Contracts",
    "scripts & automation": "Scripts & Automation",
    "scripts": "Scripts & Automation",
    "validation & testing": "Validation & Testing",
    "tests": "Validation & Testing",
    "validators": "Validation & Testing",
    "documentation": "Documentation",
    "configuration & policies": "Configuration & Policies",
    "configs": "Configuration & Policies",
    "config": "Configuration & Policies",
    "evidence & gates": "Evidence & Gates",
    "evidence": "Evidence & Gates",
    "geu (governance enforcement units)": "GEU (Governance Enforcement Units)",
    "geu": "GEU (Governance Enforcement Units)",
    "file watcher & path abstraction": "File Watcher & Path Abstraction",
    "path/watcher": "File Watcher & Path Abstraction",
    "planning & execution": "Planning & Execution",
    "planning": "Planning & Execution",
    "state management": "State Management",
    "state": "State Management",
    "ci/cd & integration": "CI/CD & Integration",
    "ci/cd": "CI/CD & Integration",
    "backups & archives": "Backups & Archives",
    "backups": "Backups & Archives",
    "templates": "Templates",
    "monitoring & training": "Monitoring & Training",
    "monitoring": "Monitoring & Training",
    "patches & migrations": "Patches & Migrations",
    "patches": "Patches & Migrations",
    "deployment & operations": "Deployment & Operations",
    "deployment": "Deployment & Operations",
    "unclassified": "Unclassified",
}

LAYER_SECTION_MAP = {
    "AUTOMATION": "Scripts & Automation",
    "CORE": "Core Governance Engine",
    "DOCUMENTATION": "Documentation",
    "EVIDENCE": "Evidence & Gates",
    "GOVERNANCE": "Configuration & Policies",
    "TESTING": "Validation & Testing",
    "VALIDATION": "Validation & Testing",
}

ARTIFACT_KIND_SECTION_MAP = {
    "MARKDOWN": "Documentation",
    "POWERSHELL": "Scripts & Automation",
    "TEXT": "Documentation",
}

GOVERNANCE_DOMAIN_SECTION_MAP = {
    "CONFIGS": "Configuration & Policies",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
}

TEXT_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".ps1", ".sh"}


def normalize_section_name(value):
    if not value:
        return None
    return SECTION_ALIASES.get(value.strip().lower())


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted([d for d in dirnames if d not in SKIP_DIRS])
        for filename in sorted(filenames):
            yield Path(dirpath) / filename


def normalize_registry_path(raw_path, repo_root):
    if not raw_path:
        return None
    path_text = raw_path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", path_text):
        try:
            return Path(path_text).resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return None
    root_name = repo_root.name
    if path_text.startswith(root_name + "/"):
        path_text = path_text[len(root_name) + 1 :]
    if path_text.startswith("./"):
        path_text = path_text[2:]
    return path_text


def load_registry_index(registry_path, repo_root):
    if not registry_path or not registry_path.exists():
        return {}
    with registry_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    records = data.get("files") or data.get("entries") or []
    index = {}
    for entry in records:
        rel_path = normalize_registry_path(entry.get("relative_path"), repo_root)
        if not rel_path:
            continue
        index[rel_path] = entry
    return index


def map_registry_section(entry):
    for field, mapping in (
        ("layer", LAYER_SECTION_MAP),
        ("artifact_kind", ARTIFACT_KIND_SECTION_MAP),
        ("geu_role", {}),
        ("bundle_role", {}),
        ("governance_domain", GOVERNANCE_DOMAIN_SECTION_MAP),
    ):
        value = entry.get(field)
        if value in mapping:
            return mapping[value], f"registry:{field}={value}"
    return None, None


def match_directory(rel_lower):
    if rel_lower.startswith("src/validators/"):
        return "Validation & Testing", "directory:src/validators"
    if rel_lower.startswith("govreg_core/"):
        return "Core Governance Engine", "directory:govreg_core"
    if rel_lower.startswith("src/registry_transition/"):
        return "Core Governance Engine", "directory:src/registry_transition"
    if rel_lower.startswith("src/") and "_geu_governance/" in rel_lower:
        return "Core Governance Engine", "directory:src/*_geu_governance"
    if rel_lower.startswith("src/"):
        return "Core Governance Engine", "directory:src"
    directory_map = [
        ("registry/", "Core Governance Engine"),
        ("schemas/", "Schemas & Contracts"),
        ("contracts/", "Schemas & Contracts"),
        ("scripts/", "Scripts & Automation"),
        ("tests/", "Validation & Testing"),
        ("test/", "Validation & Testing"),
        ("validators/", "Validation & Testing"),
        ("docs/", "Documentation"),
        ("old_md_documents_for_review/", "Documentation"),
        ("config/", "Configuration & Policies"),
        ("policies/", "Configuration & Policies"),
        ("evidence/", "Evidence & Gates"),
        ("gates/", "Evidence & Gates"),
        ("geu/", "GEU (Governance Enforcement Units)"),
        ("file watcher/", "File Watcher & Path Abstraction"),
        ("path_files/", "File Watcher & Path Abstraction"),
        ("lp_long_plan/", "Planning & Execution"),
        ("sections/", "Planning & Execution"),
        (".state/", "State Management"),
        (".state_temp/", "State Management"),
        (".github/", "CI/CD & Integration"),
        ("backups/", "Backups & Archives"),
        ("archive_gov_reg/", "Backups & Archives"),
        ("templates/", "Templates"),
        ("monitoring/", "Monitoring & Training"),
        ("training/", "Monitoring & Training"),
        ("patches/", "Patches & Migrations"),
        (".migration/", "Patches & Migrations"),
    ]
    for prefix, section in directory_map:
        if rel_lower.startswith(prefix):
            return section, f"directory:{prefix.rstrip('/')}"
    return None, None


def match_name_patterns(name_lower, rel_lower):
    if (
        name_lower.endswith(".backup")
        or "_backup_" in name_lower
        or "_before_" in name_lower
        or "archive_" in name_lower
    ):
        return "Backups & Archives", "pattern:backup"
    if name_lower.endswith(".patch.json") or "_patch.json" in name_lower:
        return "Patches & Migrations", "pattern:patch"
    if any(
        token in name_lower
        for token in [
            "id_canonicality",
            "id_allocator",
            "id_identity",
            "id_crazy",
            "counter_store",
            "id_script_inventory",
        ]
    ):
        return "ID Management System", "pattern:id"
    if "governance_registry" in name_lower or "complete_ssot" in name_lower:
        return "Core Governance Engine", "pattern:registry"
    if name_lower.startswith("test_") or name_lower.endswith("_test.py") or "_test_" in name_lower:
        return "Validation & Testing", "pattern:test"
    if name_lower.startswith("validate_") or name_lower.endswith("_validator.py"):
        return "Validation & Testing", "pattern:validator"
    if (
        re.match(r"^p_\d{20}_.+\.py$", name_lower)
        or re.match(r"^p_\d{20}_.+\.ps1$", name_lower)
        or re.match(r"^p_\d{20}_.+\.sh$", name_lower)
    ):
        return "Scripts & Automation", "pattern:p_script"
    if name_lower.startswith(("run_", "migrate_", "fix_", "generate_", "check_")):
        return "Scripts & Automation", "pattern:script_name"
    if "policy" in name_lower or "policy_map" in name_lower or "normalization_map" in name_lower:
        return "Configuration & Policies", "pattern:policy"
    if "schema" in name_lower and name_lower.endswith(".json"):
        return "Schemas & Contracts", "pattern:schema"
    if "contract" in name_lower and name_lower.endswith(".json"):
        return "Schemas & Contracts", "pattern:contract"
    if any(
        token in name_lower
        for token in [
            "deployment_checklist",
            "implementation_summary",
            "final_status",
            "final_execution",
            "execution_status",
            "execution_summary",
            "critical_fixes",
            "verified_artifact_bundle",
        ]
    ):
        return "Deployment & Operations", "pattern:deployment"
    if any(
        token in name_lower
        for token in [
            "audit",
            "report",
            "execution_log",
            "validation_report",
            "coverage",
            "results",
            "evidence",
        ]
    ):
        return "Evidence & Gates", "pattern:evidence"
    if (
        name_lower.startswith("phase_")
        or name_lower.startswith("ph-")
        or name_lower.startswith("sec_")
        or "phase_contract" in name_lower
        or "traceability_matrix" in name_lower
    ):
        return "Planning & Execution", "pattern:planning"
    if "template" in name_lower:
        return "Templates", "pattern:template"
    if "monitor" in name_lower or "alert" in name_lower or "training" in rel_lower:
        return "Monitoring & Training", "pattern:monitoring"
    return None, None


def match_extension(name_lower):
    if name_lower.endswith((".schema.json", ".schema.yaml", ".schema.yml", ".contract.json")):
        return "Schemas & Contracts", "extension:schema"
    if name_lower.endswith(".patch.json"):
        return "Patches & Migrations", "extension:patch"
    if name_lower.endswith((".md", ".txt", ".docx")):
        return "Documentation", "extension:doc"
    if name_lower.endswith((".ps1", ".sh")):
        return "Scripts & Automation", "extension:script"
    return None, None


def read_head_text(path, max_lines):
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = []
            for _ in range(max_lines):
                line = handle.readline()
                if not line:
                    break
                lines.append(line)
        return "".join(lines)
    except (OSError, UnicodeDecodeError):
        return ""


def match_content(path, max_lines):
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None, None
    text = read_head_text(path, max_lines)
    if not text:
        return None, None
    if '"$schema"' in text or "'$schema'" in text:
        return "Schemas & Contracts", "content:$schema"
    if "generated_at" in text and ("report" in text or "results" in text or "evidence" in text):
        return "Evidence & Gates", "content:generated_at"
    if path.suffix.lower() == ".py":
        if re.search(r"^\s*def\s+test_", text, re.M) or "pytest" in text:
            return "Validation & Testing", "content:pytest"
        if re.search(r"^\s*def\s+validate_", text, re.M) or "validator" in text:
            return "Validation & Testing", "content:validator"
        if "__main__" in text:
            return "Scripts & Automation", "content:__main__"
    return None, None


def classify_file(path, repo_root, registry_index, max_lines):
    rel_path = path.relative_to(repo_root)
    rel_posix = rel_path.as_posix()
    rel_lower = rel_posix.lower()
    name_lower = path.name.lower()

    signals = []
    section = None
    confidence = None

    for matcher, default_confidence in (
        (match_directory, "high"),
        (match_name_patterns, "medium"),
        (match_extension, "medium"),
        (lambda _name, _rel=None: match_content(path, max_lines), "low"),
    ):
        if matcher is match_name_patterns:
            match_section, reason = matcher(name_lower, rel_lower)
        elif matcher is match_extension:
            match_section, reason = matcher(name_lower)
        elif matcher is match_directory:
            match_section, reason = matcher(rel_lower)
        else:
            match_section, reason = matcher(None)
        if match_section:
            section = match_section
            confidence = default_confidence
            if reason:
                signals.append(reason)
            break

    registry_info = None
    if registry_index is not None:
        entry = registry_index.get(rel_posix)
        if entry:
            registry_info = {
                key: entry.get(key)
                for key in ("file_id", "layer", "artifact_kind", "geu_role", "bundle_role", "governance_domain")
                if entry.get(key) is not None
            }
            registry_section, registry_reason = map_registry_section(entry)
            if registry_section:
                if registry_reason:
                    signals.append(registry_reason)
                section = registry_section
                confidence = "registry"

    if not section:
        section = "Unclassified"
        confidence = "low"

    return {
        "path": str(rel_path),
        "section": section,
        "confidence": confidence,
        "signals": signals,
        "registry": registry_info,
    }


def build_report(root, registry_index, max_lines):
    records = []
    for path in iter_files(root):
        records.append(classify_file(path, root, registry_index, max_lines))
    records.sort(key=lambda item: item["path"].lower())
    counts = {}
    for record in records:
        counts[record["section"]] = counts.get(record["section"], 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root": str(root),
        "counts": counts,
        "files": records,
    }


def main():
    parser = argparse.ArgumentParser(description="Classify repository files into governance sections.")
    parser.add_argument("--report", required=True, help="Output report path (JSON).")
    parser.add_argument("--root", default=None, help="Repository root (default: parent of scripts).")
    parser.add_argument(
        "--registry",
        default=None,
        help="Unified registry JSON (default: 01999000042260124503_governance_registry_unified.json).",
    )
    parser.add_argument("--max-lines", type=int, default=50, help="Max lines to scan for content signals.")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    registry_path = (
        Path(args.registry).resolve()
        if args.registry
        else repo_root / "01999000042260124503_governance_registry_unified.json"
    )

    registry_index = load_registry_index(registry_path, repo_root)
    report = build_report(repo_root, registry_index, args.max_lines)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    total = sum(report["counts"].values())
    print(f"Classified {total} files.")
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
