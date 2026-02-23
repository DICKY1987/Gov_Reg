#!/usr/bin/env python3
"""Capability mapping orchestrator."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).parents[1]
_here = Path(__file__).parent
sys.path.insert(0, str(_here / "src"))
sys.path.insert(0, str(_here / "mapp_py"))
sys.path.insert(0, str(repo_root / "01260207201000001250_REGISTRY" / "01260207201000001270_scripts"))
sys.path.insert(0, str(repo_root / "01260207201000001289_src" / "01260207201000001295_P_01999000042260124484_geu_governance"))
sys.path.insert(0, str(repo_root / "01260207201000001289_src"))
sys.path.insert(0, str(repo_root / "01260207201000001173_govreg_core"))
sys.path.insert(0, str(repo_root))

from P_01260207201000000982_P_01260207233100000YYY_capability_discoverer import CapabilityDiscoverer
from P_01260207201000000983_P_01260207233100000YYY_file_inventory_builder import FileInventoryBuilder
from P_01260207201000000984_P_01260207233100000YYY_purpose_registry_builder import PurposeRegistryBuilder
from P_01260207201000000985_P_01260207233100000YYY_registry_promoter import RegistryPromoter


DEFAULT_REGISTRY_ROOT = repo_root / "01260207201000001250_REGISTRY"
DEFAULT_FILE_REGISTRY = DEFAULT_REGISTRY_ROOT / "01999000042260124503_REGISTRY_file.json"
DEFAULT_COLUMN_DICTIONARY = DEFAULT_REGISTRY_ROOT / "01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json"


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return start.resolve()
        current = current.parent


def run_step1(repo_root: Path, output_root: Path, evidence_root: Path) -> bool:
    output_path = output_root / "CAPABILITIES.json"
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    discoverer = CapabilityDiscoverer()
    ok, _ = discoverer.discover_all(repo_root, output_path, evidence_root)
    return ok


def run_step2(repo_root: Path, output_root: Path, evidence_root: Path) -> bool:
    output_path = output_root / "FILE_INVENTORY.jsonl"
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    builder = FileInventoryBuilder(repo_root)
    return builder.build_inventory(output_path, evidence_root)


def run_step3(repo_root: Path, output_root: Path, evidence_root: Path, vocab_path: Path = None, overrides_path: Path = None) -> bool:
    capabilities_path = output_root / "CAPABILITIES.json"
    inventory_path = output_root / "FILE_INVENTORY.jsonl"
    if not capabilities_path.exists() or not inventory_path.exists():
        return False
    output_path = output_root / "FILE_PURPOSE_REGISTRY.json"
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    builder = PurposeRegistryBuilder(capabilities_path, inventory_path, repo_root, vocab_path, overrides_path)
    return builder.build_registry(output_path, evidence_root)


def run_step4(repo_root: Path, output_root: Path, evidence_root: Path, registry_root: Path, registry_mode: str) -> bool:
    mapping_path = output_root / "FILE_PURPOSE_REGISTRY.json"
    capabilities_path = output_root / "CAPABILITIES.json"
    if not mapping_path.exists():
        print(f"ERROR: Mapping file not found: {mapping_path}")
        return False
    if not capabilities_path.exists():
        print(f"ERROR: Capabilities file not found: {capabilities_path}")
        return False
    evidence_root.mkdir(parents=True, exist_ok=True)
    print(f"Step 4: Running registry promotion in {registry_mode} mode...")
    print(f"  Mapping: {mapping_path}")
    print(f"  Capabilities: {capabilities_path}")
    print(f"  Registry: {DEFAULT_FILE_REGISTRY}")
    print(f"  Column Dict: {DEFAULT_COLUMN_DICTIONARY}")
    promoter = RegistryPromoter(repo_root, registry_root, evidence_root)
    try:
        result = promoter.promote(
            mapping_path=mapping_path,
            capabilities_path=capabilities_path,
            registry_path=DEFAULT_FILE_REGISTRY,
            column_dict_path=DEFAULT_COLUMN_DICTIONARY,
            mode=registry_mode,
        )
        if result:
            print(f"Step 4: SUCCESS - Evidence at {evidence_root}")
        else:
            print(f"Step 4: FAILED - Check evidence at {evidence_root}")
        return result
    except Exception as e:
        print(f"Step 4: EXCEPTION - {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capability mapping orchestrator")
    parser.add_argument("--step", default="all", choices=["1", "2", "3", "4", "all"], help="Step to run")
    parser.add_argument("--repo-root", default=None, help="Repository root")
    parser.add_argument("--registry-root", default=None, help="Registry root")
    parser.add_argument("--registry-mode", default="dry-run", choices=["dry-run", "apply"], help="Registry mode")
    parser.add_argument("--vocab-path", default=None, help="Path to COMPONENT_CAPABILITY_VOCAB.json")
    parser.add_argument("--overrides-path", default=None, help="Path to SCRIPT_CLASSIFIER_OVERRIDES.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = find_repo_root(Path.cwd())

    output_root = repo_root / ".state" / "purpose_mapping"
    evidence_root = repo_root / ".state" / "evidence" / "purpose_mapping"
    evidence_root_step4 = repo_root / ".state" / "evidence" / "registry_integration" / "purpose_mapping"

    registry_root = Path(args.registry_root) if args.registry_root else DEFAULT_REGISTRY_ROOT
    
    vocab_path = Path(args.vocab_path) if args.vocab_path else _here / "schemas" / "COMPONENT_CAPABILITY_VOCAB.json"
    overrides_path = Path(args.overrides_path) if args.overrides_path else _here / "SCRIPT_CLASSIFIER_OVERRIDES.json"

    steps = [args.step] if args.step != "all" else ["1", "2", "3", "4"]
    results = {}

    if "1" in steps:
        results["step1"] = run_step1(repo_root, output_root, evidence_root)
    if "2" in steps:
        results["step2"] = run_step2(repo_root, output_root, evidence_root)
    if "3" in steps:
        results["step3"] = run_step3(repo_root, output_root, evidence_root, vocab_path, overrides_path)
    if "4" in steps:
        results["step4"] = run_step4(
            repo_root=repo_root,
            output_root=output_root,
            evidence_root=evidence_root_step4,
            registry_root=registry_root,
            registry_mode=args.registry_mode,
        )

    all_passed = all(results.values()) if results else True
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
