"""
GEU Reporter

Generates GEU sets reports from registry data.

Features:
1. Group files by canonical primary_geu_id
2. Generate markdown report
3. Generate JSON report
4. Detect unassigned files
5. Calculate membership statistics
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime


class GEUReporter:
    """
    Generates reports on GEU (Governance Enforcement Unit) sets.

    Usage:
        reporter = GEUReporter(records)
        reporter.generate_markdown(Path("geu_sets.md"))
        reporter.generate_json(Path("geu_sets.json"))
    """

    def __init__(self, records: List[Dict[str, Any]]):
        """
        Initialize reporter with registry records.

        Args:
            records: List of registry records
        """
        self.records = records
        self._geu_sets = None
        self._unassigned = None
        self._analyze()

    def _analyze(self):
        """Analyze records and group by GEU."""
        # Group by primary_geu_id
        geu_groups = defaultdict(list)
        unassigned = []

        for record in self.records:
            primary_geu_id = record.get("primary_geu_id")
            file_id = record.get("file_id")

            if not file_id:
                continue  # Skip records without file_id

            if primary_geu_id:
                geu_groups[primary_geu_id].append(record)
            else:
                unassigned.append(record)

        self._geu_sets = dict(geu_groups)
        self._unassigned = unassigned

    def get_geu_sets(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get GEU sets (grouped by primary_geu_id)."""
        return self._geu_sets

    def get_unassigned(self) -> List[Dict[str, Any]]:
        """Get files without primary_geu_id."""
        return self._unassigned

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dict with counts and metadata
        """
        return {
            "total_records": len(self.records),
            "geu_sets_count": len(self._geu_sets),
            "unassigned_count": len(self._unassigned),
            "geu_sets": {
                geu_id: len(files) for geu_id, files in self._geu_sets.items()
            },
        }

    def generate_markdown(self, output_path: Path) -> None:
        """
        Generate markdown report.

        Args:
            output_path: Path to output markdown file
        """
        lines = []

        # Header
        lines.append("# GEU Sets Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")
        lines.append(f"**Total Records:** {len(self.records)}")
        lines.append(f"**GEU Sets Found:** {len(self._geu_sets)}")
        lines.append(f"**Unassigned Files:** {len(self._unassigned)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| GEU ID | File Count | Files |")
        lines.append("|--------|------------|-------|")

        # Sort GEU sets by ID
        for geu_id in sorted(self._geu_sets.keys()):
            files = self._geu_sets[geu_id]
            file_count = len(files)

            # Get sample file paths
            sample_paths = []
            for f in files[:3]:
                path = (
                    f.get("relative_path")
                    or f.get("absolute_path")
                    or f.get("file_id", "unknown")
                )
                sample_paths.append(path)

            files_preview = ", ".join(sample_paths)
            if file_count > 3:
                files_preview += f", ... ({file_count - 3} more)"

            lines.append(f"| `{geu_id}` | {file_count} | {files_preview} |")

        lines.append("")

        # Detailed sections for each GEU
        lines.append("## GEU Set Details")
        lines.append("")

        for geu_id in sorted(self._geu_sets.keys()):
            files = self._geu_sets[geu_id]

            lines.append(f"### GEU: `{geu_id}`")
            lines.append("")
            lines.append(f"**Member Count:** {len(files)}")
            lines.append("")

            # Check for roles
            roles = set()
            for f in files:
                role = f.get("geu_role") or f.get("bundle_role")
                if role:
                    roles.add(role)

            if roles:
                lines.append(f"**Roles:** {', '.join(sorted(roles))}")
                lines.append("")

            # List files
            lines.append("**Files:**")
            lines.append("")
            for f in files:
                file_id = f.get("file_id", "unknown")
                path = f.get("relative_path") or f.get("absolute_path") or "no path"
                role = f.get("geu_role") or f.get("bundle_role") or "no role"
                lines.append(f"- `{file_id}` - {path} ({role})")

            lines.append("")

        # Unassigned section
        if self._unassigned:
            lines.append("## Unassigned Files")
            lines.append("")
            lines.append(f"**Count:** {len(self._unassigned)}")
            lines.append("")
            lines.append("Files without primary_geu_id:")
            lines.append("")

            for f in self._unassigned[:20]:  # Limit to first 20
                file_id = f.get("file_id", "unknown")
                path = f.get("relative_path") or f.get("absolute_path") or "no path"
                lines.append(f"- `{file_id}` - {path}")

            if len(self._unassigned) > 20:
                lines.append(f"- ... and {len(self._unassigned) - 20} more")

            lines.append("")

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✓ Saved markdown report: {output_path}")

    def generate_json(self, output_path: Path) -> None:
        """
        Generate JSON report.

        Args:
            output_path: Path to output JSON file
        """
        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": self.get_summary(),
            "geu_sets": {},
            "unassigned": [],
        }

        # Add GEU set details
        for geu_id, files in self._geu_sets.items():
            report["geu_sets"][geu_id] = {
                "count": len(files),
                "files": [
                    {
                        "file_id": f.get("file_id"),
                        "relative_path": f.get("relative_path"),
                        "geu_role": f.get("geu_role"),
                        "bundle_role": f.get("bundle_role"),
                    }
                    for f in files
                ],
            }

        # Add unassigned files
        report["unassigned"] = [
            {"file_id": f.get("file_id"), "relative_path": f.get("relative_path")}
            for f in self._unassigned
        ]

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved JSON report: {output_path}")


if __name__ == "__main__":
    import sys
    import os

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from govreg_core.geu_reconciliation.registry_loader import (
        load_registry,
        get_all_records,
    )

    if len(sys.argv) < 2:
        print("Usage: python geu_reporter.py <registry_path>")
        sys.exit(1)

    registry_path = Path(sys.argv[1])

    print(f"Loading registry: {registry_path}")
    registry = load_registry(registry_path)
    records = get_all_records(registry)

    print(f"✓ Loaded {len(records)} records")

    # Generate reports
    print("\nGenerating reports...")
    reporter = GEUReporter(records)

    summary = reporter.get_summary()
    print(f"\nSummary:")
    print(f"  Total records: {summary['total_records']}")
    print(f"  GEU sets: {summary['geu_sets_count']}")
    print(f"  Unassigned: {summary['unassigned_count']}")

    print("\nGEU set sizes:")
    for geu_id, count in sorted(summary["geu_sets"].items()):
        print(f"  {geu_id}: {count} files")

    # Save reports
    output_dir = Path("REPORTS")
    output_dir.mkdir(exist_ok=True)

    md_path = output_dir / "geu_sets.regenerated.md"
    json_path = output_dir / "geu_sets.regenerated.json"

    reporter.generate_markdown(md_path)
    reporter.generate_json(json_path)

    print(f"\n✅ Reports generated successfully!")
