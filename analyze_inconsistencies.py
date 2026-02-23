import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml


REGISTRY_DIR = Path(__file__).resolve().parent / "01260207201000001250_REGISTRY"
REPORT_PATH = REGISTRY_DIR / "REGISTRY_INCONSISTENCIES_REPORT.md"


def read_csv_columns(path: Path) -> list[str]:
    columns = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            col = (row.get("column") or "").strip()
            if col:
                columns.append(col)
    return columns


def read_csv_derived_columns(path: Path) -> list[str]:
    derived = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mode = (row.get("derivation_mode") or "").strip().upper()
            if mode in {"DERIVED", "COMPUTED"}:
                col = (row.get("column") or "").strip()
                if col:
                    derived.append(col)
    return derived


def read_md_columns(path: Path) -> list[str]:
    columns = []
    pattern = re.compile(r"^-\s+\*\*(.+?)\*\*\s+[\u2014-]\s+")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            match = pattern.match(line)
            if match:
                columns.append(match.group(1).strip())
    return columns


def read_registry_headers_md(path: Path) -> list[str]:
    columns = []
    pattern = re.compile(r"^\|\s*`([^`]+)`\s*\|")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            match = pattern.match(line)
            if match:
                columns.append(match.group(1).strip())
    return columns


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_block(items: list[str]) -> str:
    if not items:
        return "```\n(none)\n```"
    return "```\n" + "\n".join(items) + "\n```"


