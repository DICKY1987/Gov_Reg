#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-1356
"""
Generate comprehensive technical documentation for PROCESS_STEP_LIB
Extracts doc_ids, descriptions, and relationships for all files and folders.
"""

import os
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

class DocumentationBuilder:
    """Builds comprehensive JSON documentation for the entire directory structure"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.doc_id_counter = 1000
        self.doc_id_map = {}

    def extract_doc_id_from_file(self, file_path: Path) -> Optional[str]:
        """Extract doc_id from file frontmatter or content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read first 2000 chars

            # Try YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        if isinstance(frontmatter, dict) and 'doc_id' in frontmatter:
                            return frontmatter['doc_id']
                    except:
                        pass

            # Try inline doc_id
            match = re.search(r'(?:doc_id|DOC_ID|doc-id):\s*([A-Z0-9_-]+)', content, re.IGNORECASE)
            if match:
                return match.group(1)

            # Try comment-style doc_id
            match = re.search(r'#\s*(?:DOC_ID|doc_id):\s*([A-Z0-9_-]+)', content)
            if match:
                return match.group(1)

        except Exception as e:
            pass

        return None

    def generate_doc_id(self, name: str, path: Path) -> str:
        """Generate a unique doc_id if one doesn't exist"""
        # Create a descriptive doc_id based on path
        rel_path = path.relative_to(self.root_path)
        parts = str(rel_path).replace('\\', '/').split('/')

        # Build doc_id from path components
        doc_parts = ['DOC', 'PROCESS_STEP_LIB']
        for part in parts[:-1]:  # Exclude filename
            doc_parts.append(part.upper().replace('.', '_').replace('-', '_'))

        # Add filename
        filename = parts[-1] if parts else name
        filename_clean = filename.replace('.', '_').replace('-', '_').upper()
        doc_parts.append(filename_clean)

        doc_id = '_'.join(doc_parts)

        # Ensure uniqueness
        if doc_id in self.doc_id_map:
            doc_id = f"{doc_id}_{self.doc_id_counter}"
            self.doc_id_counter += 1

        self.doc_id_map[doc_id] = str(path)
        return doc_id

    def get_file_description(self, file_path: Path) -> str:
        """Extract or generate description for a file"""
        descriptions = {
            # Root documentation
            'README.md': 'Main project documentation and entry point. Provides overview of PROCESS_STEP_LIB unified E2E schema system.',
            'CLAUDE.md': 'Comprehensive developer guide for Claude Code. Contains commands, architecture, and development workflow.',
            'AI_NAVIGATION_GUIDE.md': 'Navigation guide specifically designed for AI agents working with this codebase.',
            'DIRECTORY_INDEX.md': 'Complete file listing with purposes and organization structure.',
            'QUICK_REFERENCE.md': 'Quick reference card for common commands and operations.',
            'CHANGELOG.md': 'History of changes and updates to the system.',
            'AUTOMATION_STRATEGY.md': 'Detailed explanation of SSOT architecture and automation approach.',

            # Configuration
            'pipeline_config.yaml': 'Central pipeline configuration. Controls source schemas, outputs, validation, and automation behavior.',
            'phase_mappings.yaml': 'Maps 24 original phase names to 9 universal phases for schema consolidation.',
            'operation_taxonomy.yaml': 'Consolidates 30+ operation types into 15 standardized categories.',

            # Core tools
            'pfa_run_pipeline.py': 'Main pipeline orchestrator. One command rebuilds all 30+ derived artifacts from source schemas.',
            'pfa_merge_schemas.py': 'Merges 5 source schemas into unified schema with conflict resolution.',
            'pfa_build_master_index.py': 'Builds 7-dimensional master index for fast queries across all dimensions.',
            'pfa_validate_e2e_pipeline.py': 'Comprehensive validation suite with 15 tests across 4 layers.',
            'pfa_watch.py': 'Watch mode for development. Auto-rebuilds pipeline when source files change.',
            'pfa_common.py': 'Shared utilities library. Provides consistent file I/O, validation, logging, and path resolution.',
            'generate_explained_steps.py': 'Generates layman-friendly explanations for all 274 process steps.',
            'install_git_hooks.py': 'Installs git hooks for automatic pipeline execution on commit.',

            # Indices
            'master_index.json': '7-dimensional queryable index: by_phase, by_component, by_operation, by_workflow, dependencies, cross_references, step_lookup.',
            'merge_report.json': 'Statistics and conflict resolutions from schema merge process.',
            'validation_report.json': 'Comprehensive validation results with pass/fail status for all tests.',

            # Source schemas
            'PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA.yaml': 'Master orchestration and multi-agent coordination steps.',
            'PFA_PATTERNS_PROCESS_STEPS_SCHEMA.yaml': 'Pattern automation and zero-touch workflow steps.',
            'PFA_GLOSSARY_PROCESS_STEPS_SCHEMA.yaml': 'Terminology management and governance steps.',
            'PFA_SSOT_PROCESS_STEPS_SCHEMA.yaml': 'Single source of truth validation and enforcement steps.',
            'PFA_PROCESS_STEPS_SCHEMA.yaml': 'General process definition steps.',
            'PFA_DIRECTORY_INTEGRATION_PROCESS_STEPS_SCHEMA.yaml': 'Directory integration E2E coverage steps.',

            # Generated schemas
            'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml': 'Main unified schema containing all 274 merged steps from 5 sources.',
            'PFA_E2E_CANONICAL_PROCESS_STEPS_SCHEMA.yaml': 'Canonical format version of unified schema with normalized structure.',

            # Documentation guides
            'ALL_274_STEPS.md': 'Technical listing of all 274 process steps with IDs, phases, and components. Auto-generated.',
            'ALL_274_STEPS_EXPLAINED.md': 'Plain English explanations of all 274 steps for non-technical users. Auto-generated.',
            'QUICKSTART.md': '5-minute getting started guide for new users.',
            'E2E_PROJECT_COMPLETE.md': 'Complete project history, achievements, and validation results.',

            # Test suite
            'run_all_tests.py': 'Test runner. Executes all 43 tests with optional coverage reporting.',
            'test_pipeline_orchestrator.py': 'Tests for pipeline orchestration, validation, and error handling.',
            'test_schema_validation.py': 'Tests for schema integrity, format validation, and consistency.',
            'test_watch_mode.py': 'Tests for watch mode file monitoring and auto-rebuild functionality.',
        }

        filename = file_path.name
        if filename in descriptions:
            return descriptions[filename]

        # Generate description based on file type
        ext = file_path.suffix.lower()
        if ext == '.py':
            return f'Python script: {filename}. Part of automation tooling.'
        elif ext in ['.yaml', '.yml']:
            return f'YAML configuration/schema: {filename}'
        elif ext == '.json':
            return f'JSON data file: {filename}'
        elif ext == '.md':
            return f'Markdown documentation: {filename}'
        else:
            return f'File: {filename}'

    def get_folder_description(self, folder_path: Path) -> str:
        """Get description for a folder"""
        descriptions = {
            'config': 'Configuration files for pipeline behavior, phase mappings, and operation taxonomy. Edit these to change system behavior.',
            'schemas': 'All process step schemas. Contains source (editable), unified (generated), and expanded versions.',
            'schemas/source': 'SOURCE OF TRUTH. Edit these 5 YAML files to modify process steps. All other files regenerate from these.',
            'schemas/unified': 'AUTO-GENERATED unified schemas. Never edit directly. Regenerated by pipeline.',
            'schemas/expanded': 'AUTO-GENERATED expanded schemas with substeps recursively expanded.',
            'tools': 'Automation scripts. 17+ Python tools for merge, index, validate, generate, and watch operations.',
            'tools/dag': 'DAG (Directed Acyclic Graph) generation and validation tools for workflow dependencies.',
            'indices': 'AUTO-GENERATED indices and reports. Master index enables fast queries across 7 dimensions.',
            'indices/archived': 'Archived historical indices for reference.',
            'guides': 'Documentation and guides for users, developers, and AI agents.',
            'tests': 'Test suite with 43 automated tests. 85% code coverage. Run with run_all_tests.py.',
            'workspace': 'Temporary workspace for development and experimental features.',
            'workspace_ARCHIVE': 'Archived workspace files from previous development iterations.',
        }

        rel_path = str(folder_path.relative_to(self.root_path)).replace('\\', '/')
        if rel_path in descriptions:
            return descriptions[rel_path]

        return f'Directory: {folder_path.name}'

    def get_relationships(self, file_path: Path) -> List[str]:
        """Identify relationships and dependencies for a file"""
        relationships = []
        filename = file_path.name

        # Define relationships
        if filename == 'pfa_run_pipeline.py':
            relationships = [
                'orchestrates: pfa_merge_schemas.py, pfa_build_master_index.py, generate_explained_steps.py, pfa_validate_e2e_pipeline.py',
                'reads: config/pipeline_config.yaml',
                'uses: pfa_common.py',
                'generates: all files in schemas/unified/, indices/, guides/'
            ]
        elif filename == 'pfa_merge_schemas.py':
            relationships = [
                'reads: schemas/source/*.yaml, config/phase_mappings.yaml, config/operation_taxonomy.yaml',
                'uses: pfa_common.py',
                'generates: schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml, indices/merge_report.json'
            ]
        elif filename == 'pfa_build_master_index.py':
            relationships = [
                'reads: schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml',
                'uses: pfa_common.py',
                'generates: indices/master_index.json'
            ]
        elif filename == 'pfa_validate_e2e_pipeline.py':
            relationships = [
                'reads: schemas/unified/*.yaml, indices/master_index.json',
                'uses: pfa_common.py',
                'generates: indices/validation_report.json'
            ]
        elif filename == 'pfa_watch.py':
            relationships = [
                'monitors: schemas/source/*.yaml',
                'executes: pfa_run_pipeline.py',
                'uses: pfa_common.py'
            ]
        elif filename in ['PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA.yaml',
                         'PFA_PATTERNS_PROCESS_STEPS_SCHEMA.yaml',
                         'PFA_GLOSSARY_PROCESS_STEPS_SCHEMA.yaml',
                         'PFA_SSOT_PROCESS_STEPS_SCHEMA.yaml',
                         'PFA_PROCESS_STEPS_SCHEMA.yaml',
                         'PFA_DIRECTORY_INTEGRATION_PROCESS_STEPS_SCHEMA.yaml']:
            relationships = [
                'source_for: schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml',
                'processed_by: pfa_merge_schemas.py',
                'indexed_by: pfa_build_master_index.py'
            ]

        return relationships

    def build_structure(self, path: Path, max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
        """Recursively build documentation structure"""
        if current_depth > max_depth:
            return None

        name = path.name
        is_dir = path.is_dir()

        # Skip hidden files and certain directories
        if name.startswith('.') and name != '.dir_id':
            return None

        result = {
            'name': name,
            'type': 'directory' if is_dir else 'file',
            'path': str(path.relative_to(self.root_path)).replace('\\', '/')
        }

        # Extract or generate doc_id
        if not is_dir:
            extracted_doc_id = self.extract_doc_id_from_file(path)
            if extracted_doc_id:
                result['doc_id'] = extracted_doc_id
            else:
                result['doc_id'] = self.generate_doc_id(name, path)
        else:
            result['doc_id'] = self.generate_doc_id(name, path)

        # Add description
        if is_dir:
            result['description'] = self.get_folder_description(path)
        else:
            result['description'] = self.get_file_description(path)
            result['size_bytes'] = path.stat().st_size
            result['extension'] = path.suffix

        # Add relationships
        if not is_dir:
            relationships = self.get_relationships(path)
            if relationships:
                result['relationships'] = relationships

        # Add AI usage notes for key files
        if not is_dir:
            ai_notes = self.get_ai_usage_notes(path)
            if ai_notes:
                result['ai_usage_notes'] = ai_notes

        # Recursively process children for directories
        if is_dir:
            children = []
            try:
                for child in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                    child_doc = self.build_structure(child, max_depth, current_depth + 1)
                    if child_doc:
                        children.append(child_doc)
            except PermissionError:
                pass

            if children:
                result['children'] = children
                result['child_count'] = len(children)

        return result

    def get_ai_usage_notes(self, file_path: Path) -> Optional[str]:
        """Provide AI-specific usage notes for key files"""
        filename = file_path.name

        notes = {
            'pfa_run_pipeline.py': 'AI should recommend running this after any schema edits. Use --quick for incremental builds.',
            'pfa_common.py': 'Import and use these utilities for consistent file operations. All tools depend on this.',
            'master_index.json': 'Query this for fast lookups. Contains 7 index types: by_phase, by_component, by_operation, by_workflow, dependencies, cross_references, step_lookup.',
            'pipeline_config.yaml': 'Modify this to change pipeline behavior. Never hardcode what can be configured here.',
            'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml': 'READ-ONLY for AI. This is auto-generated. Edit source schemas instead.',
            'CLAUDE.md': 'Read this first for comprehensive understanding of system architecture and workflows.',
            'README.md': 'Entry point for understanding the system. Contains quick start and feature overview.',
        }

        return notes.get(filename)

    def build_documentation(self) -> Dict[str, Any]:
        """Build complete documentation structure"""
        print("Building comprehensive documentation...")

        structure = self.build_structure(self.root_path)

        documentation = {
            'metadata': {
                'root_path': str(self.root_path),
                'generated_at': '2026-01-09',
                'system_name': 'PROCESS_STEP_LIB',
                'version': '1.0.0',
                'description': 'Unified E2E Process Step Schema System with 274 steps from 5 sources',
                'total_files': len([k for k, v in self.doc_id_map.items() if Path(v).is_file()]),
                'total_directories': len([k for k, v in self.doc_id_map.items() if Path(v).is_dir()]),
                'doc_id_system_note': 'Each file and folder has a unique doc_id for AI reference. Extracted from file frontmatter where available, generated otherwise.'
            },
            'system_overview': {
                'purpose': 'Consolidates 5 incompatible process schemas (274 steps) into single unified pipeline with automation',
                'core_concepts': [
                    'SSOT (Single Source of Truth) - Edit source schemas only, regenerate everything else',
                    '9 Universal Phases - Bootstrap → Discovery → Design → Approval → Registration → Execution → Consolidation → Maintenance → Sync',
                    '7-Dimensional Indexing - Multiple concurrent query interfaces for fast lookups',
                    'Configuration-Driven - Logic decoupled from config, change behavior via YAML',
                    'One-Command Automation - pfa_run_pipeline.py regenerates 30+ artifacts in seconds'
                ],
                'workflow': 'Edit schemas/source/*.yaml → Run pfa_run_pipeline.py → All artifacts regenerate → Run tests → Commit',
                'key_directories': {
                    'schemas/source/': 'EDITABLE - Source of truth for all process steps',
                    'schemas/unified/': 'GENERATED - Never edit, always regenerate',
                    'config/': 'EDITABLE - Configuration for pipeline behavior',
                    'tools/': 'SCRIPTS - Automation and processing tools',
                    'indices/': 'GENERATED - Queryable indices and reports',
                    'guides/': 'DOCUMENTATION - User and developer guides',
                    'tests/': 'TESTS - Automated test suite (43 tests, 85% coverage)'
                }
            },
            'structure': structure
        }

        return documentation

def main():
    root = Path(__file__).parent
    builder = DocumentationBuilder(root)

    print(f"Scanning: {root}")
    documentation = builder.build_documentation()

    output_file = root / 'COMPREHENSIVE_TECHNICAL_DOCUMENTATION.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documentation, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Documentation generated: {output_file}")
    print(f"   Total files documented: {documentation['metadata']['total_files']}")
    print(f"   Total directories documented: {documentation['metadata']['total_directories']}")
    print(f"   Total doc_ids assigned: {len(builder.doc_id_map)}")

if __name__ == '__main__':
    main()
