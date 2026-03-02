import argparse
import importlib.util
from pathlib import Path


def load_classifier_module(repo_root):
    classifier_path = repo_root / "scripts" / "P_01260207201000000001_classify_all_files.py"
    if not classifier_path.exists():
        raise FileNotFoundError(f"Classifier script not found: {classifier_path}")
    spec = importlib.util.spec_from_file_location("classify_all_files", classifier_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description="Validate file classification against expected section.")
    parser.add_argument("--file", required=True, help="File path (relative to repo root or absolute).")
    parser.add_argument("--expected-section", required=True, help="Expected classification section.")
    parser.add_argument("--root", default=None, help="Repository root (default: parent of validators).")
    parser.add_argument(
        "--registry",
        default=None,
        help="Unified registry JSON (default: 01999000042260124503_governance_registry_unified.json).",
    )
    parser.add_argument("--max-lines", type=int, default=50, help="Max lines to scan for content signals.")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = repo_root / file_path
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    classifier = load_classifier_module(repo_root)
    expected = classifier.normalize_section_name(args.expected_section)
    if not expected:
        print(f"Unknown expected section: {args.expected_section}")
        print("Valid sections:")
        for section in classifier.SECTIONS:
            print(f"- {section}")
        return 1

    registry_path = (
        Path(args.registry).resolve()
        if args.registry
        else repo_root / "01999000042260124503_governance_registry_unified.json"
    )
    registry_index = classifier.load_registry_index(registry_path, repo_root)
    result = classifier.classify_file(file_path, repo_root, registry_index, args.max_lines)

    match = result["section"] == expected
    print(f"file: {result['path']}")
    print(f"expected: {expected}")
    print(f"classified: {result['section']}")
    print(f"confidence: {result['confidence']}")
    if result.get("signals"):
        print("signals:")
        for signal in result["signals"]:
            print(f"- {signal}")

    return 0 if match else 1


if __name__ == "__main__":
    raise SystemExit(main())
