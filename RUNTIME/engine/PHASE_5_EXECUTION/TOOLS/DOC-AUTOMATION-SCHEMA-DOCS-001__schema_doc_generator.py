#!/usr/bin/env python3
"""
DOC-AUTOMATION-SCHEMA-DOCS-001: Schema Documentation Generator
Phase: PH-ENH-008
Purpose: Automatically generate comprehensive schema documentation
"""

import json
from pathlib import Path
from typing import Dict, List

class SchemaDocGenerator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.schema_dir = repo_root / "GOVERNANCE" / "ssot" / "SSOT_System" / "SSOT_SYS_schemas"
        
    def generate_schema_doc(self, schema_path: Path) -> str:
        """Generate markdown documentation for a schema"""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        doc = []
        doc.append(f"# {schema.get('title', 'Untitled Schema')}\n")
        doc.append(f"**Schema ID**: `{schema.get('$id', 'N/A')}`  ")
        doc.append(f"**Version**: {schema.get('schema_version', 'N/A')}  ")
        doc.append(f"**File**: `{schema_path.name}`\n")
        
        if 'description' in schema:
            doc.append(f"## Description\n\n{schema['description']}\n")
        
        doc.append("## Schema Structure\n")
        doc.append("```json")
        doc.append(json.dumps(schema, indent=2))
        doc.append("```\n")
        
        if 'properties' in schema:
            doc.append("## Properties\n")
            for prop_name, prop_spec in schema['properties'].items():
                doc.append(f"### `{prop_name}`\n")
                doc.append(f"- **Type**: `{prop_spec.get('type', 'any')}`")
                if 'description' in prop_spec:
                    doc.append(f"- **Description**: {prop_spec['description']}")
                if 'pattern' in prop_spec:
                    doc.append(f"- **Pattern**: `{prop_spec['pattern']}`")
                if 'enum' in prop_spec:
                    doc.append(f"- **Allowed Values**: {', '.join(f'`{v}`' for v in prop_spec['enum'])}")
                doc.append("")
        
        if 'required' in schema:
            doc.append("## Required Properties\n")
            for req in schema['required']:
                doc.append(f"- `{req}`")
            doc.append("")
        
        return '\n'.join(doc)
    
    def generate_index(self, schemas: List[Dict]) -> str:
        """Generate index of all schemas"""
        doc = ["# Schema Index\n"]
        doc.append("Complete index of all schemas in the repository.\n")
        
        by_category = {}
        for schema in schemas:
            category = schema.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(schema)
        
        for category in sorted(by_category.keys()):
            doc.append(f"## {category.capitalize()} Schemas\n")
            for schema in sorted(by_category[category], key=lambda s: s.get('schema_id', '')):
                doc.append(f"- [{schema.get('title', schema.get('schema_id'))}]({schema.get('path')})")
            doc.append("")
        
        return '\n'.join(doc)
    
    def generate_all_docs(self):
        """Generate documentation for all schemas"""
        output_dir = self.repo_root / "docs" / "schemas"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        schemas = []
        for schema_path in self.schema_dir.glob("DOC-SCHEMA-*.schema.json"):
            doc_content = self.generate_schema_doc(schema_path)
            doc_path = output_dir / f"{schema_path.stem}.md"
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            schemas.append({
                'schema_id': schema_path.stem,
                'title': schema_path.stem,
                'path': f"schemas/{doc_path.name}",
                'category': 'canonical'
            })
        
        # Generate index
        index_content = self.generate_index(schemas)
        index_path = output_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"\n✅ PH-ENH-008 Schema Documentation Generated")
        print(f"📚 Documentation: {output_dir}")
        print(f"📑 Index: {index_path}")
        print(f"📄 Total Schemas Documented: {len(schemas)}")


def main():
    repo_root = Path(r"C:\Users\richg\ALL_AI")
    generator = SchemaDocGenerator(repo_root)
    generator.generate_all_docs()


if __name__ == "__main__":
    main()
