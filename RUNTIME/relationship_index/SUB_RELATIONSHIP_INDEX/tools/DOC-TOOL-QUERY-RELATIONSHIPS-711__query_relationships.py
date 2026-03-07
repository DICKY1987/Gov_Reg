#!/usr/bin/env python3
# DOC_LINK: DOC-TOOL-QUERY-RELATIONSHIPS-711
"""
Query Relationships CLI

Command-line tool for querying the relationship index graph.

Usage:
    # Find dependencies
    python query_relationships.py deps DOC-CORE-FOO-001

    # Find dependents (what depends on this?)
    python query_relationships.py dependents DOC-CORE-FOO-001

    # Transitive dependencies
    python query_relationships.py deps DOC-CORE-FOO-001 --transitive

    # Impact analysis
    python query_relationships.py impact DOC-CORE-FOO-001

    # Detect cycles
    python query_relationships.py cycles

    # Find path
    python query_relationships.py path DOC-A DOC-B

    # Graph statistics
    python query_relationships.py stats
"""
# DOC_ID: DOC-TOOL-QUERY-RELATIONSHIPS-711

import sys
import argparse
import json
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
.parent.parent))

from core.graph_index import GraphIndex


def format_list(items: List[str], max_items: int = 20) -> str:
    """Format a list of items for display."""
    if not items:
        return "  (none)"

    lines = []
    for i, item in enumerate(items[:max_items]):
        lines.append(f"  {i+1}. {item}")

    if len(items) > max_items:
        lines.append(f"  ... and {len(items) - max_items} more")

    return "\n".join(lines)


def cmd_deps(graph: GraphIndex, args):
    """Find dependencies of a doc_id."""
    doc_id = args.doc_id

    print(f"\n=== Dependencies of {doc_id} ===\n")

    # Get node info
    node = graph.get_node_info(doc_id)
    if not node:
        print(f"❌ Error: doc_id '{doc_id}' not found")
        return 1

    print(f"File: {node['path']}")
    print(f"Type: {node['file_type']}\n")

    # Get dependencies
    deps = graph.get_dependencies(
        doc_id,
        edge_type=args.type,
        transitive=args.transitive,
        max_depth=args.depth
    )

    if args.transitive:
        print(f"Transitive Dependencies (depth={args.depth or 'unlimited'}):")
    else:
        print("Direct Dependencies:")

    print(format_list(deps))
    print(f"\nTotal: {len(deps)}")

    return 0


def cmd_dependents(graph: GraphIndex, args):
    """Find dependents of a doc_id (reverse lookup)."""
    doc_id = args.doc_id

    print(f"\n=== Dependents of {doc_id} ===\n")

    # Get node info
    node = graph.get_node_info(doc_id)
    if not node:
        print(f"❌ Error: doc_id '{doc_id}' not found")
        return 1

    print(f"File: {node['path']}")
    print(f"Type: {node['file_type']}\n")

    # Get dependents
    dependents = graph.get_dependents(
        doc_id,
        edge_type=args.type,
        transitive=args.transitive,
        max_depth=args.depth
    )

    if args.transitive:
        print(f"Transitive Dependents (depth={args.depth or 'unlimited'}):")
    else:
        print("Direct Dependents:")

    print(format_list(dependents))
    print(f"\nTotal: {len(dependents)}")

    return 0


def cmd_impact(graph: GraphIndex, args):
    """Analyze impact of changing a doc_id."""
    doc_id = args.doc_id

    print(f"\n=== Impact Analysis: {doc_id} ===\n")

    # Get node info
    node = graph.get_node_info(doc_id)
    if not node:
        print(f"❌ Error: doc_id '{doc_id}' not found")
        return 1

    print(f"File: {node['path']}")
    print(f"Type: {node['file_type']}\n")

    # Run impact analysis
    impact = graph.impact_analysis(doc_id, max_depth=args.depth)

    print(f"Risk Level: {impact['risk_level'].upper()}")
    print(f"Total Impact: {impact['total_impact']} files affected\n")

    print(f"Direct Dependents: {len(impact['direct_dependents'])}")
    print(format_list(impact['direct_dependents'], max_items=10))

    if impact['transitive_dependents']:
        print(f"\nTransitive Dependents: {len(impact['transitive_dependents'])}")
        print(format_list(impact['transitive_dependents'], max_items=10))

    print(f"\nDepth Distribution:")
    for depth, count in sorted(impact['depth_distribution'].items()):
        print(f"  Depth {depth}: {count} files")

    return 0


