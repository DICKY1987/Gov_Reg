#!/usr/bin/env python3
"""
Schema Update Script
Fixes Issues #5 and #6
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    schema_path = Path("01999000042260124012_governance_registry_schema.v3.json")
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = schema_path.with_suffix(f".json.backup.{timestamp}")
    
    print(f"Creating backup: {backup_path}")
    with open(schema_path) as f:
        schema = json.load(f)
    
    with open(backup_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    # Issue #6: Fix EdgeRecord ID patterns
    edge_record = schema["definitions"]["EdgeRecord"]["properties"]
    edge_record["source_file_id"]["pattern"] = "^[0-9]{20}$"
    edge_record["target_file_id"]["pattern"] = "^[0-9]{20}$"
    
    # Issue #6: Fix generated_by_file_id pattern in FileRecord
    file_record = schema["definitions"]["FileRecord"]["properties"]
    if "generated_by_file_id" in file_record:
        file_record["generated_by_file_id"]["pattern"] = "^[0-9]{20}$"
    
    # Issue #5: Add GEU fields to FileRecord
    file_record["geu_ids"] = {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of Governance Enforcement Unit IDs associated with this file"
    }
    
    file_record["is_shared"] = {
        "type": "boolean",
        "description": "Whether file is shared across multiple GEUs"
    }
    
    file_record["owner_geu_id"] = {
        "type": ["string", "null"],
        "description": "GEU ID of the owner if file is shared, otherwise null"
    }
    
    file_record["primary_geu_id"] = {
        "type": ["string", "null"],
        "description": "Primary GEU ID responsible for this file, or null if not assigned"
    }
    
    # Write updated schema
    print(f"Writing updated schema: {schema_path}")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    print("\n=== SCHEMA UPDATE REPORT ===")
    print("✅ Fixed EdgeRecord ID patterns (16-hex → 20-decimal)")
    print("✅ Fixed generated_by_file_id pattern")
    print("✅ Added GEU fields (geu_ids, is_shared, owner_geu_id, primary_geu_id)")
    print(f"\nBackup saved to: {backup_path}")
    print(f"Schema updated: {schema_path}")

if __name__ == "__main__":
    main()
