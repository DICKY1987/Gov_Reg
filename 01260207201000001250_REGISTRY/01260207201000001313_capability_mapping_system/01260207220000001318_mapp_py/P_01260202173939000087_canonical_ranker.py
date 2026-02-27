#!/usr/bin/env python3
"""
Canonical Ranker - Best Version Selection
DOC-SCRIPT-XXXX-CANON

Produces: py_canonical_candidate_score (0-100)

Ranks files within overlap groups and selects the best (canonical) version
based on quality metrics, test coverage, recency, and other factors.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict


def calculate_canonical_score(file_record: dict, group_context: dict) -> float:
    """
    Calculate canonical candidate score for a file within its overlap group.
    
    Scoring factors:
    - Quality score (40%)
    - Test coverage (25%)
    - Recency (20%)
    - Simplicity (15%) - fewer duplicates in group = bonus
    
    Args:
        file_record: File record with py_* metrics
        group_context: Context about the overlap group (size, avg_quality, etc.)
        
    Returns:
        Score 0-100
    """
    score = 0.0
    group_size = group_context.get('group_size', 1)
    
    # Quality score component (40 points)
    quality = file_record.get('py_quality_score', 0) or 0
    score += (quality / 100.0) * 40
    
    # Coverage component (25 points)
    coverage = file_record.get('py_coverage_percent', 0) or 0
    score += (coverage / 100.0) * 25
    
    # Recency component (20 points)
    # Prefer recently updated files (indicates active maintenance)
    mtime_utc = file_record.get('mtime_utc')
    last_seen_utc = file_record.get('last_seen_utc')
    
    recency_score = 0
    if mtime_utc or last_seen_utc:
        try:
            # Try to parse timestamp
            timestamp_str = mtime_utc or last_seen_utc
            if 'T' in timestamp_str:
                file_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                file_time = datetime.fromisoformat(timestamp_str)
            
            # Calculate days since last update
            now = datetime.now(timezone.utc)
            days_old = (now - file_time.astimezone(timezone.utc)).days
            
            # Full points if updated in last 90 days, scale down
            if days_old <= 90:
                recency_score = 20
            elif days_old <= 180:
                recency_score = 15
            elif days_old <= 365:
                recency_score = 10
            else:
                recency_score = 5
        except (ValueError, AttributeError):
            recency_score = 10  # Unknown = neutral
    else:
        recency_score = 10  # Unknown = neutral
    
    score += recency_score
    
    # Simplicity bonus (15 points)
    # Prefer files from smaller overlap groups (less duplication)
    if group_size == 1:
        simplicity_score = 15  # No duplicates = perfect
    elif group_size == 2:
        simplicity_score = 12
    elif group_size <= 3:
        simplicity_score = 10
    elif group_size <= 5:
        simplicity_score = 7
    else:
        simplicity_score = 5  # Many duplicates = lower score
    
    score += simplicity_score
    
    # Clamp to [0, 100]
    return max(0.0, min(100.0, score))


def rank_group(group_files: List[dict]) -> List[dict]:
    """
    Rank files within an overlap group.
    
    Args:
        group_files: List of file records in the same overlap group
        
    Returns:
        List of file records sorted by canonical_score (highest first)
    """
    group_context = {
        'group_size': len(group_files),
        'avg_quality': sum(f.get('py_quality_score', 0) or 0 for f in group_files) / max(1, len(group_files))
    }
    
    # Calculate score for each file
    for file_rec in group_files:
        file_rec['py_canonical_candidate_score'] = calculate_canonical_score(
            file_rec, group_context
        )
    
    # Sort by score (descending)
    return sorted(
        group_files, 
        key=lambda x: (
            x.get('py_canonical_candidate_score', 0),
            x.get('file_id', '')  # Tie-breaker
        ),
        reverse=True
    )


def select_canonical(ranked: List[dict]) -> Optional[str]:
    """
    Select canonical file_id from ranked list.
    
    Args:
        ranked: List of file records sorted by canonical score
        
    Returns:
        file_id of canonical version, or None if empty
    """
    if not ranked:
        return None
    return ranked[0].get('file_id')


def rank_all_groups(
    registry: dict, 
    group_assignments: Dict[str, str]
) -> Dict[str, dict]:
    """
    Rank all overlap groups in the registry.
    
    Args:
        registry: Full registry with files array
        group_assignments: Dict mapping file_id → py_overlap_group_id
        
    Returns:
        Dict mapping file_id → ranking result
    """
    # Group files by overlap_group_id
    groups = defaultdict(list)
    file_map = {f['file_id']: f for f in registry.get('files', []) if 'file_id' in f}
    
    for file_id, group_id in group_assignments.items():
        if file_id in file_map:
            file_record = file_map[file_id].copy()
            file_record['py_overlap_group_id'] = group_id
            groups[group_id].append(file_record)
    
    # Rank each group
    results = {}
    for group_id, group_files in groups.items():
        ranked = rank_group(group_files)
        canonical_id = select_canonical(ranked)
        
        for idx, file_rec in enumerate(ranked):
            file_id = file_rec['file_id']
            results[file_id] = {
                'py_canonical_candidate_score': file_rec['py_canonical_candidate_score'],
                'canonical_file_id': canonical_id,
                'is_canonical': (file_id == canonical_id),
                'rank_in_group': idx + 1,
                'group_size': len(ranked),
                'group_id': group_id
            }
    
    return results


def generate_consolidation_recommendations(
    ranking_results: Dict[str, dict]
) -> List[dict]:
    """
    Generate consolidation recommendations for duplicate clusters.
    
    Args:
        ranking_results: Dict mapping file_id → ranking info
        
    Returns:
        List of recommendations for consolidation
    """
    # Group by cluster
    clusters = defaultdict(list)
    for file_id, info in ranking_results.items():
        if info['group_size'] > 1:  # Only multi-file clusters
            clusters[info['group_id']].append({
                'file_id': file_id,
                'score': info['py_canonical_candidate_score'],
                'is_canonical': info['is_canonical'],
                'rank': info['rank_in_group']
            })
    
    recommendations = []
    for group_id, files in clusters.items():
        canonical = next((f for f in files if f['is_canonical']), None)
        if not canonical:
            continue
        
        non_canonical = [f for f in files if not f['is_canonical']]
        
        recommendations.append({
            'group_id': group_id,
            'action': 'CONSOLIDATE',
            'keep': canonical['file_id'],
            'archive': [f['file_id'] for f in non_canonical],
            'duplicate_count': len(files) - 1,
            'canonical_score': canonical['score'],
            'justification': f"Canonical version has score {canonical['score']:.1f}/100"
        })
    
    return sorted(recommendations, key=lambda x: x['duplicate_count'], reverse=True)


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Rank files within overlap groups and select canonical versions'
    )
    parser.add_argument('--registry-json', required=True, 
                       help='Registry file with py_quality_score and other metrics')
    parser.add_argument('--clusters-json', required=True, 
                       help='Cluster assignments (file_id → group_id)')
    parser.add_argument('--output', required=True, 
                       help='Output JSON (file_id → ranking result)')
    parser.add_argument('--recommendations', 
                       help='Optional consolidation recommendations file')
    
    args = parser.parse_args()
    
    # Load registry
    try:
        with open(args.registry_json, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        print(f"Error loading registry: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Load cluster assignments
    try:
        with open(args.clusters_json, 'r', encoding='utf-8') as f:
            clusters = json.load(f)
    except Exception as e:
        print(f"Error loading clusters: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(clusters)} cluster assignments...", file=sys.stderr)
    
    # Rank all groups
    results = rank_all_groups(registry, clusters)
    
    # Write ranking results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, sort_keys=True)
    
    # Statistics
    canonical_files = set(r['canonical_file_id'] for r in results.values())
    multi_file_groups = sum(1 for r in results.values() if r['group_size'] > 1)
    
    print(f"\n✓ Ranking complete:", file=sys.stderr)
    print(f"  Ranked files: {len(results)}", file=sys.stderr)
    print(f"  Canonical versions: {len(canonical_files)}", file=sys.stderr)
    print(f"  Multi-file clusters: {multi_file_groups}", file=sys.stderr)
    
    # Generate recommendations
    if args.recommendations:
        recs = generate_consolidation_recommendations(results)
        with open(args.recommendations, 'w', encoding='utf-8') as f:
            json.dump(recs, f, indent=2, sort_keys=True)
        
        print(f"  Consolidation recommendations: {len(recs)}", file=sys.stderr)
        print(f"  → {args.recommendations}", file=sys.stderr)
    
    sys.exit(0)
