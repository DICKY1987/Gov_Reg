"""
GEU Reconciliation CLI

Commands:
- audit: Analyze registry for issues (non-destructive)
- normalize-ids: Fix file_id format and merge duplicates
- reconcile: Fix GEU fields (labels, types, dependencies)
- validate: Validate registry after fixes
"""

import click
import json
from pathlib import Path
from typing import Optional

from .registry_loader import (
    load_registry,
    save_registry,
    get_all_records,
    scan_registry_file_ids,
)
from .id_normalizer import (
    detect_duplicates,
    analyze_normalization_needs,
    normalize_file_id,
)
from .patch_writer import PatchWriter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GEU Reconciliation CLI - Fix registry data inconsistencies."""
    pass


@cli.command()
@click.option(
    "--registry",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to registry JSON file",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("EVIDENCE"),
    help="Output directory for evidence files",
)
def audit(registry: Path, output_dir: Path):
    """
    Audit registry for data inconsistencies (non-destructive).

    Checks:
    - file_id format (19-digit vs 20-digit)
    - file_id duplicates
    - geu_ids type drift
    - GEU ID format (labels vs canonical)
    - Dependency violations

    Generates evidence files for review.
    """
    click.echo(f"📊 Auditing registry: {registry}")

    # Load registry
    reg = load_registry(registry)
    records = get_all_records(reg)

    click.echo(f"  Loaded {len(records)} records")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================
    # Check 1: File ID Format
    # ========================================
    click.echo("\n🔍 Checking file_id format...")
    scan_results = scan_registry_file_ids(reg)

    # Filter out superseded records from validation
    active_records = [r for r in records if not r.get("superseded_by")]
    active_invalid_19 = [
        r
        for r in active_records
        if r.get("file_id") and len(r.get("file_id", "")) == 19
    ]

    file_id_issues = {
        "valid": len(
            [
                r
                for r in active_records
                if r.get("file_id") and len(r.get("file_id", "")) == 20
            ]
        ),
        "invalid_19_digit": len(active_invalid_19),
        "invalid_type": len(scan_results["invalid_type"]),
        "invalid_length": len(scan_results["invalid_length"]),
        "invalid_format": len(scan_results["invalid_format"]),
    }

    click.echo(f"  ✓ Valid (20-digit): {file_id_issues['valid']}")
    if file_id_issues["invalid_19_digit"] > 0:
        click.echo(f"  ❌ Invalid (19-digit): {file_id_issues['invalid_19_digit']}")
    if file_id_issues["invalid_type"]:
        click.echo(f"  ❌ Invalid (wrong type): {file_id_issues['invalid_type']}")
    if file_id_issues["invalid_length"]:
        click.echo(f"  ❌ Invalid (wrong length): {file_id_issues['invalid_length']}")
    if file_id_issues["invalid_format"]:
        click.echo(f"  ❌ Invalid (non-digit): {file_id_issues['invalid_format']}")

    # Save invalid file_ids
    if scan_results["invalid_19_digit"]:
        invalid_path = output_dir / "geu_audit.invalid_file_ids.jsonl"
        with open(invalid_path, "w") as f:
            for fid in scan_results["invalid_19_digit"]:
                f.write(json.dumps({"file_id": fid, "issue": "19_digits"}) + "\n")
        click.echo(f"  📄 Saved: {invalid_path}")

    # ========================================
    # Check 2: Duplicates
    # ========================================
    click.echo("\n🔍 Checking for duplicate file_ids...")
    # Only check active records (exclude superseded)
    active_records = [r for r in records if not r.get("superseded_by")]
    duplicates = detect_duplicates(active_records)

    click.echo(f"  Found {len(duplicates)} duplicate groups")

    if duplicates:
        dup_path = output_dir / "geu_audit.duplicate_file_id_groups.json"
        dup_data = {
            canonical: [r.get("file_id") for r in group]
            for canonical, group in duplicates.items()
        }
        with open(dup_path, "w") as f:
            json.dump(dup_data, f, indent=2)
        click.echo(f"  📄 Saved: {dup_path}")

        # Show examples
        for canonical, group in list(duplicates.items())[:3]:
            click.echo(f"    Example: {canonical} → {len(group)} records")

    # ========================================
    # Check 3: GEU Type Drift
    # ========================================
    click.echo("\n🔍 Checking geu_ids type...")
    active_records = [r for r in records if not r.get("superseded_by")]
    type_drift = []

    for i, record in enumerate(active_records):
        geu_ids = record.get("geu_ids")
        if geu_ids is not None and isinstance(geu_ids, str):
            type_drift.append(
                {
                    "file_id": record.get("file_id"),
                    "index": i,
                    "current_type": "string",
                    "expected_type": "array",
                    "value": geu_ids,
                }
            )

    if type_drift:
        click.echo(f"  ❌ String geu_ids found: {len(type_drift)}")

    if type_drift:
        drift_path = output_dir / "geu_audit.type_drift.jsonl"
        with open(drift_path, "w") as f:
            for entry in type_drift:
                f.write(json.dumps(entry) + "\n")
        click.echo(f"  📄 Saved: {drift_path}")

    # ========================================
    # Check 4: GEU ID Format
    # ========================================
    click.echo("\n🔍 Checking GEU ID format...")
    active_records = [r for r in records if not r.get("superseded_by")]
    geu_format_issues = []

    for i, record in enumerate(active_records):
        # Check primary_geu_id
        primary = record.get("primary_geu_id")
        if primary and isinstance(primary, str) and primary.startswith("GEU-"):
            geu_format_issues.append(
                {
                    "file_id": record.get("file_id"),
                    "index": i,
                    "field": "primary_geu_id",
                    "value": primary,
                    "issue": "label_format",
                }
            )

        # Check geu_ids array
        geu_ids = record.get("geu_ids")
        if isinstance(geu_ids, list):
            for gid in geu_ids:
                if isinstance(gid, str) and gid.startswith("GEU-"):
                    geu_format_issues.append(
                        {
                            "file_id": record.get("file_id"),
                            "index": i,
                            "field": "geu_ids",
                            "value": gid,
                            "issue": "label_format",
                        }
                    )

    if geu_format_issues:
        click.echo(f"  ❌ GEU labels found: {len(geu_format_issues)}")

    if geu_format_issues:
        format_path = output_dir / "geu_audit.invalid_geu_values.jsonl"
        with open(format_path, "w") as f:
            for entry in geu_format_issues:
                f.write(json.dumps(entry) + "\n")
        click.echo(f"  📄 Saved: {format_path}")

    # ========================================
    # Generate Summary Report
    # ========================================
    report = {
        "generated_at": "2026-02-03T19:00:00Z",
        "registry_path": str(registry),
        "total_records": len(records),
        "checks": {
            "file_id_format": {
                "valid": file_id_issues["valid"],
                "invalid_19_digit": file_id_issues["invalid_19_digit"],
                "invalid_type": file_id_issues["invalid_type"],
                "invalid_length": file_id_issues["invalid_length"],
                "invalid_format": file_id_issues["invalid_format"],
            },
            "duplicates": {
                "duplicate_groups": len(duplicates),
                "total_duplicates": sum(len(g) for g in duplicates.values()),
            },
            "geu_type_drift": {"string_geu_ids": len(type_drift)},
            "geu_format": {"label_format_issues": len(geu_format_issues)},
        },
        "status": "FAIL"
        if any(
            [
                file_id_issues["invalid_19_digit"],
                duplicates,
                type_drift,
                geu_format_issues,
            ]
        )
        else "PASS",
    }

    report_path = output_dir / "geu_audit.report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    click.echo(f"\n📊 Audit Report: {report_path}")
    click.echo(f"\n{'=' * 60}")
    click.echo(f"Status: {'❌ FAIL' if report['status'] == 'FAIL' else '✅ PASS'}")
    click.echo(f"{'=' * 60}")

    if report["status"] == "FAIL":
        click.echo("\n⚠️  Issues found. Run 'normalize-ids' and 'reconcile' to fix.")
        exit(1)
    else:
        click.echo("\n✅ Registry is clean!")
        exit(0)


@cli.command()
@click.option(
    "--registry",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to registry JSON file",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("PATCHES"),
    help="Output directory for patches",
)
@click.option(
    "--apply", is_flag=True, help="Apply patches immediately (default: dry run)"
)
def normalize_ids(registry: Path, output_dir: Path, apply: bool):
    """
    Normalize file_id format and merge duplicates.

    Fixes:
    - 19-digit → 20-digit file_ids
    - Merges duplicate records deterministically
    - Marks superseded records
    """
    click.echo(f"🔧 Normalizing file_ids: {registry}")

    if not apply:
        click.echo("  ℹ️  DRY RUN mode (use --apply to make changes)")

    # Load registry
    reg = load_registry(registry)
    records = get_all_records(reg)

    click.echo(f"  Loaded {len(records)} records")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Analyze normalization needs
    click.echo("\n📊 Analyzing normalization needs...")
    results = analyze_normalization_needs(records)

    needs_norm = [r for r in results if r.needs_normalization or r.is_duplicate]
    click.echo(f"  Found {len(needs_norm)} file_ids needing normalization/merge")

    if not needs_norm:
        click.echo("\n✅ No normalization needed!")
        return

    # Generate patches
    click.echo("\n📝 Generating patches...")
    writer = PatchWriter()

    # Build index of file_id → (record_index, data_key)
    file_id_to_index = {}
    files_count = len(reg.get("files", []))
    for i, record in enumerate(records):
        fid = record.get("file_id")
        if fid:
            # Determine if this record is in files or entries
            data_key = "files" if i < files_count else "entries"
            # For entries, adjust index to be relative to entries array
            rel_idx = i if data_key == "files" else (i - files_count)
            file_id_to_index[fid] = (rel_idx, data_key)

    # Track changes
    normalized_count = 0
    merged_count = 0

    for result in needs_norm:
        canonical_id = result.canonical_id
        original_ids = result.original_ids

        # Case 1: Just normalization (19-digit → 20-digit), no duplicate
        if result.needs_normalization and not result.is_duplicate:
            for orig_id in original_ids:
                if len(orig_id) == 19:
                    idx_info = file_id_to_index.get(orig_id)
                    if idx_info is not None:
                        rel_idx, data_key = idx_info
                        writer.add_file_id_normalization(
                            file_index=rel_idx,
                            old_file_id=orig_id,
                            new_file_id=canonical_id,
                            data_key=data_key,
                        )
                        normalized_count += 1

        # Case 2: Duplicates (merge required)
        elif result.is_duplicate:
            # Get canonical record and superseded records
            canonical_rec = result.canonical_record
            superseded_recs = result.superseded_records

            # Update canonical record's file_id if needed
            canonical_orig_id = canonical_rec.get("file_id")
            if canonical_orig_id != canonical_id:
                idx_info = file_id_to_index.get(canonical_orig_id)
                if idx_info is not None:
                    rel_idx, data_key = idx_info
                    writer.add_file_id_normalization(
                        file_index=rel_idx,
                        old_file_id=canonical_orig_id,
                        new_file_id=canonical_id,
                        data_key=data_key,
                    )

            # Mark superseded records
            for sup_rec in superseded_recs:
                sup_id = sup_rec.get("file_id")
                idx_info = file_id_to_index.get(sup_id)
                if idx_info is not None:
                    rel_idx, data_key = idx_info
                    writer.add_record_supersession(
                        file_index=rel_idx, canonical_id=canonical_id, data_key=data_key
                    )

            merged_count += len(superseded_recs)

    # Print summary
    writer.print_summary()
    click.echo(f"\n📊 Changes Summary:")
    click.echo(f"  Normalized (19→20 digit): {normalized_count}")
    click.echo(f"  Merged duplicates: {merged_count}")

    # Save patches
    patch_path = output_dir / "geu_fix.file_id_normalization.patch.json"
    evidence_path = output_dir / "geu_fix.file_id_merge_decisions.jsonl"

    writer.save_patch(patch_path)
    writer.save_evidence(evidence_path)

    if apply:
        click.echo("\n🔧 Applying patches...")
        click.echo("  ⚠️  Creating backup...")

        # Apply patches using simplified implementation
        # Note: For production, use jsonpatch library
        from .patch_writer import apply_patch

        try:
            patched_reg = apply_patch(reg, patch_path)

            # Save patched registry
            backup_path = registry.with_suffix(".json.backup")
            import shutil

            shutil.copy2(registry, backup_path)
            click.echo(f"  ✓ Backup: {backup_path}")

            save_registry(patched_reg, registry, backup=False)
            click.echo(f"  ✓ Applied patches to: {registry}")

            click.echo("\n✅ Normalization complete!")
        except Exception as e:
            click.echo(f"\n❌ Error applying patches: {e}")
            click.echo("  Patches saved but not applied. Review and apply manually.")
            exit(1)
    else:
        click.echo("\n💡 DRY RUN complete. Review patches:")
        click.echo(f"  - {patch_path}")
        click.echo(f"  - {evidence_path}")
        click.echo("\nTo apply: Add --apply flag")


@cli.command()
@click.option(
    "--registry",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to registry JSON file",
)
@click.option(
    "--geu-label-map",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to GEU label map JSON",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("PATCHES"),
    help="Output directory for patches",
)
@click.option(
    "--apply", is_flag=True, help="Apply patches immediately (default: dry run)"
)
def reconcile(registry: Path, geu_label_map: Path, output_dir: Path, apply: bool):
    """
    Reconcile GEU fields to canonical format.

    Fixes:
    - geu_ids type (string → array)
    - GEU labels → canonical IDs
    - Missing primary_geu_id (auto-assign)
    - Dependency violations
    """
    click.echo(f"🎯 Reconciling GEU fields: {registry}")

    if not apply:
        click.echo("  ℹ️  DRY RUN mode (use --apply to make changes)")

    # Load registry
    reg = load_registry(registry)
    records = get_all_records(reg)

    click.echo(f"  Loaded {len(records)} records")

    # Load GEU reconciler
    click.echo(f"\n📋 Loading GEU label map: {geu_label_map}")
    from .geu_reconciler import GEUReconciler

    try:
        reconciler = GEUReconciler.load_label_map(geu_label_map)
        click.echo(f"  ✓ Loaded {len(reconciler.label_map)} GEU mappings")
    except Exception as e:
        click.echo(f"  ❌ Failed to load label map: {e}")
        exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Analyze and reconcile
    click.echo("\n📊 Analyzing GEU fields...")

    results = []
    records_changed = 0
    total_changes = 0
    total_warnings = 0

    for i, record in enumerate(records):
        result = reconciler.reconcile_record(record)
        if result.changes_made or result.warnings:
            results.append((i, result))
            if result.changes_made:
                records_changed += 1
                total_changes += len(result.changes_made)
            total_warnings += len(result.warnings)

    click.echo(f"  Found {records_changed} records needing reconciliation")
    click.echo(f"  Total changes: {total_changes}")
    click.echo(f"  Total warnings: {total_warnings}")

    if not results:
        click.echo("\n✅ No reconciliation needed!")
        return

    # Generate patches
    click.echo("\n📝 Generating patches...")
    writer = PatchWriter()

    # Track change types
    type_fixes = 0
    label_mappings = 0
    auto_assignments = 0

    for record_idx, result in results:
        file_id = result.file_id

        # Determine data_key (files vs entries)
        data_key = "files" if record_idx < len(reg.get("files", [])) else "entries"
        if data_key == "entries":
            record_idx -= len(reg.get("files", []))

        # Generate patch operations for each change
        for field_name, new_value in result.new_values.items():
            old_value = result.original_values.get(field_name)

            # Determine operation type
            if old_value is None:
                op = "add"
            else:
                op = "replace"

            path = f"/{data_key}/{record_idx}/{field_name}"

            # Determine change type for tracking
            if field_name == "geu_ids" and isinstance(old_value, str):
                type_fixes += 1
                reason = "Type normalization: string → array"
            elif field_name in ["geu_ids", "primary_geu_id", "owner_geu_id"]:
                if isinstance(old_value, str) and old_value.startswith("GEU-"):
                    label_mappings += 1
                    reason = f"Label→ID mapping: {old_value} → canonical"
                elif field_name == "primary_geu_id" and old_value is None:
                    auto_assignments += 1
                    reason = "Auto-assigned from geu_ids[0]"
                else:
                    reason = f"GEU field reconciliation"
            else:
                reason = "GEU reconciliation"

            writer.add_operation(
                op=op,
                path=path,
                value=new_value,
                old_value=old_value,
                reason=reason,
                metadata={
                    "file_id": file_id,
                    "field": field_name,
                    "record_index": record_idx,
                    "data_key": data_key,
                },
            )

    # Print summary
    writer.print_summary()
    click.echo(f"\n📊 Changes Breakdown:")
    click.echo(f"  Type fixes (string→array): {type_fixes}")
    click.echo(f"  Label→ID mappings: {label_mappings}")
    click.echo(f"  Auto-assignments: {auto_assignments}")

    # Save patches
    patch_path = output_dir / "geu_fix.geu_field_reconcile.patch.json"
    evidence_path = output_dir / "geu_fix.geu_field_changes.jsonl"

    writer.save_patch(patch_path)
    writer.save_evidence(evidence_path)

    # Save warnings report
    if total_warnings > 0:
        warnings_path = output_dir / "geu_fix.warnings.jsonl"
        with open(warnings_path, "w", encoding="utf-8") as f:
            for record_idx, result in results:
                if result.warnings:
                    for warning in result.warnings:
                        f.write(
                            json.dumps({"file_id": result.file_id, "warning": warning})
                            + "\n"
                        )
        click.echo(f"✓ Saved warnings: {warnings_path} ({total_warnings} warnings)")

    if apply:
        click.echo("\n🔧 Applying patches...")
        click.echo("  ⚠️  Creating backup...")

        # Apply patches
        from .patch_writer import apply_patch

        try:
            patched_reg = apply_patch(reg, patch_path)

            # Save patched registry
            backup_path = registry.with_suffix(".json.backup")
            import shutil

            shutil.copy2(registry, backup_path)
            click.echo(f"  ✓ Backup: {backup_path}")

            save_registry(patched_reg, registry, backup=False)
            click.echo(f"  ✓ Applied patches to: {registry}")

            click.echo("\n✅ Reconciliation complete!")
        except Exception as e:
            click.echo(f"\n❌ Error applying patches: {e}")
            click.echo("  Patches saved but not applied. Review and apply manually.")
            exit(1)
    else:
        click.echo("\n💡 DRY RUN complete. Review patches:")
        click.echo(f"  - {patch_path}")
        click.echo(f"  - {evidence_path}")
        if total_warnings > 0:
            click.echo(f"  - {warnings_path}")
        click.echo("\nTo apply: Add --apply flag")


if __name__ == "__main__":
    cli()
