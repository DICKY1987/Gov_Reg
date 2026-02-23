#!/usr/bin/env python3
"""
Demonstration: Path Abstraction Solves File Organization Problem

This script demonstrates how path abstraction allows files to be
reorganized without breaking imports or path references.

FILE_ID: 01999000042260126006
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def demo_path_resolution():
    """Demonstrate resolving paths by semantic keys."""
    print("=" * 70)
    print("DEMO 1: Path Resolution")
    print("=" * 70)
    
    from path_registry import resolve_path
    
    keys = [
        "REGISTRY_UNIFIED",
        "SCHEMA_V3",
        "ID_COUNTER",
        "SHARED_UTILS",
        "ID_ALLOCATOR"
    ]
    
    print("\n✅ Resolving paths by semantic keys:\n")
    for key in keys:
        try:
            path = resolve_path(key)
            print(f"  {key:25} -> {path.name}")
        except Exception as e:
            print(f"  {key:25} -> ERROR: {e}")
    
    print("\n💡 These files can move anywhere!")
    print("   Just update PATH_FILES/path_index.yaml")


def demo_dynamic_import():
    """Demonstrate dynamic module importing."""
    print("\n" + "=" * 70)
    print("DEMO 2: Dynamic Module Import")
    print("=" * 70)
    
    from path_registry import import_module
    
    print("\n✅ Dynamically importing ID_ALLOCATOR:\n")
    
    try:
        id_allocator = import_module("ID_ALLOCATOR")
        print(f"  Module name: {id_allocator.__name__}")
        print(f"  Module file: {id_allocator.__file__}")
        print(f"  Has allocate_single_id: {hasattr(id_allocator, 'allocate_single_id')}")
        print(f"  Has allocate_batch_ids: {hasattr(id_allocator, 'allocate_batch_ids')}")
        
        print("\n💡 Import works even if file moves to scripts/ folder!")
    except Exception as e:
        print(f"  ERROR: {e}")


def demo_fallback_pattern():
    """Demonstrate fallback import pattern."""
    print("\n" + "=" * 70)
    print("DEMO 3: Backward-Compatible Fallback")
    print("=" * 70)
    
    print("\n✅ Using fallback pattern for compatibility:\n")
    
    code = '''
try:
    from path_registry import resolve_path
    REGISTRY_PATH = resolve_path("REGISTRY_UNIFIED")
    print(f"  Using path registry: {REGISTRY_PATH.name}")
except ImportError:
    REGISTRY_PATH = Path(__file__).parent / "registry.json"
    print(f"  Using fallback: {REGISTRY_PATH}")
'''
    
    print("  Code:")
    for line in code.strip().split('\n'):
        print(f"    {line}")
    
    exec(code)
    
    print("\n💡 Works with or without path_registry!")


def demo_before_after():
    """Show before/after comparison."""
    print("\n" + "=" * 70)
    print("DEMO 4: Before vs After Comparison")
    print("=" * 70)
    
    print("\n❌ BEFORE (Hardcoded - Breaks when files move):")
    print("   " + "-" * 66)
    
    before_code = [
        "# Import with hardcoded module name",
        "from P_01999000042260124027_id_allocator import allocate_single_id",
        "",
        "# Path with hardcoded location",
        'REGISTRY_PATH = Path(__file__).parent / "registry.json"',
        "",
        "# ❌ Breaks when:",
        "#   - Files move to scripts/",
        "#   - Files reorganize into packages",
        "#   - Running with python -m",
    ]
    
    for line in before_code:
        print(f"   {line}")
    
    print("\n✅ AFTER (Path Abstraction - Works anywhere):")
    print("   " + "-" * 66)
    
    after_code = [
        "# Import with semantic key",
        "from path_registry import import_module",
        "id_allocator = import_module('ID_ALLOCATOR')",
        "allocate_single_id = id_allocator.allocate_single_id",
        "",
        "# Path with semantic key",
        "from path_registry import resolve_path",
        "REGISTRY_PATH = resolve_path('REGISTRY_UNIFIED')",
        "",
        "# ✅ Works even when:",
        "#   - Files move to scripts/ (update path_index.yaml)",
        "#   - Files reorganize into packages",
        "#   - Running from any directory",
        "#   - Using python script.py or python -m script",
    ]
    
    for line in after_code:
        print(f"   {line}")


def demo_registry_stats():
    """Show registry statistics."""
    print("\n" + "=" * 70)
    print("DEMO 5: Registry Statistics")
    print("=" * 70)
    
    from path_registry import get_registry
    
    registry = get_registry()
    
    print(f"\n📊 Current Registry Status:\n")
    print(f"  Repo root: {registry.repo_root}")
    print(f"  Index file: {registry.index_path.name}")
    print(f"  Total entries: {len(registry._paths)}")
    
    # Count by kind
    by_kind = {}
    for key, entry in registry._paths.items():
        kind = entry.get('kind', 'unknown')
        by_kind[kind] = by_kind.get(kind, 0) + 1
    
    print(f"\n  Breakdown by kind:")
    for kind, count in sorted(by_kind.items()):
        print(f"    {kind:20} : {count:2} entries")
    
    print(f"\n💡 All {len(registry._paths)} resources are location-independent!")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" PATH ABSTRACTION SYSTEM - LIVE DEMONSTRATION")
    print("=" * 70)
    print("\nShowing how path abstraction solves file organization problems...")
    
    try:
        demo_path_resolution()
        demo_dynamic_import()
        demo_fallback_pattern()
        demo_before_after()
        demo_registry_stats()
        
        print("\n" + "=" * 70)
        print(" ✅ ALL DEMONSTRATIONS COMPLETE")
        print("=" * 70)
        
        print("\n📚 Summary:")
        print("  • Files can move freely - just update path_index.yaml")
        print("  • No broken imports - dynamic resolution")
        print("  • Location independent - works from any directory")
        print("  • Backward compatible - fallback patterns included")
        print("\n  Ready to move files to scripts/ folder! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
