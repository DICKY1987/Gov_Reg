#!/usr/bin/env python3
"""
Component ID Generator for mapp_py Analysis Pipeline
Produces: py_component_ids_list

Generates stable, unique identifiers for each component.
CRITICAL: Uses file_id (not doc_id) as mandated by SSOT.
"""

import hashlib
import json
import sys
from typing import List, Dict, Any


def generate_component_id(
    file_id: str, component_kind: str, qualname: str, signature_hash: str
) -> str:
    """
    Generate deterministic component ID.

    Format: sha256({file_id}|{kind}|{qualname}|{signature_hash})[:16]

    Args:
        file_id: 20-digit file identifier (MUST be file_id, not doc_id)
        component_kind: 'class', 'function', or 'method'
        qualname: Fully qualified name (e.g., 'MyClass.my_method')
        signature_hash: Hash of signature (args + returns)

    Returns:
        16-character hex component ID
    """
    # Validate file_id format (20 digits, string type)
    if not isinstance(file_id, str) or len(file_id) != 20 or not file_id.isdigit():
        raise ValueError(
            f"Invalid file_id: must be 20-digit string, got {repr(file_id)}"
        )

    # Build deterministic input
    id_input = f"{file_id}|{component_kind}|{qualname}|{signature_hash}"

    # Hash and truncate
    full_hash = hashlib.sha256(id_input.encode("utf-8")).hexdigest()
    return full_hash[:16]


def compute_signature_hash(signature: Dict[str, Any]) -> str:
    """
    Compute deterministic hash of function/method signature.

    Args:
        signature: Dictionary with 'args' and 'returns'

    Returns:
        SHA256 hex digest of canonical signature
    """
    # Canonical JSON encoding
    canonical = json.dumps(signature, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_component_ids(file_id: str, components_json: str) -> List[str]:
    """
    Generate component IDs for all components in a file.

    Args:
        file_id: 20-digit file identifier
        components_json: JSON string of components from component_extractor

    Returns:
        List of component IDs in same order as components
    """
    components = json.loads(components_json)
    component_ids = []

    for component in components:
        kind = component["kind"]
        qualname = component["qualname"]

        # Compute signature hash
        if "signature" in component:
            sig_hash = compute_signature_hash(component["signature"])
        else:
            # Classes don't have signatures, use empty
            sig_hash = hashlib.sha256(b"").hexdigest()

        # Generate component ID
        comp_id = generate_component_id(file_id, kind, qualname, sig_hash)
        component_ids.append(comp_id)

        # Process methods if class
        if kind == "class" and "methods" in component:
            for method in component["methods"]:
                method_qualname = method["qualname"]
                method_sig_hash = compute_signature_hash(method["signature"])
                method_id = generate_component_id(
                    file_id, "method", method_qualname, method_sig_hash
                )
                component_ids.append(method_id)

    return component_ids


def analyze_file(file_id: str, components_json: str) -> dict:
    """
    Generate component IDs for a file.

    Args:
        file_id: 20-digit file identifier
        components_json: JSON string of components

    Returns:
        Dictionary with py_component_ids_list
    """
    try:
        component_ids = generate_component_ids(file_id, components_json)

        return {"py_component_ids_list": component_ids}

    except Exception as e:
        return {"py_component_ids_list": None, "error": f"{type(e).__name__}: {str(e)}"}


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate component IDs for Python file"
    )
    parser.add_argument("file_id", help="20-digit file identifier")
    parser.add_argument(
        "components_json", help="Path to components JSON file or JSON string"
    )

    args = parser.parse_args()

    # Load components JSON
    try:
        from pathlib import Path

        if Path(args.components_json).exists():
            components_json = Path(args.components_json).read_text()
        else:
            components_json = args.components_json
    except:
        components_json = args.components_json

    result = analyze_file(args.file_id, components_json)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Generated {len(result['py_component_ids_list'])} component IDs:")
    for comp_id in result["py_component_ids_list"]:
        print(f"  {comp_id}")

    sys.exit(0)


if __name__ == "__main__":
    main()
