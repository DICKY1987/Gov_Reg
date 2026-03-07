# DOC_LINK: DOC-PAT-VALIDATION-VALIDATE-WORKSTREAMS-640
import argparse
import json
import sys
import re  # Import re for regex matching
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Assuming bundles.py is in src/pipeline/ relative to the project root
# Adjust sys.path to allow importing bundles
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

try:
    from pipeline import bundles
except ImportError as exc:
    print("Pipeline module not found; ensure pipeline/ is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Validate workstream bundles for authoring.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Directory containing workstream JSON files. Defaults to project_root/workstreams or PIPELINE_WORKSTREAM_DIR env var."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format for machine readability."
    )
    args = parser.parse_args()

    output_json: Dict[str, Any] = {
        "ok": False,
        "bundles_checked": 0,
        "errors": []
    }

    try:
        # Determine workstream directory
        if args.dir:
            workstream_dir = Path(args.dir).resolve()
        else:
            workstream_dir = bundles.get_workstream_dir()

        if not args.json:
            print(f"Resolved workstream_dir: {workstream_dir}", file=sys.stderr)

        if not workstream_dir.exists() or not workstream_dir.is_dir():
            raise FileNotFoundError(f"Workstream directory not found: {workstream_dir}")

        # Count files for bundles_checked
        json_files = list(workstream_dir.glob("*.json"))
        output_json["bundles_checked"] = len(json_files)

        # Load and validate bundles
        all_bundles = bundles.load_and_validate_bundles(workstream_dir=workstream_dir)
        # If load_and_validate_bundles succeeds, output_json["bundles_checked"] is already set
        # and reflects the number of files found.

        if not args.json:
            print(f"Loaded {len(all_bundles)} bundles.", file=sys.stderr)
            # for b in all_bundles:
            #     print(f"Bundle ID: {b.id}, Files Scope: {b.files_scope}", file=sys.stderr)

        # Detect file scope overlaps
        overlaps = bundles.detect_filescope_overlaps(all_bundles)

        if overlaps:
            for file_path, ws_ids in overlaps.items():
                output_json["errors"].append({
                    "type": "overlap",
                    "file": file_path,
                    "id": None, # Overlap is not tied to a single bundle ID
                    "details": f"File '{file_path}' is claimed by multiple workstreams: {', '.join(ws_ids)}"
                })
            raise bundles.FileScopeOverlapError("File scope overlaps detected.")

        output_json["ok"] = True

        if args.json:
            print(json.dumps(output_json, indent=2))
        else:
            print(f"{len(all_bundles)} workstream bundles validated successfully.")
        sys.exit(0)

    except (
        bundles.BundleValidationError,
        bundles.BundleDependencyError,
        bundles.BundleCycleError,
        bundles.FileScopeOverlapError,
        FileNotFoundError
    ) as e:
        if not args.json:
            print(f"Validation failed: {e}", file=sys.stderr)
            if isinstance(e, bundles.FileScopeOverlapError):
                for error_detail in output_json["errors"]:
                    if error_detail["type"] == "overlap":
                        print(f"  - {error_detail['details']}", file=sys.stderr)

        # Populate error details for JSON output
        if isinstance(e, bundles.BundleValidationError):
            # Attempt to parse jsonschema errors for better reporting
            # This is a bit fragile as it depends on the error message format
            match = re.search(r"id=(?P<id>[^)]+)\s+\((?P<file>[^)]+)\):\s+(?P<details>.+)", str(e))
            if match:
                output_json["errors"].append({
                    "type": "schema",
                    "file": match.group("file").strip(),
                    "id": match.group("id").strip(),
                    "details": match.group("details").strip()
                })
            else:
                output_json["errors"].append({
                    "type": "schema",
                    "file": None,
                    "id": None,
                    "details": str(e)
                })
        elif isinstance(e, bundles.BundleDependencyError):
            output_json["errors"].append({
                "type": "dependency",
                "file": None,
                "id": None,
                "details": str(e)
            })
        elif isinstance(e, bundles.BundleCycleError):
            output_json["errors"].append({
                "type": "cycle",
                "file": None,
                "id": None,
                "details": str(e)
            })
        elif isinstance(e, bundles.FileScopeOverlapError):
            # Overlaps are already added to output_json["errors"]
            pass # The errors were added before the raise
        elif isinstance(e, FileNotFoundError):
            output_json["errors"].append({
                "type": "config",
                "file": None,
                "id": None,
                "details": str(e)
            })
        else:
            output_json["errors"].append({
                "type": "unknown",
                "file": None,
                "id": None,
                "details": str(e)
            })

        # Always print JSON to stdout if --json is specified, even on error
        if args.json:
            print(json.dumps(output_json, indent=2))
        sys.exit(1)
    except Exception as e:
        if not args.json:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
        output_json["errors"].append({
            "type": "unexpected",
            "file": None,
            "id": None,
            "details": str(e)
        })
        # Always print JSON to stdout if --json is specified, even on error
        if args.json:
            print(json.dumps(output_json, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
