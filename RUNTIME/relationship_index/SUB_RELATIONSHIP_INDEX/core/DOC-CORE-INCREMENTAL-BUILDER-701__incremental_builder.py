# DOC_LINK: DOC-CORE-INCREMENTAL-BUILDER-701
"""
Incremental Relationship Index Builder

Extends the base builder with caching and change detection for fast incremental builds.

Performance targets:
- No changes: <2s (100% cache hit)
- 1 file changed: <5s
- 10 files changed: <10s
- 100+ files: Fall back to full rebuild
"""
# DOC_ID: DOC-CORE-INCREMENTAL-BUILDER-701

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import hashlib

from core.index_builder import RelationshipIndexBuilder
from core.change_detector import ChangeDetector, ChangeManifest
from core.file_manifest import FileManifest


class IncrementalRelationshipIndexBuilder(RelationshipIndexBuilder):
    """
    Incremental index builder with edge caching.

    Extends base RelationshipIndexBuilder with:
    - Edge cache management
    - Change detection
    - Selective re-analysis
    - Automatic fallback to full rebuild
    """

    def __init__(
        self,
        run_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        registry_path: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        force_full: bool = False
    ):
        """
        Initialize incremental builder.

        Args:
            run_id: Optional run ID
            trace_id: Optional trace ID
            registry_path: Path to doc_id inventory
            cache_dir: Directory for cache files (default: ./cache)
            force_full: Force full rebuild even if cache exists
        """
        super().__init__(run_id, trace_id, registry_path)

        # Cache setup
        if cache_dir is None:
            cache_dir = Path(__file__).resolve().parent.parent / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_path = self.cache_dir / "edge_cache.json"
        self.force_full = force_full

        # Change detector (uses file manifest now)
        self.change_detector = ChangeDetector(self.registry, self.cache_dir)

    def build(self) -> Dict[str, Any]:
        """
        Build index incrementally if possible, otherwise full rebuild.

        Returns:
            Index dictionary with meta, nodes, edges, statistics
        """
        print(f"\n=== Building Relationship Index (Incremental Mode) ===")
        print(f"Run ID: {self.run_id}")
        print(f"Trace ID: {self.trace_id}")
        print(f"Cache: {self.cache_path}")
        print()

        # Step 1: Detect changes
        print("[1/6] Detecting changes...")
        changes = self.change_detector.detect_changes()

        total_changes = changes.total_changes()
        print(f"      Added: {len(changes.added)}, Modified: {len(changes.modified)}, Deleted: {len(changes.deleted)}")

        # Decide: incremental or full?
        cache_exists = self.cache_path.exists()
        change_threshold = 100  # Fall back to full if >100 changes

        use_incremental = (
            cache_exists and
            not self.force_full and
            total_changes < change_threshold
        )

        if use_incremental:
            print(f"      ✓ Using incremental build ({total_changes} changes < {change_threshold} threshold)")
            return self._build_incremental(changes)
        else:
            reason = (
                "no cache" if not cache_exists
                else "forced" if self.force_full
                else f"too many changes ({total_changes} >= {change_threshold})"
            )
            print(f"      ✓ Using full build (reason: {reason})")
            return self._build_full_and_cache()

    def _build_incremental(self, changes: ChangeManifest) -> Dict[str, Any]:
        """
        Build incrementally using cached edges.

        Args:
            changes: ChangeManifest with added/modified/deleted files

        Returns:
            Index dictionary
        """
        # Step 2: Load cache
        print("[2/6] Loading edge cache...")
        cache = self._load_cache()
        edges_before = sum(len(edges) for edges in cache["edges_by_source"].values())
        print(f"      Loaded {len(cache['edges_by_source'])} sources, {edges_before} edges")

        # Step 3: Invalidate changed files
        print("[3/6] Invalidating changed files...")
        invalidated_count = 0
        for doc_id in changes.modified + changes.deleted:
            if doc_id in cache["edges_by_source"]:
                del cache["edges_by_source"][doc_id]
                invalidated_count += 1
        print(f"      Invalidated {invalidated_count} sources")

        # Step 4: Re-analyze changed files
        print("[4/6] Re-analyzing changed files...")
        nodes = self._build_nodes()
        changed_nodes = [n for n in nodes if n["doc_id"] in (changes.added + changes.modified)]

        new_edges = self._extract_edges_for_nodes(changed_nodes)
        print(f"      Found {len(new_edges)} new edges")

        # Step 5: Merge into cache
        print("[5/6] Merging into cache...")
        for edge in new_edges:
            source = edge["source"]
            if source not in cache["edges_by_source"]:
                cache["edges_by_source"][source] = []
            cache["edges_by_source"][source].append(edge)

        # Step 6: Build final index
        print("[6/6] Building final index...")
        all_edges = []
        for edges_list in cache["edges_by_source"].values():
            all_edges.extend(edges_list)

        edges_after = len(all_edges)
        cache_hits = edges_after - len(new_edges)

        # Update cache metadata
        cache["stats"] = {
            "total_edges": edges_after,
            "cache_hits": cache_hits,
            "cache_misses": len(new_edges),
            "last_incremental_build": datetime.now(timezone.utc).isoformat()
        }

        print(f"      Cache hits: {cache_hits}, Cache misses: {len(new_edges)}")

        # Save updated cache
        self._save_cache(cache)

        # Update file manifest with changed files
        print("[6/6] Updating file manifest...")
        file_manifest = FileManifest(self.cache_dir / "file_manifest.json")
        full_manifest = file_manifest.load_manifest()

        # Update hashes for changed files
        for node in changed_nodes:
            doc_id = node["doc_id"]
            file_hash = self._compute_file_hash(node["path"])
            full_manifest[doc_id] = file_hash

        file_manifest.save_manifest(full_manifest)
        print(f"      Updated {len(changed_nodes)} file hashes")

        # Build final index structure (reuse edges that already have rel_ids)
        return self._finalize_index(nodes, all_edges)

    def _build_full_and_cache(self) -> Dict[str, Any]:
        """
        Perform full build and create/update cache.

        Returns:
            Index dictionary
        """
        # Do full build using parent class
        index = super().build()

        # Create cache from full build
        print("\n[Cache] Building cache from full index...")
        cache = {
            "version": "2.0.0",
            "last_full_build": datetime.now(timezone.utc).isoformat(),
            "doc_id_checksum": self._compute_inventory_checksum(),
            "edges_by_source": {},
            "stats": {
                "total_edges": len(index["edges"]),
                "cache_hits": 0,
                "cache_misses": len(index["edges"]),
                "last_full_build": datetime.now(timezone.utc).isoformat()
            }
        }

        # Index edges by source and add file hashes
        for edge in index["edges"]:
            source = edge["source"]

            # Add file hash if not present
            if "source_file_hash" not in edge:
                # Find source node to get path
                source_node = next((n for n in index["nodes"] if n["doc_id"] == source), None)
                if source_node:
                    edge["source_file_hash"] = self._compute_file_hash(source_node["path"])

            if source not in cache["edges_by_source"]:
                cache["edges_by_source"][source] = []
            cache["edges_by_source"][source].append(edge)

        # Save cache
        self._save_cache(cache)
        print(f"[Cache] Saved {len(cache['edges_by_source'])} sources to edge cache")

        # Build and save file manifest for ALL files
        print("[Cache] Building file manifest for all files...")
        file_manifest = FileManifest(self.cache_dir / "file_manifest.json")
        manifest = file_manifest.build_manifest(self.registry)
        file_manifest.save_manifest(manifest)
        print(f"[Cache] Saved manifest for {len(manifest)} files")

        return index

    def _extract_edges_for_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract edges for specific nodes only.

        Args:
            nodes: List of node dictionaries

        Returns:
            List of edge dictionaries (with rel_id and file_hash)
        """
        all_edges = []
        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/

        for i, node in enumerate(nodes):
            if (i + 1) % 10 == 0 and len(nodes) > 10:
                print(f"      Processing {i + 1}/{len(nodes)}...")

            doc_id = node["doc_id"]
            path = node["path"]
            file_type = node["file_type"]
            file_path = repo_root / path

            if not file_path.exists():
                continue

            # Compute file hash
            file_hash = self._compute_file_hash(path)

            # Run analyzers
            for analyzer in self.analyzers:
                if analyzer.can_analyze(file_path, file_type):
                    try:
                        edges = analyzer.analyze(file_path, doc_id)
                        for e in edges:
                            edge_dict = e.to_dict()
                            edge_dict["source_file_hash"] = file_hash
                            all_edges.append(edge_dict)
                    except Exception as e:
                        print(f"      Warning: {analyzer.analyzer_id} failed on {path}: {e}")

        # Add rel_ids to new edges
        all_edges = self._add_edge_ids(all_edges)

        return all_edges

    def _finalize_index(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """
        Build final index structure from nodes and edges.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries (already have rel_ids)

        Returns:
            Complete index dictionary
        """
        # Compute statistics
        stats = self._compute_statistics(edges)

        # Sort everything deterministically
        nodes = self._sort_nodes(nodes)
        edges = self._sort_edges(edges)

        # Build index
        return {
            "meta": {
                "version": "1.0.0",
                "doc_id": f"DOC-INDEX-RELGRAPH-{self.run_id[:6].upper()}",
                "source_registry": str(self.registry.inventory_path),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generator": "incremental_relationship_index_builder",
                "generator_version": "2.0.0",
                "run_id": self.run_id,
                "trace_id": self.trace_id,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            },
            "nodes": nodes,
            "edges": edges,
            "statistics": stats
        }

    def _load_cache(self) -> Dict[str, Any]:
        """Load edge cache from file."""
        if not self.cache_path.exists():
            return {
                "version": "2.0.0",
                "edges_by_source": {},
                "stats": {"total_edges": 0}
            }

        with open(self.cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_cache(self, cache: Dict[str, Any]):
        """Save edge cache to file."""
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

    def _compute_file_hash(self, rel_path: str) -> str:
        """Compute SHA-256 hash of file content."""
        file_path = Path(__file__).resolve().parent.parent.parent.parent.parent / rel_path  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/

        if not file_path.exists():
            return ""

        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except (IOError, OSError):
            return ""

    def _compute_inventory_checksum(self) -> str:
        """Compute checksum of entire inventory for cache validation."""
        docs = self.registry.get_all_docs()
        doc_ids = sorted(d["doc_id"] for d in docs)
        data = "".join(doc_ids).encode('utf-8')
        return hashlib.sha256(data).hexdigest()
