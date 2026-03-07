#!/usr/bin/env python3
"""
Component ID Generator - Phase A Core Script
Produces: py_component_ids (assigns stable IDs to each component)

Generates deterministic IDs for Python components using file_id + component signature.
CRITICAL: Uses file_id (20-digit), NOT doc_id.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def generate_component_signature(component: Dict[str, Any]) -> str:
    """
    Generate canonical signature for a component.

    Signature includes:
    - kind (class/function/method)
    - qualname (fully qualified name)
    - args (for functions/methods)
    - decorators
    - base classes (for classes)
    """
    sig_parts = [component["kind"], component["qualname"]]

    # Add args for functions/methods
    if component["kind"] in ("function", "method"):
        args = component.get("args", [])
        arg_sig = ",".join(
            [f"{arg['name']}:{arg.get('annotation', '')}" for arg in args]
        )
        sig_parts.append(arg_sig)

    # Add bases for classes
    if component["kind"] == "class":
        bases = component.get("bases", [])
        sig_parts.append(",".join(sorted(bases)))

    # Add decorators
    decorators = component.get("decorators", [])
    if decorators:
        sig_parts.append(",".join(sorted(decorators)))

    return "|".join(sig_parts)


def generate_component_id(file_id: str, component: Dict[str, Any]) -> str:
    """
    Generate stable component ID.

    Format: {file_id}::{component_hash}

    Args:
        file_id: 20-digit file identifier (string)
        component: Component dictionary

    Returns:
        Component ID string
    """
    signature = generate_component_signature(component)

    # Hash the signature for compact ID
    sig_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]

    return f"{file_id}::{sig_hash}"


def assign_component_ids(file_id: str, components: List[Dict[str, Any]]) -> dict:
    """
    Assign IDs to all components in a file.

    Args:
        file_id: 20-digit file identifier (must be string)
        components: List of component dictionaries

    Returns dict with:
    - py_component_ids: Dict[str, str] (qualname -> component_id)
    - components_with_ids: List[Dict] (components with id field added)
    - success: bool
    - error: Optional[str]
    """
    try:
        # Validate file_id format
        if not isinstance(file_id, str):
            raise ValueError(f"file_id must be string, got {type(file_id)}")

        if not file_id.isdigit() or len(file_id) != 20:
            raise ValueError(f"file_id must be 20-digit string, got: {file_id}")

        component_ids = {}
        components_with_ids = []

        for component in components:
            qualname = component["qualname"]
            component_id = generate_component_id(file_id, component)

            component_ids[qualname] = component_id

            # Add ID to component
            component_copy = component.copy()
            component_copy["component_id"] = component_id
            components_with_ids.append(component_copy)

        return {
            "py_component_ids": component_ids,
            "components_with_ids": components_with_ids,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_component_ids": {},
            "components_with_ids": [],
            "success": False,
            "error": f"Component ID generation failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: component_id_generator.py <file_id> <components_json>",
            file=sys.stderr,
        )
        print("  file_id: 20-digit file identifier (string)", file=sys.stderr)
        print(
            "  components_json: Path to JSON file with components list", file=sys.stderr
        )
        sys.exit(1)

    file_id = sys.argv[1]
    components_path = Path(sys.argv[2])

    if not components_path.exists():
        print(f"Error: Components file not found: {components_path}", file=sys.stderr)
        sys.exit(1)

    try:
        components = json.loads(components_path.read_text())
    except Exception as e:
        print(f"Error: Failed to load components JSON: {e}", file=sys.stderr)
        sys.exit(1)

    result = assign_component_ids(file_id, components)
    
    # Handle --json flag (after positional args processed)
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        out_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if out_path:
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2, sort_keys=True)
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(0)

    if result["success"]:
        print(f"Generated {len(result['py_component_ids'])} component IDs")
        print(json.dumps(result["py_component_ids"], indent=2))
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
