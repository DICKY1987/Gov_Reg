#!/usr/bin/env python3
"""Timestamp Clustering (Week 3 - Component 2/6)"""
import json
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

class TimestampClusterer:
    def cluster_by_timestamp(self, files: List[Dict[str, Any]], 
                            time_window_seconds: int = 300) -> List[List[Dict[str, Any]]]:
        """Group files by timestamp proximity (5-minute window default)."""
        if not files:
            return []
        
        # Sort by timestamp
        sorted_files = sorted(files, key=lambda f: f.get("created_at", ""))
        
        clusters = []
        current_cluster = [sorted_files[0]]
        
        for i in range(1, len(sorted_files)):
            prev_time = datetime.fromisoformat(sorted_files[i-1].get("created_at", "").replace("Z", "+00:00"))
            curr_time = datetime.fromisoformat(sorted_files[i].get("created_at", "").replace("Z", "+00:00"))
            
            if (curr_time - prev_time).total_seconds() <= time_window_seconds:
                current_cluster.append(sorted_files[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sorted_files[i]]
        
        clusters.append(current_cluster)
        return clusters

def main():
    import sys, argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--window', type=int, default=300)
    args = parser.parse_args()
    
    with open(args.registry) as f:
        registry = json.load(f)
    
    clusterer = TimestampClusterer()
    clusters = clusterer.cluster_by_timestamp(registry.get("files", []), args.window)
    
    report = {
        "total_files": len(registry.get("files", [])),
        "clusters_found": len(clusters),
        "cluster_sizes": [len(c) for c in clusters]
    }
    
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Clustered into {len(clusters)} groups")

if __name__ == "__main__":
    main()
