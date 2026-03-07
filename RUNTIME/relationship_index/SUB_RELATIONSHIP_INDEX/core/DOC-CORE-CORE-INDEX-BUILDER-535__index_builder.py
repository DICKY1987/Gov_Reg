# DOC_LINK: DOC-CORE-CORE-INDEX-BUILDER-535
"""
Relationship Index Builder

Main orchestrator for building the autonomous relationship index.

Process:
1. Load doc_id registry from SUB_DOC_ID
2. Build nodes from registry entries
3. Run analyzers to extract edges
4. Flag broken edges (target_missing)
5. Compute statistics
6. Sort deterministically
7. Generate index JSON
"""
# DOC_ID: DOC-CORE-CORE-INDEX-BUILDER-535

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzers import (
    PythonImportAnalyzer,
    SchemaReferenceAnalyzer,
    PowerShellImportAnalyzer,
    MarkdownLinkAnalyzer,
    YAMLReferenceAnalyzer,
    TestLinkAnalyzer,
    ArtifactBundleAnalyzer,
    RelationshipEdge
)
from core.confidence_engine import ConfidenceEngine
from core.edge_id_generator import generate_edge_id


class SimpleDocIDRegistry:
    """
    Simplified doc_id registry for path lookups.

    Reads from docs_inventory.jsonl and provides path->doc_id mapping.
    """

    def __init__(self, inventory_path: Optional[Path] = None):
        """
        Initialize registry.

        Args:
            inventory_path: Path to docs_inventory.jsonl.
                          If None, uses default location in SUB_DOC_ID/
        """
        if inventory_path is None:
            # Default: SUB_DOC_ID/5_REGISTRY_DATA/docs_inventory.jsonl
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/
            inventory_path = repo_root / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "5_REGISTRY_DATA" / "docs_inventory.jsonl"

        self.inventory_path = inventory_path
        self.data = self._load_inventory()
        self._build_lookup_index()

    def _load_inventory(self) -> List[Dict[str, Any]]:
        """Load inventory from JSONL file."""
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Inventory not found: {self.inventory_path}")

        docs = []
        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    doc = json.loads(line)
                    docs.append(doc)

        return docs

    def _build_lookup_index(self):
        """Build path->doc_id lookup index."""
        self.path_to_doc_id = {}

        for doc in self.data:
            path = doc.get("path", "")
            doc_id = doc.get("doc_id")
            status = doc.get("status")

            # Only index docs with doc_ids and registered status
            if doc_id and status == "registered":
                # Normalize path separators
                normalized_path = path.replace("\\", "/")
                self.path_to_doc_id[normalized_path] = doc_id

    def lookup_by_path(self, file_path: str) -> Optional[str]:
        """
        Lookup doc_id by file path.

        Args:
            file_path: Absolute or relative file path

        Returns:
            Doc ID if found, None otherwise
        """
        # Normalize path separators
        normalized = str(file_path).replace("\\", "/")

        # Try direct lookup
        if normalized in self.path_to_doc_id:
            return self.path_to_doc_id[normalized]

        # Try relative to repo root
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/
            path_obj = Path(file_path)

            if path_obj.is_absolute():
                # Convert absolute path to relative
                try:
                    relative = path_obj.relative_to(repo_root)
                    relative_str = str(relative).replace("\\", "/")
                    if relative_str in self.path_to_doc_id:
                        return self.path_to_doc_id[relative_str]
                except ValueError:
                    pass

        except Exception:
            pass

        return None

    def get_all_docs(self) -> List[Dict[str, Any]]:
        """Get all docs with doc_ids."""
        return [d for d in self.data if d.get("status") == "registered"]


