#!/usr/bin/env python3
"""
Similarity Clusterer - Batch Duplicate Detection
DOC-SCRIPT-XXXX-CLUSTER

Produces: py_overlap_group_id

Clusters files by exact py_deliverable_signature_hash match.
Files with identical deliverable signatures are grouped together
for duplicate detection and consolidation.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Iterable, Any
from collections import defaultdict


def cluster_by_hash(records: Iterable[dict]) -> Dict[str, List[str]]:
    """
    Cluster files by deliverable signature hash.
    
    Args:
        records: Iterable of dicts with 'file_id' and 'py_deliverable_signature_hash'
        
    Returns:
        Dict mapping cluster_key → list of file_ids
    """
    clusters = defaultdict(list)
    
    for record in records:
        file_id = record.get('file_id')
        sig_hash = record.get('py_deliverable_signature_hash')
        
        if not file_id:
            continue
        
        if sig_hash:
            # Group by signature hash (exact match)
            clusters[sig_hash].append(file_id)
        else:
            # Singleton cluster for files without signature
            singleton_key = f"SINGLETON_{file_id}"
            clusters[singleton_key].append(file_id)
    
    return dict(clusters)


def assign_group_ids(clusters: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Assign deterministic group IDs to clusters.
    
    Group ID is computed from sorted file_ids in cluster to ensure:
    - Determinism: same cluster contents → same group_id
    - Stability: group_id doesn't change when files reordered
    
    Args:
        clusters: Dict mapping cluster_key → list of file_ids
        
    Returns:
        Dict mapping file_id → py_overlap_group_id
    """
    file_to_group = {}
    
    for cluster_key, file_ids in clusters.items():
        # Sort for determinism
        sorted_ids = sorted(file_ids)
        
        # Generate deterministic group ID
        if cluster_key.startswith('SINGLETON_'):
            # Singleton clusters get their own ID format
            group_id = cluster_key
        else:
            # Multi-file clusters: hash of sorted file_id list
            group_content = '|'.join(sorted_ids)
            group_hash = hashlib.sha256(group_content.encode('utf-8')).hexdigest()[:12]
            group_id = f"OVERLAP_{group_hash.upper()}"
        
        # Assign same group_id to all files in cluster
        for file_id in file_ids:
            file_to_group[file_id] = group_id
    
    return file_to_group


def cluster_files(records: Iterable[dict]) -> Dict[str, str]:
    """
    Main entry point: cluster files and assign group IDs.
    
    Args:
        records: Iterable of file records with py_deliverable_signature_hash
        
    Returns:
        Dict mapping file_id → py_overlap_group_id
    """
    clusters = cluster_by_hash(records)
    return assign_group_ids(clusters)


def generate_cluster_report(file_to_group: Dict[str, str]) -> dict:
    """
    Generate cluster statistics report.
    
    Args:
        file_to_group: Mapping of file_id → group_id
        
    Returns:
        Dict with cluster statistics
    """
    from collections import Counter
    
    group_counter = Counter(file_to_group.values())
    
    # Count cluster sizes
    singleton_count = sum(1 for g in group_counter.keys() if g.startswith('SINGLETON_'))
    multi_file_clusters = {g: c for g, c in group_counter.items() if not g.startswith('SINGLETON_')}
    
    # Find largest clusters
    largest = sorted(multi_file_clusters.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'total_files': len(file_to_group),
        'total_clusters': len(group_counter),
        'singleton_clusters': singleton_count,
        'multi_file_clusters': len(multi_file_clusters),
        'largest_clusters': [
            {'group_id': g, 'file_count': c} for g, c in largest
        ],
        'duplicate_candidates': sum(c - 1 for c in multi_file_clusters.values())
    }


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Cluster files by deliverable signature'
    )
    parser.add_argument('--registry-json', required=True, 
                       help='Registry file with py_deliverable_signature_hash')
    parser.add_argument('--output', required=True, 
                       help='Output JSON (file_id → group_id mapping)')
    parser.add_argument('--report', help='Optional cluster statistics report file')
    parser.add_argument('--min-cluster-size', type=int, default=2,
                       help='Minimum cluster size to report (default: 2)')
    
    args = parser.parse_args()
    
    # Load registry
    try:
        with open(args.registry_json, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        print(f"Error loading registry: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get file records
    records = registry.get('files', [])
    if not records:
        print("No files found in registry", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(records)} file records...", file=sys.stderr)
    
    # Cluster files
    file_to_group = cluster_files(records)
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(file_to_group, f, indent=2, sort_keys=True)
    
    print(f"✓ Cluster assignments written to: {args.output}", file=sys.stderr)
    
    # Generate and optionally write report
    report = generate_cluster_report(file_to_group)
    
    print(f"\nCluster Statistics:", file=sys.stderr)
    print(f"  Total files: {report['total_files']}", file=sys.stderr)
    print(f"  Total clusters: {report['total_clusters']}", file=sys.stderr)
    print(f"  Singleton clusters: {report['singleton_clusters']}", file=sys.stderr)
    print(f"  Multi-file clusters: {report['multi_file_clusters']}", file=sys.stderr)
    print(f"  Duplicate candidates: {report['duplicate_candidates']}", file=sys.stderr)
    
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"\n✓ Cluster report written to: {args.report}", file=sys.stderr)
    
    # Show largest clusters
    if report['largest_clusters']:
        print(f"\nLargest clusters:", file=sys.stderr)
        for cluster in report['largest_clusters'][:5]:
            if cluster['file_count'] >= args.min_cluster_size:
                print(f"  {cluster['group_id']}: {cluster['file_count']} files", file=sys.stderr)
    
    sys.exit(0)