def cmd_path(graph: GraphIndex, args):
    """Find path between two doc_ids."""
    source = args.source
    target = args.target

    print(f"\n=== Path from {source} to {target} ===\n")

    path = graph.find_path(source, target)

    if path is None:
        print("❌ No path found")
        return 1

    print(f"Shortest path ({len(path)-1} hops):\n")
    for i, doc_id in enumerate(path):
        node = graph.get_node_info(doc_id)
        prefix = "  " * i
        print(f"{prefix}{'→ ' if i > 0 else ''}{doc_id}")
        print(f"{prefix}   ({node['path']})")

    return 0


def cmd_cycles(graph: GraphIndex, args):
    """Detect circular dependencies."""
    print("\n=== Circular Dependencies ===\n")

    print("Detecting cycles...")
    cycles = graph.find_cycles()

    if not cycles:
        print("✅ No cycles detected! Graph is acyclic.")
        return 0

    print(f"❌ Found {len(cycles)} cycle(s):\n")

    for i, cycle in enumerate(cycles[:args.max_cycles], 1):
        print(f"Cycle {i} (length {len(cycle)-1}):")
        for j, doc_id in enumerate(cycle):
            print(f"  {j+1}. {doc_id}")
        print()

    if len(cycles) > args.max_cycles:
        print(f"... and {len(cycles) - args.max_cycles} more cycles")

    return 1  # Exit with error if cycles found


def cmd_stats(graph: GraphIndex, args):
    """Show graph statistics."""
    print("\n=== Graph Statistics ===\n")

    stats = graph.get_stats()

    print(f"Total Nodes: {stats['total_nodes']:,}")
    print(f"Total Edges: {stats['total_edges']:,}")
    print(f"Isolated Nodes: {stats['isolated_nodes']:,}")
    print(f"\nAverage Out-Degree: {stats['avg_out_degree']:.2f}")
    print(f"Average In-Degree: {stats['avg_in_degree']:.2f}")
    print(f"Max Out-Degree: {stats['max_out_degree']}")
    print(f"Max In-Degree: {stats['max_in_degree']}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Query relationship index graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--index",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "RELATIONSHIP_INDEX.json",
        help="Path to relationship index JSON file"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # deps command
    deps_parser = subparsers.add_parser("deps", help="Find dependencies")
    deps_parser.add_argument("doc_id", help="Document ID")
    deps_parser.add_argument("--transitive", action="store_true", help="Include transitive dependencies")
    deps_parser.add_argument("--type", help="Filter by edge type (imports, documents, etc.)")
    deps_parser.add_argument("--depth", type=int, help="Max depth for transitive search")

    # dependents command
    dependents_parser = subparsers.add_parser("dependents", help="Find dependents (reverse)")
    dependents_parser.add_argument("doc_id", help="Document ID")
    dependents_parser.add_argument("--transitive", action="store_true", help="Include transitive dependents")
    dependents_parser.add_argument("--type", help="Filter by edge type")
    dependents_parser.add_argument("--depth", type=int, help="Max depth for transitive search")

    # impact command
    impact_parser = subparsers.add_parser("impact", help="Impact analysis")
    impact_parser.add_argument("doc_id", help="Document ID")
    impact_parser.add_argument("--depth", type=int, default=3, help="Max depth (default: 3)")

    # path command
    path_parser = subparsers.add_parser("path", help="Find shortest path")
    path_parser.add_argument("source", help="Source document ID")
    path_parser.add_argument("target", help="Target document ID")

    # cycles command
    cycles_parser = subparsers.add_parser("cycles", help="Detect circular dependencies")
    cycles_parser.add_argument("--max-cycles", type=int, default=10, help="Max cycles to display")

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show graph statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load graph
    try:
        graph = GraphIndex(args.index)
    except FileNotFoundError:
        print(f"❌ Error: Index file not found: {args.index}")
        print("\nRun: python tools/build_relationship_index.py --output data/RELATIONSHIP_INDEX.json")
        return 1
    except Exception as e:
        print(f"❌ Error loading index: {e}")
        return 1

    # Execute command
    commands = {
        "deps": cmd_deps,
        "dependents": cmd_dependents,
        "impact": cmd_impact,
        "path": cmd_path,
        "cycles": cmd_cycles,
        "stats": cmd_stats
    }

    handler = commands.get(args.command)
    if handler:
        return handler(graph, args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
