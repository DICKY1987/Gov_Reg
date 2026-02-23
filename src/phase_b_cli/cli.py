"""
Phase B CLI Entry Point

Commands:
  validate  - Validate Phase A plan is execution-ready
  compile   - Generate execution compilation package
  preview   - Generate human-readable execution preview
  package   - Bundle artifacts into deployable archive
"""

import argparse
import sys
from pathlib import Path

from .commands.validate import ValidateCommand
from .commands.compile import CompileCommand
from .commands.preview import PreviewCommand
from .commands.package import PackageCommand


def create_parser():
    parser = argparse.ArgumentParser(
        prog="plan-refine-b",
        description="Phase B: Execution Compilation CLI"
    )
    
    # Global flags
    parser.add_argument(
        "--repo-root", "-R",
        dest="repo_root",
        type=Path,
        default=Path.cwd(),
        help="Repository root for path resolution"
    )
    parser.add_argument(
        "--runs-dir",
        dest="runs_dir",
        type=Path,
        default=Path(".acms_runs"),
        help="Base directory for all run folders"
    )
    parser.add_argument(
        "--run-id",
        dest="run_id",
        required=True,
        help="Phase A run ID to operate on"
    )
    parser.add_argument(
        "--phase-b-run-id",
        dest="phase_b_run_id",
        help="Phase B run ID (auto-generated if omitted)"
    )
    parser.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        default=True,
        help="Fail-closed on any policy/schema/LIV violation"
    )
    parser.add_argument(
        "--json-stdout",
        dest="json_stdout",
        action="store_true",
        help="Emit JSON summary to stdout"
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # B1: validate
    validate_parser = subparsers.add_parser(
        "validate",
        help="Pre-flight check that Phase A plan is execution-ready"
    )
    validate_parser.add_argument(
        "--allow-waived-overlaps",
        dest="allow_waived_overlaps",
        action="store_true",
        help="Permit scope overlaps that were explicitly waived in Phase A"
    )
    
    # B2: compile
    compile_parser = subparsers.add_parser(
        "compile",
        help="Generate execution compilation package"
    )
    compile_parser.add_argument(
        "--parallel-detection",
        dest="parallel_detection",
        default="auto",
        choices=["auto", "none"],
        help="Detect independent tasks for parallel grouping"
    )
    compile_parser.add_argument(
        "--max-task-duration",
        dest="max_task_duration",
        type=int,
        default=3600,
        help="Fail if any task estimate (seconds) exceeds this limit"
    )
    compile_parser.add_argument(
        "--harness-lang",
        dest="harness_lang",
        default="sh",
        choices=["sh", "py"],
        help="Language for generated test harness script"
    )
    
    # B3: preview
    preview_parser = subparsers.add_parser(
        "preview",
        help="Human-readable execution plan preview"
    )
    preview_parser.add_argument(
        "--format", "-f",
        dest="output_format",
        default="markdown",
        choices=["markdown", "mermaid", "json"],
        help="Output format"
    )
    preview_parser.add_argument(
        "--out", "-o",
        dest="out_path",
        type=Path,
        help="Override output file path"
    )
    
    # B4: package
    package_parser = subparsers.add_parser(
        "package",
        help="Bundle all Phase B artifacts into deployable archive"
    )
    package_parser.add_argument(
        "--archive-format",
        dest="archive_format",
        default="tar.gz",
        choices=["tar.gz", "zip"],
        help="Archive format"
    )
    package_parser.add_argument(
        "--include-lineage",
        dest="include_lineage",
        action="store_true",
        default=True,
        help="Include Phase A artifacts in archive under lineage/"
    )
    package_parser.add_argument(
        "--out", "-o",
        dest="out_path",
        type=Path,
        help="Override output archive path"
    )
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # Route to command handlers
    commands = {
        "validate": ValidateCommand,
        "compile": CompileCommand,
        "preview": PreviewCommand,
        "package": PackageCommand
    }
    
    try:
        command_class = commands[args.command]
        command = command_class(args)
        exit_code = command.execute()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Internal error: {e}", file=sys.stderr)
        sys.exit(13)


if __name__ == "__main__":
    main()
