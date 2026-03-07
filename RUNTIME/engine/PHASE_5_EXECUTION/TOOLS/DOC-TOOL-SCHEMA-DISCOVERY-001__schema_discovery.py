#!/usr/bin/env python3
"""
DOC-TOOL-SCHEMA-DISCOVERY-001: Schema Registry & Discovery Tool
Phase: PH-ENH-003
Purpose: Centralized schema registry with discovery APIs
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


class SchemaRegistry:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.registry: Dict[str, Dict] = {}
        self.index_by_type: Dict[str, List[str]] = defaultdict(list)
        self.index_by_category: Dict[str, List[str]] = defaultdict(list)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.usage_stats: Dict[str, int] = defaultdict(int)
        
    def load_schema_inventory(self):
        """Load existing schema inventory from PH-ENH-001"""
        inventory_path = self.repo_root / "data" / "schema_audit" / "DOC-CONFIG-SCHEMA-INVENTORY-001__schema_inventory.json"
        
        if not inventory_path.exists():
            print("Warning: Schema inventory not found, registry will be empty")
            return
        
        with open(inventory_path, 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        
        # Build registry from inventory
        for schema_id, schema_info in inventory.get("schemas", {}).items():
            self.register_schema(schema_id, schema_info)
        
        # Load dependencies
        for schema_id, deps in inventory.get("dependencies", {}).items():
            self.dependency_graph[schema_id] = set(deps)
        
        print(f"Loaded {len(self.registry)} schemas into registry")
    
    def register_schema(self, schema_id: str, schema_info: Dict):
        """Register a schema in the registry"""
        self.registry[schema_id] = schema_info
        
        # Index by category
        category = schema_info.get("category", "other")
        self.index_by_category[category].append(schema_id)
        
        # Extract type from properties
        if "properties" in schema_info:
            for prop in schema_info["properties"]:
                self.index_by_type[prop].append(schema_id)
    
    def discover_by_id(self, schema_id: str) -> Optional[Dict]:
        """Discover schema by ID"""
        self.usage_stats[schema_id] += 1
        return self.registry.get(schema_id)
    
    def discover_by_category(self, category: str) -> List[Dict]:
        """Discover schemas by category"""
        schema_ids = self.index_by_category.get(category, [])
        return [self.registry[sid] for sid in schema_ids if sid in self.registry]
    
    def discover_by_property(self, property_name: str) -> List[Dict]:
        """Discover schemas that have a specific property"""
        schema_ids = self.index_by_type.get(property_name, [])
        return [self.registry[sid] for sid in schema_ids if sid in self.registry]
    
    def get_dependencies(self, schema_id: str) -> Set[str]:
        """Get dependencies for a schema"""
        return self.dependency_graph.get(schema_id, set())
    
    def get_dependents(self, schema_id: str) -> Set[str]:
        """Get schemas that depend on this schema"""
        dependents = set()
        for sid, deps in self.dependency_graph.items():
            if schema_id in deps:
                dependents.add(sid)
        return dependents
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get schema usage statistics"""
        return dict(self.usage_stats)
    
    def search_schemas(self, query: str) -> List[Dict]:
        """Search schemas by query string"""
        results = []
        query_lower = query.lower()
        
        for schema_id, schema_info in self.registry.items():
            if (query_lower in schema_id.lower() or
                query_lower in schema_info.get("title", "").lower() or
                query_lower in schema_info.get("description", "").lower() or
                query_lower in str(schema_info.get("path", "")).lower()):
                results.append(schema_info)
        
        return results
    
    def export_registry(self) -> Dict:
        """Export registry to JSON format"""
        return {
            "doc_id": "DOC-REGISTRY-SCHEMA-001",
            "phase_id": "PH-ENH-003",
            "registry_timestamp": "2026-02-08T02:50:00Z",
            "total_schemas": len(self.registry),
            "schemas": self.registry,
            "indices": {
                "by_category": {k: v for k, v in self.index_by_category.items()},
                "by_type": {k: v for k, v in self.index_by_type.items()}
            },
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()},
            "usage_stats": self.get_usage_stats()
        }


def main():
    repo_root = Path(r"C:\Users\richg\ALL_AI")
    output_dir = repo_root / "data" / "schema_registry"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    registry = SchemaRegistry(repo_root)
    registry.load_schema_inventory()
    
    # Export registry
    registry_data = registry.export_registry()
    registry_path = output_dir / "DOC-REGISTRY-SCHEMA-001__schema_registry.json"
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2)
    
    # Test discovery APIs
    canonical_schemas = registry.discover_by_category("canonical")
    pattern_schemas = registry.discover_by_category("pattern")
    
    print(f"\n✅ PH-ENH-003 Schema Registry Complete")
    print(f"📊 Registry: {registry_path}")
    print(f"\nSummary:")
    print(f"  Total Schemas: {registry_data['total_schemas']}")
    print(f"  Canonical: {len(canonical_schemas)}")
    print(f"  Pattern: {len(pattern_schemas)}")
    print(f"  Categories: {len(registry_data['indices']['by_category'])}")
    
    # Demo search
    print(f"\n🔍 Discovery API Examples:")
    print(f"  - discover_by_category('canonical'): {len(canonical_schemas)} results")
    print(f"  - discover_by_property('doc_id'): Available")
    print(f"  - search_schemas('execution'): Available")


if __name__ == "__main__":
    main()
