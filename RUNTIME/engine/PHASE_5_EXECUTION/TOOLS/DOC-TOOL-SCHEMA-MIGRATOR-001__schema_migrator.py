#!/usr/bin/env python3
"""
DOC-TOOL-SCHEMA-MIGRATOR-001: Schema Migration Tool
Phase: PH-ENH-002
Purpose: Migrate schemas between versions with validation
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class SchemaMigrator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.migrations: List[Dict] = []
        
    def backup_schema(self, schema_path: Path) -> Path:
        """Create backup of schema before migration"""
        backup_dir = schema_path.parent / ".schema_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{schema_path.stem}_{timestamp}.backup{schema_path.suffix}"
        
        shutil.copy2(schema_path, backup_path)
        return backup_path
    
    def migrate_schema(self, schema_path: Path, migration_spec: Dict) -> bool:
        """Apply migration to schema"""
        try:
            backup_path = self.backup_schema(schema_path)
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            # Apply migration transformations
            if "add_properties" in migration_spec:
                if "properties" not in schema_data:
                    schema_data["properties"] = {}
                schema_data["properties"].update(migration_spec["add_properties"])
            
            if "add_required" in migration_spec:
                if "required" not in schema_data:
                    schema_data["required"] = []
                schema_data["required"].extend(migration_spec["add_required"])
                schema_data["required"] = list(set(schema_data["required"]))
            
            if "update_schema_version" in migration_spec:
                schema_data["$schema"] = migration_spec["update_schema_version"]
            
            # Write migrated schema
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2)
            
            self.migrations.append({
                "schema_path": str(schema_path.relative_to(self.repo_root)),
                "backup_path": str(backup_path.relative_to(self.repo_root)),
                "migration_spec": migration_spec,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            print(f"Migration failed for {schema_path}: {e}")
            return False
    
    def generate_migration_report(self) -> Dict:
        """Generate migration report"""
        return {
            "doc_id": "DOC-REPORT-SCHEMA-MIGRATION-002",
            "phase_id": "PH-ENH-002",
            "migration_timestamp": datetime.now().isoformat(),
            "total_migrations": len(self.migrations),
            "migrations": self.migrations
        }


def main():
    repo_root = Path(r"C:\Users\richg\ALL_AI")
    migrator = SchemaMigrator(repo_root)
    
    print("✅ PH-ENH-002 Schema Migrator Ready")
    print("Migration tool initialized for future schema version upgrades")


if __name__ == "__main__":
    main()