class RelationshipIndexBuilder:
    """
    Main orchestrator for building the relationship index.

    Coordinates analyzers, collects edges, and generates the final index.
    """

    def __init__(
        self,
        run_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        registry_path: Optional[Path] = None
    ):
        """
        Initialize the index builder.

        Args:
            run_id: Optional run ID for observability
            trace_id: Optional trace ID for observability
            registry_path: Path to doc_id inventory (uses default if None)
        """
        # Generate run_id if not provided
        if run_id is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            run_id = f"run_{timestamp}"

        if trace_id is None:
            trace_id = f"trace-{run_id}"

        self.run_id = run_id
        self.trace_id = trace_id

        # Load registry
        self.registry = SimpleDocIDRegistry(registry_path)

        # Initialize confidence engine
        self.confidence_engine = ConfidenceEngine()

        # Initialize analyzers (Phase 2: 7 analyzers - added ArtifactBundleAnalyzer)
        self.analyzers = [
            PythonImportAnalyzer(self.registry, self.confidence_engine),
            SchemaReferenceAnalyzer(self.registry, self.confidence_engine),
            PowerShellImportAnalyzer(self.registry, self.confidence_engine),
            MarkdownLinkAnalyzer(self.registry, self.confidence_engine),
            YAMLReferenceAnalyzer(self.registry, self.confidence_engine),
            TestLinkAnalyzer(self.registry, self.confidence_engine),
            ArtifactBundleAnalyzer(self.registry, self.confidence_engine)
        ]

    def build(self) -> Dict[str, Any]:
        """
        Build the complete relationship index.

        Returns:
            Dictionary containing meta, nodes, edges, and statistics

        Process:
            1. Build nodes from registry
            2. Run analyzers to extract edges
            3. Add rel_id to each edge
            4. Compute statistics
            5. Sort deterministically
            6. Return index dict
        """
        print(f"\n=== Building Relationship Index ===")
        print(f"Run ID: {self.run_id}")
        print(f"Trace ID: {self.trace_id}\n")

        # Step 1: Build nodes
        print("[1/5] Building nodes from doc_id registry...")
        nodes = self._build_nodes()
        print(f"      Found {len(nodes)} nodes")

        # Step 2: Extract edges
        print("[2/5] Extracting edges with analyzers...")
        edges = self._extract_edges(nodes)
        print(f"      Found {len(edges)} edges")

        # Step 3: Add rel_ids
        print("[3/5] Generating stable edge IDs...")
        edges_with_ids = self._add_edge_ids(edges)

        # Step 4: Compute statistics
        print("[4/5] Computing statistics...")
        stats = self._compute_statistics(edges_with_ids)

        # Step 5: Sort deterministically
        print("[5/5] Sorting for deterministic output...")
        sorted_nodes = self._sort_nodes(nodes)
        sorted_edges = self._sort_edges(edges_with_ids)

        # Build final index
        index = {
            "meta": self._build_meta(len(sorted_nodes), len(sorted_edges)),
            "nodes": sorted_nodes,
            "edges": sorted_edges,
            "statistics": stats
        }

        print(f"\n✅ Index built successfully!")
        print(f"   Nodes: {len(sorted_nodes)}")
        print(f"   Edges: {len(sorted_edges)}")
        print(f"   High confidence: {stats['confidence_distribution'].get('high', 0)}")
        print(f"   Broken: {stats['confidence_distribution'].get('broken', 0)}\n")

        return index

    def _build_nodes(self) -> List[Dict[str, Any]]:
        """Build node list from doc_id registry."""
        nodes = []
        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/

        for doc in self.registry.get_all_docs():
            doc_id = doc.get("doc_id")
            path = doc.get("path", "")
            file_type = doc.get("file_type", "unknown")
            last_modified = doc.get("last_modified", "")

            nodes.append({
                "doc_id": doc_id,
                "path": path,
                "file_type": file_type,
                "status": "active",  # All docs in inventory are active
                "last_modified": last_modified
            })

        return nodes

    def _extract_edges(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationship edges using analyzers.

        Args:
            nodes: List of node dicts

        Returns:
            List of edge dicts (without rel_id yet)
        """
        all_edges = []
        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/

        # Track analyzer activity
        analyzer_stats = {a.__class__.__name__: 0 for a in self.analyzers}

        for i, node in enumerate(nodes):
            if (i + 1) % 100 == 0:
                print(f"      Processing node {i + 1}/{len(nodes)}...")

            doc_id = node["doc_id"]
            path = node["path"]
            file_type = node["file_type"]

            # Construct absolute path
            file_path = repo_root / path

            # Check if file exists
            if not file_path.exists():
                continue

            # Find applicable analyzers
            for analyzer in self.analyzers:
                if analyzer.can_analyze(file_path, file_type):
                    # Run analyzer
                    try:
                        edges = analyzer.analyze(file_path, doc_id)
                        if edges:
                            analyzer_stats[analyzer.__class__.__name__] += len(edges)
                        all_edges.extend([e.to_dict() for e in edges])
                    except Exception as e:
                        # Log error but continue
                        print(f"\n      ⚠️  Analyzer {analyzer.analyzer_id} failed on {path}:")
                        print(f"          {type(e).__name__}: {e}")
                        if "MarkdownLink" in analyzer.__class__.__name__:
                            import traceback
                            traceback.print_exc()

        # Print analyzer statistics
        print(f"\n   Edge extraction complete!")
        print(f"   Total edges found: {len(all_edges)}")
        for analyzer_name, count in analyzer_stats.items():
            print(f"     • {analyzer_name}: {count} edges")

        return all_edges

    def _add_edge_ids(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add rel_id to each edge using stable ID generation."""
        edges_with_ids = []

        for edge in edges:
            source = edge["source"]
            target = edge.get("target", "")
            edge_type = edge["type"]

            # Generate rel_id
            # For broken edges (target empty), use special marker
            if not target:
                target_for_id = "<MISSING>"
            else:
                target_for_id = target

            rel_id = generate_edge_id(source, target_for_id, edge_type)

            # Add rel_id to edge
            edge_with_id = {
                "rel_id": rel_id,
                **edge
            }

            edges_with_ids.append(edge_with_id)

        return edges_with_ids

    def _compute_statistics(self, edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute statistics about the relationship index."""
        edge_types = defaultdict(int)
        confidence_dist = defaultdict(int)
        analyzer_coverage = defaultdict(int)

        for edge in edges:
            # Edge types
            edge_type = edge.get("type", "unknown")
            edge_types[edge_type] += 1

            # Confidence distribution
            confidence = edge.get("confidence", 0.0)
            if confidence == 1.0:
                confidence_dist["high"] += 1
            elif confidence == 0.0:
                confidence_dist["broken"] += 1

            # Analyzer coverage
            analyzer_id = edge.get("analyzer_id", "unknown")
            analyzer_coverage[analyzer_id] += 1

        return {
            "edge_types": dict(edge_types),
            "confidence_distribution": dict(confidence_dist),
            "analyzer_coverage": dict(analyzer_coverage)
        }

    def _sort_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort nodes deterministically by doc_id."""
        return sorted(nodes, key=lambda n: n["doc_id"])

    def _sort_edges(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort edges deterministically by rel_id."""
        return sorted(edges, key=lambda e: e["rel_id"])

    def _build_meta(self, total_nodes: int, total_edges: int) -> Dict[str, Any]:
        """Build metadata section."""
        return {
            "doc_id": "DOC-CONFIG-RELATIONSHIP-INDEX-DATA-009",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": "1.0.0",
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "source_registry": str(self.registry.inventory_path),
            "run_id": self.run_id,
            "trace_id": self.trace_id
        }


if __name__ == "__main__":
    # Example usage
    print("\n=== Relationship Index Builder Example ===\n")

    # Build index
    builder = RelationshipIndexBuilder(
        run_id="example_run_001",
        trace_id="trace-example-001"
    )

    try:
        index = builder.build()

        # Print summary
        print("\nIndex Summary:")
        print(f"  Total nodes: {index['meta']['total_nodes']}")
        print(f"  Total edges: {index['meta']['total_edges']}")
        print(f"  Edge types:")
        for edge_type, count in index['statistics']['edge_types'].items():
            print(f"    {edge_type}: {count}")
        print(f"  Confidence distribution:")
        for conf, count in index['statistics']['confidence_distribution'].items():
            print(f"    {conf}: {count}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure SUB_DOC_ID/5_REGISTRY_DATA/docs_inventory.jsonl exists")
