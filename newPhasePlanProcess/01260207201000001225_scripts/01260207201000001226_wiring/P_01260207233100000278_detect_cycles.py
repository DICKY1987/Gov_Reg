#!/usr/bin/env python3
"""FM-06: Circular Dependencies Detection"""
import argparse, json, sys
from pathlib import Path

def detect_cycle(graph, node, visited, stack):
    visited.add(node)
    stack.add(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if detect_cycle(graph, neighbor, visited, stack):
                return True
        elif neighbor in stack:
            return True

    stack.remove(node)
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    phases = data.get('plan', {}).get('phases_by_id', {})
    graph = {pid: pdata.get('depends_on', []) for pid, pdata in phases.items()}

    has_cycle = any(detect_cycle(graph, node, set(), set()) for node in graph)

    print(f"{'✅ PASSED' if not has_cycle else '❌ CYCLE'}: Cycle {'detected' if has_cycle else 'not found'}")
    sys.exit(0 if not has_cycle else 1)

if __name__ == '__main__':
    main()