def main() -> None:
    paths = {
        "csv": REGISTRY_DIR / "COLUMN_DICTIONARY_184_COLUMNS.csv",
        "md": REGISTRY_DIR / "COLUMN_DICTIONARY_184_COLUMNS.md",
        "registry_headers_md": REGISTRY_DIR / "REGISTRY_COLUMN_HEADERS.md",
        "json_dict": REGISTRY_DIR / "01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json",
        "derivations": REGISTRY_DIR / "01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml",
        "write_policy": REGISTRY_DIR / "01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml",
        "registry": REGISTRY_DIR / "01999000042260124503_REGISTRY_file.json",
    }

    csv_columns = read_csv_columns(paths["csv"])
    csv_derived = read_csv_derived_columns(paths["csv"])
    md_columns = read_md_columns(paths["md"])
    registry_headers_md = read_registry_headers_md(paths["registry_headers_md"])

    json_dict = load_json(paths["json_dict"])
    json_columns = list(json_dict.get("headers", {}).keys())
    header_count_expected = json_dict.get("header_count_expected")
    dictionary_version = json_dict.get("dictionary_version")

    derivations = load_yaml(paths["derivations"]) or {}
    derived_columns = list((derivations.get("derived_columns") or {}).keys())

    write_policy = load_yaml(paths["write_policy"]) or {}
    write_policy_columns = list((write_policy.get("columns") or {}).keys())

    registry = load_json(paths["registry"])
    registry_headers = list((registry.get("column_headers") or {}).keys())
    registry_version = registry.get("schema_version")
    column_headers_version = registry.get("column_headers_version")

    record_counts = {}
    record_columns_by_type = {}
    for key, value in registry.items():
        if isinstance(value, list):
            record_counts[key] = len(value)
            col_set = set()
            for entry in value:
                if isinstance(entry, dict):
                    col_set.update(entry.keys())
            record_columns_by_type[key] = col_set

    record_columns_union = set().union(*record_columns_by_type.values()) if record_columns_by_type else set()

    sets = {
        "csv": set(csv_columns),
        "md": set(md_columns),
        "json": set(json_columns),
        "registry_headers": set(registry_headers),
        "registry_headers_md": set(registry_headers_md),
        "derived": set(derived_columns),
        "write_policy": set(write_policy_columns),
    }

    union_all = set().union(*sets.values())
    union_def_sources = (
        sets["csv"] | sets["md"] | sets["json"] | sets["registry_headers"] | sets["write_policy"]
    )
    intersection_def_sources = (
        sets["csv"] & sets["md"] & sets["json"] & sets["registry_headers"] & sets["write_policy"]
    )

    csv_not_in_json = sorted(sets["csv"] - sets["json"])
    json_not_in_csv = sorted(sets["json"] - sets["csv"])
    md_not_in_json = sorted(sets["md"] - sets["json"])
    json_not_in_md = sorted(sets["json"] - sets["md"])

    derived_not_in_dict = sorted(sets["derived"] - sets["json"])
    write_policy_not_in_dict = sorted(sets["write_policy"] - sets["json"])
    dict_not_in_write_policy = sorted(sets["json"] - sets["write_policy"])
    orphaned_columns = sorted((sets["derived"] | sets["write_policy"]) - sets["json"])

    missing_derivation_flags = sorted(sets["derived"] - set(csv_derived))
    missing_derivation_flags_in_dict = sorted((sets["derived"] & sets["json"]) - set(csv_derived))

    record_not_in_headers = sorted(record_columns_union - sets["registry_headers"])
    headers_not_in_records = sorted(sets["registry_headers"] - record_columns_union)

    used_defined_columns = sorted(record_columns_union & sets["registry_headers"])

    field_record_types = {}
    for record_type, cols in record_columns_by_type.items():
        for col in cols:
            field_record_types.setdefault(col, []).append(record_type)

    report_lines = []
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    report_lines.append("# Registry Schema Inconsistencies Report")
    report_lines.append("")
    report_lines.append(f"Generated: {now_utc}")
    report_lines.append("Analysis Scope: 7 registry definition files")
    report_lines.append(f"Registry Version: {registry_version}")
    report_lines.append(f"Dictionary Version: {dictionary_version}")
    report_lines.append(f"Registry Column Headers Version: {column_headers_version}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append(
        f"- Column count mismatch: CSV/MD list {len(csv_columns)} columns, JSON dictionary and registry headers list {len(json_columns)}; JSON header_count_expected is {header_count_expected} (missing `dir_id` in CSV/MD)."
    )
    report_lines.append(
        f"- Orphaned policy/derivation columns: {len(orphaned_columns)} columns appear in derivations/write policy but not in the dictionary."
    )
    report_lines.append(
        f"- Missing write policies: {len(dict_not_in_write_policy)} dictionary columns lack write policy entries (all `py_*`)."
    )
    report_lines.append(
        f"- Derivation mode mismatch: {len(derived_columns)} derived columns in YAML vs {len(csv_derived)} marked DERIVED/COMPUTED in CSV ({len(missing_derivation_flags)} missing flags; {len(missing_derivation_flags_in_dict)} of those are in the dictionary)."
    )
    report_lines.append(
        f"- Undeclared fields in records: {len(record_not_in_headers)} fields appear in records but are not in registry headers."
    )
    report_lines.append(
        f"- Column utilization: {len(used_defined_columns)}/{len(registry_headers)} defined columns are used in data; {len(headers_not_in_records)} unused ({len(headers_not_in_records) / len(registry_headers) * 100:.1f}%)."
    )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Files Analyzed")
    report_lines.append("")
    report_lines.append("| File | Purpose | Count/Version |")
    report_lines.append("|------|---------|---------------|")
    report_lines.append(f"| `COLUMN_DICTIONARY_184_COLUMNS.csv` | CSV column definitions | {len(csv_columns)} columns |")
    report_lines.append(f"| `COLUMN_DICTIONARY_184_COLUMNS.md` | Human-readable column documentation | {len(md_columns)} columns |")
    report_lines.append(
        f"| `REGISTRY_COLUMN_HEADERS.md` | Governance registry column subset | {len(registry_headers_md)} columns |"
    )
    report_lines.append(
        f"| `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json` | JSON dictionary | {len(json_columns)} headers (v{dictionary_version}) |"
    )
    report_lines.append(
        f"| `01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml` | Derivation formulas | {len(derived_columns)} columns |"
    )
    report_lines.append(
        f"| `01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` | Write policies | {len(write_policy_columns)} columns |"
    )
    report_lines.append(
        f"| `01999000042260124503_REGISTRY_file.json` | Registry data | {len(registry_headers)} headers (v{registry_version}) |"
    )
    report_lines.append("")
    report_lines.append(
        "Registry Data: "
        + ", ".join(f"{record_counts.get(k, 0)} {k}" for k in sorted(record_counts))
    )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Issue Category 1: Column Count Mismatch (185 vs 184)")
    report_lines.append("")
    report_lines.append(
        "CSV/MD list 184 columns, while the JSON dictionary and registry headers list 185. The JSON dictionary also sets `header_count_expected` to 184."
    )
    report_lines.append("")
    report_lines.append("Missing from CSV/MD:")
    report_lines.append(format_block(json_not_in_csv))
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Issue Category 2: Orphaned Policy/Derivation Columns")
    report_lines.append("")
    report_lines.append(
        "These columns appear in derivations and write policy but are missing from the dictionary and registry headers."
    )
    report_lines.append("")
    report_lines.append(format_block(orphaned_columns))
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Issue Category 3: Missing Write Policies")
    report_lines.append("")
    report_lines.append(
        "These dictionary columns are missing write policy entries. All are `py_*` fields."
    )
    report_lines.append("")
    report_lines.append(format_block(dict_not_in_write_policy))
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Issue Category 4: Derivation Mode Mismatch")
    report_lines.append("")
    report_lines.append(
        f"Derivations YAML defines {len(derived_columns)} derived columns, but the CSV marks only {len(csv_derived)} as DERIVED/COMPUTED. "
        f"Total missing derivation_mode flags: {len(missing_derivation_flags)}; {len(missing_derivation_flags_in_dict)} of these are present in the dictionary."
    )
    report_lines.append("")
    report_lines.append("CSV columns marked DERIVED/COMPUTED:")
    report_lines.append(format_block(sorted(csv_derived)))
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Issue Category 5: Undeclared Fields in Registry Records")
    report_lines.append("")
    report_lines.append(
        "These fields are present in registry records but not defined in registry headers."
    )
    report_lines.append("")
    report_lines.append(format_block(record_not_in_headers))
    report_lines.append("")
    report_lines.append("Field usage by record type:")
    report_lines.append("")
    report_lines.append("| Field | Record Types |")
    report_lines.append("|-------|--------------|")
    for field in record_not_in_headers:
        record_types = ", ".join(sorted(field_record_types.get(field, [])))
        report_lines.append(f"| `{field}` | {record_types} |")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Issue Category 6: Column Under-Utilization")
    report_lines.append("")
    report_lines.append(f"- Defined columns (registry headers): {len(registry_headers)}")
    report_lines.append(f"- Used defined columns in records: {len(used_defined_columns)}")
    report_lines.append(
        f"- Unused defined columns: {len(headers_not_in_records)} ({len(headers_not_in_records) / len(registry_headers) * 100:.1f}%)"
    )
    report_lines.append(f"- Total fields seen in records (including undeclared): {len(record_columns_union)}")
    report_lines.append("")
    report_lines.append("Unique fields by record type:")
    report_lines.append("")
    report_lines.append("| Record Type | Record Count | Unique Fields |")
    report_lines.append("|-------------|--------------|---------------|")
    for key in sorted(record_counts):
        report_lines.append(
            f"| {key} | {record_counts.get(key, 0)} | {len(record_columns_by_type.get(key, set()))} |"
        )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Cross-File Synchronization Summary")
    report_lines.append("")
    report_lines.append("| Source | Column Count | Notes |")
    report_lines.append("|--------|--------------|-------|")
    report_lines.append(f"| CSV Dictionary | {len(csv_columns)} | Missing `dir_id` |")
    report_lines.append(f"| MD Dictionary | {len(md_columns)} | Missing `dir_id` |")
    report_lines.append(
        f"| JSON Dictionary | {len(json_columns)} | header_count_expected={header_count_expected} |"
    )
    report_lines.append(f"| Registry Headers | {len(registry_headers)} | Matches JSON headers |")
    report_lines.append(f"| Derivations YAML | {len(derived_columns)} | {len(derived_not_in_dict)} not in dictionary |")
    report_lines.append(
        f"| Write Policy YAML | {len(write_policy_columns)} | {len(dict_not_in_write_policy)} dictionary columns missing |"
    )
    report_lines.append(f"| Governance Headers (REGISTRY_COLUMN_HEADERS.md) | {len(registry_headers_md)} | Subset documentation |")
    report_lines.append("")
    report_lines.append(
        f"Total unique column names across all sources: {len(union_all)}"
    )
    report_lines.append(
        f"Columns shared by CSV+MD+JSON+Registry Headers+Write Policy: {len(intersection_def_sources)}"
    )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Technical Debt Metrics (Derived from Current Files)")
    report_lines.append("")
    report_lines.append(
        f"- Schema consistency (definition sources): {len(intersection_def_sources)}/{len(union_def_sources)} ({len(intersection_def_sources) / len(union_def_sources) * 100:.1f}%)"
    )
    report_lines.append(
        f"- Write policy coverage: {len(sets['json'] & sets['write_policy'])}/{len(sets['json'])} ({len(sets['json'] & sets['write_policy']) / len(sets['json']) * 100:.1f}%)"
    )
    report_lines.append(
        f"- Derivation documentation coverage: {len(csv_derived)}/{len(derived_columns)} ({len(csv_derived) / len(derived_columns) * 100:.1f}%)"
    )
    report_lines.append(
        f"- Schema utilization (defined columns used): {len(used_defined_columns)}/{len(registry_headers)} ({len(used_defined_columns) / len(registry_headers) * 100:.1f}%)"
    )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Remediation Plan (Suggested)")
    report_lines.append("")
    report_lines.append("Phase 1: Stop schema violations")
    report_lines.append("- Decide whether to add the 8 undeclared fields to the schema or remove them from writers.")
    report_lines.append("- Add write policy entries for all 37 `py_*` columns, or remove those columns from the dictionary.")
    report_lines.append("- Resolve the 184 vs 185 column count mismatch (`dir_id`).")
    report_lines.append("")
    report_lines.append("Phase 2: Align definitions")
    report_lines.append(f"- Decide the fate of the {len(orphaned_columns)} orphaned policy/derivation columns.")
    report_lines.append("- Align derivation mode flags between CSV and derivations YAML.")
    report_lines.append("")
    report_lines.append("Phase 3: Reduce bloat")
    report_lines.append("- Audit the 143 unused defined columns and classify as deprecated or future.")
    report_lines.append("- Consider tiering the schema (Core / Extended / Future).")
    report_lines.append("")
    report_lines.append("Phase 4: Prevent recurrence")
    report_lines.append("- Add automated checks to keep CSV/MD/JSON/policy/derivations in sync.")
    report_lines.append("- Validate record writes against the registry headers.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Appendices")
    report_lines.append("")
    report_lines.append("### Appendix A: Missing Write Policy Columns")
    report_lines.append(format_block(dict_not_in_write_policy))
    report_lines.append("")
    report_lines.append("### Appendix B: Orphaned Policy/Derivation Columns")
    report_lines.append(format_block(orphaned_columns))
    report_lines.append("")
    report_lines.append("### Appendix C: Derived Columns Missing CSV Derivation Flags")
    report_lines.append(format_block(missing_derivation_flags))
    report_lines.append("")
    report_lines.append("### Appendix D: Record Fields by Type")
    for record_type in sorted(record_columns_by_type):
        report_lines.append("")
        report_lines.append(f"**{record_type}** ({len(record_columns_by_type[record_type])} fields)")
        report_lines.append(format_block(sorted(record_columns_by_type[record_type])))
    report_lines.append("")
    report_lines.append("### Appendix E: References")
    report_lines.append("")
    report_lines.append("Files:")
    report_lines.append(format_block([str(path) for path in paths.values()]))
    report_lines.append("")
    report_lines.append("Script:")
    report_lines.append(format_block([str(Path(__file__).resolve())]))

    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
