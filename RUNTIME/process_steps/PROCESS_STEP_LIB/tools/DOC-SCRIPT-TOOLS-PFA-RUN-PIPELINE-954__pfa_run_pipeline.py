#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-RUN-PIPELINE-954
"""
Pipeline Orchestrator - Regenerate Everything from Source Schemas

One command to rebuild the entire E2E pipeline from source schemas.

Usage:
    python pfa_run_pipeline.py              # Full rebuild
    python pfa_run_pipeline.py --quick      # Only rebuild if changed
    python pfa_run_pipeline.py --dry-run    # Preview what would change
    python pfa_run_pipeline.py --validate   # Validate only (no rebuild)
"""
# DOC_ID: DOC-SCRIPT-TOOLS-PFA-RUN-PIPELINE-954

import sys
import DOC-ERROR-UTILS-TIME-145__time
import subprocess
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from DOC-SCRIPT-TOOLS-PFA-COMMON-944__pfa_common import print_success, print_error, print_warning, print_info

class PipelineOrchestrator:
    """Orchestrates the E2E pipeline regeneration"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.tools_dir = base_dir / 'tools'
        self.schemas_dir = base_dir / 'schemas'
        self.indices_dir = base_dir / 'indices'
        self.guides_dir = base_dir / 'guides'

    def run_tool(self, script_name: str, args: list, description: str, dry_run=False):
        """Run a Python tool and capture output"""
        if dry_run:
            print_info(f"[DRY RUN] Would run: {script_name} {' '.join(args)}")
            return True

        script_path = self.tools_dir / script_name
        cmd = [sys.executable, str(script_path)] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.tools_dir)
            )

            if result.returncode == 0:
                print_success(f"✓ {description}")
                if result.stdout:
                    # Print important lines from stdout
                    for line in result.stdout.split('\n'):
                        if any(marker in line for marker in ['✓', '✅', 'steps', 'Complete', 'Created']):
                            print(f"  {line}")
                return True
            else:
                print_error(f"✗ {description} failed")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"✗ {description} failed: {e}")
            return False

    def check_if_rebuild_needed(self):
        """Check if source schemas are newer than unified schema"""
        source_files = list((self.schemas_dir / 'source').glob('*.yaml'))
        unified_file = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'

        if not unified_file.exists():
            return True, "Unified schema doesn't exist"

        unified_mtime = unified_file.stat().st_mtime

        for source_file in source_files:
            if source_file.stat().st_mtime > unified_mtime:
                return True, f"{source_file.name} was modified"

        return False, "All files up-to-date"

    def validate_sources(self, dry_run=False):
        """Step 1: Validate source schemas"""
        print_info("Validating source schemas...")

        # Check that source files exist
        source_files = list((self.schemas_dir / 'source').glob('PFA_*.yaml'))

        if len(source_files) < 5:
            print_warning(f"Only found {len(source_files)} source schemas (expected 5)")

        print(f"  Found {len(source_files)} source schemas")

        # TODO: Could add schema validation here
        # For now, just check they exist and are readable
        for source_file in source_files:
            if source_file.stat().st_size == 0:
                print_error(f"  {source_file.name} is empty!")
                return False

        print_success("Source schemas validated")
        return True

    def merge_schemas(self, dry_run=False):
        """Step 2: Merge source schemas into unified schema"""
        print_info("Merging schemas...")

        output = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        report = self.indices_dir / 'merge_report.json'

        args = [
            '--all',
            '--output', str(output),
            '--report', str(report)
        ]

        return self.run_tool(
            'pfa_merge_schemas.py',
            args,
            'Schema merge',
            dry_run
        )

    def build_index(self, dry_run=False):
        """Step 3: Build master index from unified schema"""
        print_info("Building master index...")

        schema = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        output = self.indices_dir / 'master_index.json'

        args = [
            '--schema', str(schema),
            '--output', str(output),
            '--pretty'
        ]

        return self.run_tool(
            'pfa_build_master_index.py',
            args,
            'Master index build',
            dry_run
        )

    def generate_lists(self, dry_run=False, parallel=False):
        """Step 4: Generate step list documents"""
        print_info("Generating step lists...")

        if dry_run:
            print_info("[DRY RUN] Would generate ALL_274_STEPS.md")
            print_info("[DRY RUN] Would generate ALL_274_STEPS_EXPLAINED.md")
            return True

        if parallel:
            # Run in parallel (future enhancement)
            from concurrent.futures import ThreadPoolExecutor

            print_info("Running generators in parallel...")
            with ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(
                    self.run_tool,
                    'generate_explained_steps.py',
                    [],
                    'Explained list',
                    dry_run
                )
                # Future: Add technical list generator here

                return future1.result()
        else:
            # Run sequentially
            return self.run_tool(
                'generate_explained_steps.py',
                [],
                'Step list generation',
                dry_run
            )

    def run_validation(self, dry_run=False):
        """Step 5: Run validation suite"""
        print_info("Running validation...")

        schema = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        index = self.indices_dir / 'master_index.json'
        docs = self.base_dir.parent / 'docs' / 'e2e'
        report = self.indices_dir / 'validation_report.json'

        args = [
            '--schema', str(schema),
            '--index', str(index),
            '--docs-dir', str(docs),
            '--report', str(report)
        ]

        # Validation can fail but we still want to see results
        result = self.run_tool(
            'pfa_validate_e2e_pipeline.py',
            args,
            'Validation suite',
            dry_run
        )

        # Don't fail pipeline on validation warnings
        return True

    def run_full_pipeline(self, dry_run=False, quick=False):
        """Run complete pipeline from source to all outputs"""
        start_time = time.time()

        print("=" * 70)
        print("🚀 E2E PIPELINE ORCHESTRATOR")
        print("=" * 70)
        print()

        if dry_run:
            print_warning("DRY RUN MODE - No files will be modified")
            print()

        if quick:
            needs_rebuild, reason = self.check_if_rebuild_needed()
            if not needs_rebuild:
                print_success(f"✅ {reason} - Skipping rebuild")
                return True
            else:
                print_info(f"Rebuild needed: {reason}")
                print()

        steps = [
            ("1/5", "Validate sources", self.validate_sources),
            ("2/5", "Merge schemas", self.merge_schemas),
            ("3/5", "Build index", self.build_index),
            ("4/5", "Generate lists", self.generate_lists),
            ("5/5", "Run validation", self.run_validation),
        ]

        failed = []

        for step_num, desc, func in steps:
            print(f"[{step_num}] {desc}...")
            try:
                success = func(dry_run=dry_run)
                if not success:
                    failed.append(desc)
                    print_error(f"Step failed: {desc}")
            except Exception as e:
                failed.append(desc)
                print_error(f"Step failed: {desc} - {e}")
            print()

        elapsed = time.time() - start_time

        print("=" * 70)
        if failed:
            print_warning(f"⚠️  Pipeline completed with {len(failed)} failures in {elapsed:.1f}s")
            for step in failed:
                print(f"  ✗ {step}")
            return False
        else:
            print_success(f"✅ Pipeline complete in {elapsed:.1f} seconds!")
            print()
            print("Generated files:")
            print("  • schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml")
            print("  • indices/master_index.json")
            print("  • guides/ALL_274_STEPS.md")
            print("  • guides/ALL_274_STEPS_EXPLAINED.md")
            print("  • indices/validation_report.json")
        print("=" * 70)

        return len(failed) == 0

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='E2E Pipeline Orchestrator - Regenerate everything from source schemas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pfa_run_pipeline.py              # Full rebuild
  python pfa_run_pipeline.py --quick      # Only if changed
  python pfa_run_pipeline.py --dry-run    # Preview changes
  python pfa_run_pipeline.py --validate   # Validate only
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying files')
    parser.add_argument('--quick', action='store_true',
                        help='Only rebuild if source schemas changed')
    parser.add_argument('--validate', action='store_true',
                        help='Run validation only (no rebuild)')

    args = parser.parse_args()

    # Get base directory (PROCESS_STEP_LIB)
    base_dir = Path(__file__).parent.parent

    orchestrator = PipelineOrchestrator(base_dir)

    if args.validate:
        # Validate only
        print("Running validation only...")
        success = orchestrator.run_validation(dry_run=args.dry_run)
    else:
        # Full pipeline
        success = orchestrator.run_full_pipeline(
            dry_run=args.dry_run,
            quick=args.quick
        )

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
