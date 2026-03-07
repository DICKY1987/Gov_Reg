# DOC_LINK: DOC-CORE-CORE-EDGE-ID-GENERATOR-534
"""
Edge ID Generator

Generates stable, deterministic relationship edge IDs using SHA256 hashing.

Edge ID Format: REL-<SHA256(source:target:type)[:16]>

This ensures:
- Determinism: Same source/target/type always produces same ID
- Uniqueness: Different relationships get different IDs
- Stability: IDs don't change across runs
- Compactness: 16-char hex = 64 bits of entropy (collision probability ~10^-19)
"""
# DOC_ID: DOC-CORE-CORE-EDGE-ID-GENERATOR-534

import hashlib
from typing import Optional


def generate_edge_id(source_doc_id: str, target_doc_id: str, edge_type: str) -> str:
    """
    Generate a stable relationship edge ID.

    Args:
        source_doc_id: Source file doc_id (e.g., "DOC-CORE-ORCHESTRATOR-001")
        target_doc_id: Target file doc_id (e.g., "DOC-CORE-SCHEDULER-042")
        edge_type: Relationship type (e.g., "imports", "references_schema", "dot_sources")

    Returns:
        Edge ID in format REL-<16-char-hex>

    Examples:
        >>> generate_edge_id("DOC-A-001", "DOC-B-002", "imports")
        'REL-a1b2c3d4e5f6a7b8'

        >>> # Determinism: same inputs produce same output
        >>> id1 = generate_edge_id("DOC-X-001", "DOC-Y-002", "imports")
        >>> id2 = generate_edge_id("DOC-X-001", "DOC-Y-002", "imports")
        >>> id1 == id2
        True

        >>> # Different edge type = different ID
        >>> id_import = generate_edge_id("DOC-X-001", "DOC-Y-002", "imports")
        >>> id_ref = generate_edge_id("DOC-X-001", "DOC-Y-002", "references_schema")
        >>> id_import != id_ref
        True
    """
    # Canonical representation: source:target:type
    canonical = f"{source_doc_id}:{target_doc_id}:{edge_type}"

    # SHA256 hash
    hash_bytes = hashlib.sha256(canonical.encode('utf-8')).digest()

    # Convert to hex and take first 16 characters
    hash_hex = hash_bytes.hex()[:16]

    return f"REL-{hash_hex}"


def validate_edge_id_format(edge_id: str) -> bool:
    """
    Validate that an edge ID matches the expected format.

    Args:
        edge_id: Edge ID to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_edge_id_format("REL-a1b2c3d4e5f6a7b8")
        True

        >>> validate_edge_id_format("REL-xyz")  # Too short
        False

        >>> validate_edge_id_format("EDGE-a1b2c3d4e5f6a7b8")  # Wrong prefix
        False
    """
    if not edge_id.startswith("REL-"):
        return False

    hex_part = edge_id[4:]  # Remove "REL-" prefix

    if len(hex_part) != 16:
        return False

    # Check if all characters are valid hex
    try:
        int(hex_part, 16)
        return True
    except ValueError:
        return False


def parse_edge_id(edge_id: str) -> Optional[str]:
    """
    Extract the hash component from an edge ID.

    Args:
        edge_id: Edge ID to parse

    Returns:
        16-character hex hash, or None if invalid format

    Examples:
        >>> parse_edge_id("REL-a1b2c3d4e5f6a7b8")
        'a1b2c3d4e5f6a7b8'

        >>> parse_edge_id("invalid") is None
        True
    """
    if not validate_edge_id_format(edge_id):
        return None

    return edge_id[4:]  # Remove "REL-" prefix


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # Example usage
    print("\n=== Edge ID Generator Examples ===\n")

    # Example 1: Basic usage
    source = "DOC-CORE-ORCHESTRATOR-001"
    target = "DOC-CORE-SCHEDULER-042"
    edge_type = "imports"

    edge_id = generate_edge_id(source, target, edge_type)
    print(f"Source: {source}")
    print(f"Target: {target}")
    print(f"Type: {edge_type}")
    print(f"Edge ID: {edge_id}")
    print()

    # Example 2: Determinism
    id1 = generate_edge_id(source, target, edge_type)
    id2 = generate_edge_id(source, target, edge_type)
    print(f"Determinism check:")
    print(f"  First generation:  {id1}")
    print(f"  Second generation: {id2}")
    print(f"  Are identical: {id1 == id2}")
    print()

    # Example 3: Different edge types
    id_import = generate_edge_id(source, target, "imports")
    id_ref = generate_edge_id(source, target, "references_schema")
    id_dot = generate_edge_id(source, target, "dot_sources")
    print(f"Different edge types:")
    print(f"  imports:          {id_import}")
    print(f"  references_schema: {id_ref}")
    print(f"  dot_sources:      {id_dot}")
    print()

    # Example 4: Validation
    print(f"Validation:")
    print(f"  Valid ID:   {validate_edge_id_format(edge_id)} ({edge_id})")
    print(f"  Invalid ID: {validate_edge_id_format('WRONG-format')} (WRONG-format)")
