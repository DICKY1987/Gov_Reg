#!/usr/bin/env python3
"""
DOC-TOOL-SCHEMA-AUDIT-001: Schema Foundation Audit Tool
Phase: PH-ENH-001
Purpose: Audit all schemas, identify gaps, catalog dependencies
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import hashlib

class SchemaAuditor:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.schemas: Dict[str, Dict] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.gaps: List[Dict] = []
        self.stats = {
            "total_schemas": 0,
            "canonical_schemas": 0,
            "pattern_schemas": 0,
            "orphaned_schemas": 0,
            "missing_doc_ids": 0,
            "missing_titles": 0,
            "missing_descriptions": 0
        }

    def scan_schemas(self):
        """Scan repository for all .schema.json files"""
        print(f"Scanning {self.repo_root} for schemas...")
        schema_files = list(self.repo_root.rglob("*.schema.json"))
        self.stats["total_schemas"] = len(schema_files)
        
        for schema_path in schema_files:
            self._process_schema(schema_path)
        
        print(f"Found {self.stats['total_schemas']} schemas")

    def _process_schema(self, schema_path: Path):
        """Process individual schema file"""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            rel_path = schema_path.relative_to(self.repo_root)
            schema_id = self._extract_schema_id(schema_path, schema_data)
            
            # Categorize schema
            category = self._categorize_schema(rel_path)
            if category == "canonical":
                self.stats["canonical_schemas"] += 1
            elif category == "pattern":
                self.stats["pattern_schemas"] += 1
            
            # Extract metadata
            schema_info = {
                "schema_id": schema_id,
                "path": str(rel_path),
                "category": category,
                "title": schema_data.get("title", ""),
                "description": schema_data.get("description", ""),
                "schema_version": schema_data.get("$schema", ""),
                "properties": list(schema_data.get("properties", {}).keys()) if "properties" in schema_data else [],
                "required": schema_data.get("required", []),
                "has_doc_id": "doc_id" in schema_data.get("properties", {}),
                "file_size": schema_path.stat().st_size,
                "checksum": self._compute_checksum(schema_path)
            }
            
            # Check for gaps
            self._check_gaps(schema_info)
            
            # Extract dependencies
            self._extract_dependencies(schema_id, schema_data)
            
            self.schemas[schema_id] = schema_info
            
        except Exception as e:
            print(f"Error processing {schema_path}: {e}")
            self.gaps.append({
                "gap_type": "parse_error",
                "schema_path": str(schema_path.relative_to(self.repo_root)),
                "error": str(e)
            })

    def _extract_schema_id(self, schema_path: Path, schema_data: Dict) -> str:
        """Extract or generate schema ID"""
        # Try to extract from doc_id in filename
        if "__" in schema_path.stem:
            parts = schema_path.stem.split("__")
            if parts[0].startswith("DOC-"):
                return parts[0]
        
        # Try from schema data
        if "$id" in schema_data:
            return schema_data["$id"]
        
        # Generate from path
        return f"SCHEMA-{schema_path.stem}"

    def _categorize_schema(self, rel_path: Path) -> str:
        """Categorize schema by location"""
        path_str = str(rel_path).replace("\\", "/")
        
        if "SSOT_System/SSOT_SYS_schemas" in path_str:
            return "canonical"
        elif "patterns" in path_str.lower():
            return "pattern"
        elif "RUNTIME" in path_str:
            return "runtime"
        else:
            return "other"

    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:16]

    def _check_gaps(self, schema_info: Dict):
        """Check for common schema gaps"""
        schema_id = schema_info["schema_id"]
        
        if not schema_info["title"]:
            self.stats["missing_titles"] += 1
            self.gaps.append({
                "gap_type": "missing_title",
                "schema_id": schema_id,
                "path": schema_info["path"]
            })
        
        if not schema_info["description"]:
            self.stats["missing_descriptions"] += 1
            self.gaps.append({
                "gap_type": "missing_description",
                "schema_id": schema_id,
                "path": schema_info["path"]
            })
        
        if not schema_info["has_doc_id"] and schema_info["category"] == "canonical":
            self.stats["missing_doc_ids"] += 1
            self.gaps.append({
                "gap_type": "missing_doc_id_property",
                "schema_id": schema_id,
                "path": schema_info["path"]
            })

    def _extract_dependencies(self, schema_id: str, schema_data: Dict):
        """Extract schema dependencies from $ref references"""
        def find_refs(obj, refs: Set[str]):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    refs.add(obj["$ref"])
                for value in obj.values():
                    find_refs(value, refs)
            elif isinstance(obj, list):
                for item in obj:
                    find_refs(item, refs)
        
        refs = set()
        find_refs(schema_data, refs)
        self.dependencies[schema_id] = refs

    def generate_audit_report(self) -> Dict:
        """Generate comprehensive audit report"""
        return {
            "doc_id": "DOC-REPORT-SCHEMA-AUDIT-001",
            "audit_timestamp": "2026-02-08T02:37:00Z",
            "phase_id": "PH-ENH-001",
            "summary": {
                "total_schemas": self.stats["total_schemas"],
                "canonical_schemas": self.stats["canonical_schemas"],
                "pattern_schemas": self.stats["pattern_schemas"],
                "gaps_found": len(self.gaps),
                "schemas_with_dependencies": len([s for s in self.dependencies.values() if s])
            },
            "statistics": self.stats,
            "gaps": self.gaps,
            "recommendations": self._generate_recommendations()
        }

    def generate_schema_inventory(self) -> Dict:
        """Generate schema inventory"""
        return {
            "doc_id": "DOC-CONFIG-SCHEMA-INVENTORY-001",
            "inventory_timestamp": "2026-02-08T02:37:00Z",
            "phase_id": "PH-ENH-001",
            "schemas": self.schemas,
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "categories": {
                "canonical": [sid for sid, info in self.schemas.items() if info["category"] == "canonical"],
                "pattern": [sid for sid, info in self.schemas.items() if info["category"] == "pattern"],
                "runtime": [sid for sid, info in self.schemas.items() if info["category"] == "runtime"],
                "other": [sid for sid, info in self.schemas.items() if info["category"] == "other"]
            }
        }

    def _generate_recommendations(self) -> List[Dict]:
        """Generate recommendations based on audit findings"""
        recommendations = []
        
        if self.stats["missing_titles"] > 0:
            recommendations.append({
                "priority": "high",
                "category": "metadata",
                "recommendation": f"Add titles to {self.stats['missing_titles']} schemas",
                "rationale": "Schema titles improve discoverability and documentation"
            })
        
        if self.stats["missing_descriptions"] > 0:
            recommendations.append({
                "priority": "high",
                "category": "metadata",
                "recommendation": f"Add descriptions to {self.stats['missing_descriptions']} schemas",
                "rationale": "Descriptions help developers understand schema purpose"
            })
        
        if self.stats["missing_doc_ids"] > 0:
            recommendations.append({
                "priority": "critical",
                "category": "governance",
                "recommendation": f"Add doc_id property to {self.stats['missing_doc_ids']} canonical schemas",
                "rationale": "doc_id is required for governance and tracking"
            })
        
        return recommendations


def main():
    repo_root = Path(r"C:\Users\richg\ALL_AI")
    output_dir = repo_root / "data" / "schema_audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    auditor = SchemaAuditor(repo_root)
    auditor.scan_schemas()
    
    # Generate reports
    audit_report = auditor.generate_audit_report()
    schema_inventory = auditor.generate_schema_inventory()
    
    # Save reports
    audit_path = output_dir / "DOC-REPORT-SCHEMA-AUDIT-001__schema_audit_report.json"
    inventory_path = output_dir / "DOC-CONFIG-SCHEMA-INVENTORY-001__schema_inventory.json"
    
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2)
    
    with open(inventory_path, 'w', encoding='utf-8') as f:
        json.dump(schema_inventory, f, indent=2)
    
    print(f"\n✅ PH-ENH-001 Complete")
    print(f"📊 Audit Report: {audit_path}")
    print(f"📋 Schema Inventory: {inventory_path}")
    print(f"\nSummary:")
    print(f"  Total Schemas: {audit_report['summary']['total_schemas']}")
    print(f"  Canonical: {audit_report['summary']['canonical_schemas']}")
    print(f"  Pattern: {audit_report['summary']['pattern_schemas']}")
    print(f"  Gaps Found: {audit_report['summary']['gaps_found']}")


if __name__ == "__main__":
    main()
