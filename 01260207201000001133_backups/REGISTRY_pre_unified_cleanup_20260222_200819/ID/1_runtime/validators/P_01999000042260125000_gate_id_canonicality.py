"""
Pre-commit Gate: ID Canonicality Enforcement

FILE_ID: 01999000042260125000
DOC_ID: P_01999000042260125000

Enforces:
1. No imports of DEPRECATED or INTERNAL ID modules
2. No bespoke ID regex patterns (must use canonical patterns module)
3. No ad-hoc allocator definitions (must use facade)
4. New ID scripts must be inventoried before commit

Contract: docs/ID_IDENTITY_CONTRACT.md
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.P_01999000042260125003_repo_root import get_repo_root


class IDCanonicalityGate:
    """
    Pre-commit gate that enforces ID canonicality rules.
    
    Reads ID_SCRIPT_INVENTORY.jsonl as SSOT and blocks violations.
    """
    
    def __init__(self):
        """Initialize gate with repo context and inventory."""
        self.repo_root = get_repo_root()
        self.inventory_path = self.repo_root / "ID_SCRIPT_INVENTORY.jsonl"
        
        # Canonical module references
        self.canonical_patterns_module = "govreg_core.P_01999000042260125002_canonical_id_patterns"
        self.canonical_facade_module = "govreg_core.P_01999000042260125006_id_allocator_facade"
        
        # Load inventory
        self.inventory_records = []
        self.deprecated_modules = set()
        self.internal_modules = set()
        self.inventory_paths = set()
        
        self._load_inventory()
    
    def _load_inventory(self):
        """Load and parse inventory JSONL."""
        if not self.inventory_path.exists():
            print(f"ERROR: Inventory not found: {self.inventory_path}", file=sys.stderr)
            print("Cannot enforce canonicality without inventory.", file=sys.stderr)
            sys.exit(1)
        
        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"ERROR: Invalid JSON at line {line_num}: {e}", file=sys.stderr)
                    sys.exit(1)
                
                # First line is meta record
                if record.get("record_type") == "meta":
                    schema_version = record.get("schema_version")
                    if schema_version != "2.1.4":
                        print(f"ERROR: Inventory schema version mismatch", file=sys.stderr)
                        print(f"  Expected: 2.1.4", file=sys.stderr)
                        print(f"  Found: {schema_version}", file=sys.stderr)
                        sys.exit(1)
                    continue
                
                self.inventory_records.append(record)
                
                # Build enforcement sets
                import_module = record.get("import_module")
                canonicality = record.get("canonicality")
                relative_path = record.get("relative_path")
                
                if relative_path:
                    self.inventory_paths.add(relative_path)
                
                if import_module and canonicality == "DEPRECATED":
                    self.deprecated_modules.add(import_module)
                
                if import_module and canonicality == "INTERNAL":
                    self.internal_modules.add(import_module)
    
    def get_staged_files(self) -> List[Path]:
        """Get list of staged Python files."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_root
            )
            
            staged = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                path = self.repo_root / line
                if path.suffix == '.py' and path.exists():
                    staged.append(path)
            
            return staged
        
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to get staged files: {e}", file=sys.stderr)
            sys.exit(1)
    
    def check_deprecated_imports(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Check for imports of DEPRECATED ID modules."""
        violations = []
        
        for node in ast.walk(tree):
            # ImportFrom: from X import Y
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                
                # Exact match or submodule match
                if module in self.deprecated_modules:
                    violations.append(
                        f"DEPRECATED IMPORT BLOCKED: {file_path.name} imports {module}\n"
                        f"  Line {node.lineno}: from {module} import ...\n"
                        f"  This module is deprecated. See ID_SCRIPT_INVENTORY.jsonl for replacement."
                    )
                else:
                    # Check submodule imports (e.g., deprecated_mod.submod)
                    for dep_mod in self.deprecated_modules:
                        if module.startswith(dep_mod + '.'):
                            violations.append(
                                f"DEPRECATED SUBMODULE IMPORT BLOCKED: {file_path.name} imports {module}\n"
                                f"  Line {node.lineno}: from {module} import ...\n"
                                f"  Parent module {dep_mod} is deprecated."
                            )
                            break
            
            # Import: import X
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    
                    if module in self.deprecated_modules:
                        violations.append(
                            f"DEPRECATED IMPORT BLOCKED: {file_path.name} imports {module}\n"
                            f"  Line {node.lineno}: import {module}\n"
                            f"  This module is deprecated. See ID_SCRIPT_INVENTORY.jsonl for replacement."
                        )
                    else:
                        for dep_mod in self.deprecated_modules:
                            if module.startswith(dep_mod + '.'):
                                violations.append(
                                    f"DEPRECATED SUBMODULE IMPORT BLOCKED: {file_path.name} imports {module}\n"
                                    f"  Line {node.lineno}: import {module}\n"
                                    f"  Parent module {dep_mod} is deprecated."
                                )
                                break
        
        return violations
    
    def check_internal_imports(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Check for imports of INTERNAL ID modules (backend allocators)."""
        violations = []
        
        # Skip if this IS the canonical facade
        rel_path = str(file_path.relative_to(self.repo_root)).replace('\\', '/')
        if rel_path == 'govreg_core/P_01999000042260125006_id_allocator_facade.py':
            return violations
        
        for node in ast.walk(tree):
            # ImportFrom: from X import Y
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                
                if module in self.internal_modules:
                    violations.append(
                        f"INTERNAL IMPORT BLOCKED: {file_path.name} imports {module}\n"
                        f"  Line {node.lineno}: from {module} import ...\n"
                        f"  This is a backend allocator. Use canonical facade instead:\n"
                        f"    from {self.canonical_facade_module} import allocate_id"
                    )
                else:
                    for int_mod in self.internal_modules:
                        if module.startswith(int_mod + '.'):
                            violations.append(
                                f"INTERNAL SUBMODULE IMPORT BLOCKED: {file_path.name} imports {module}\n"
                                f"  Line {node.lineno}: from {module} import ...\n"
                                f"  Parent module {int_mod} is internal. Use canonical facade."
                            )
                            break
            
            # Import: import X
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    
                    if module in self.internal_modules:
                        violations.append(
                            f"INTERNAL IMPORT BLOCKED: {file_path.name} imports {module}\n"
                            f"  Line {node.lineno}: import {module}\n"
                            f"  This is a backend allocator. Use canonical facade instead:\n"
                            f"    from {self.canonical_facade_module} import allocate_id"
                        )
                    else:
                        for int_mod in self.internal_modules:
                            if module.startswith(int_mod + '.'):
                                violations.append(
                                    f"INTERNAL SUBMODULE IMPORT BLOCKED: {file_path.name} imports {module}\n"
                                    f"  Line {node.lineno}: import {module}\n"
                                    f"  Parent module {int_mod} is internal. Use canonical facade."
                                )
                                break
        
        return violations
    
    def check_bespoke_regex(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Check for bespoke ID regex patterns."""
        violations = []
        
        # Skip the canonical patterns module itself
        rel_path = str(file_path.relative_to(self.repo_root)).replace('\\', '/')
        if rel_path == 'govreg_core/P_01999000042260125002_canonical_id_patterns.py':
            return violations
        
        # ID pattern indicators
        id_indicators = [r'\d{20}', r'\d{22}', r'P_\d']
        
        # Check string literals for ID patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                
                # Check if contains ID pattern indicators
                contains_id_pattern = any(ind in s for ind in id_indicators)
                if not contains_id_pattern:
                    continue
                
                # Ignore benign strings (URLs, markdown, etc.)
                if any(benign in s for benign in ['http', 'README', 'example', 'test_']):
                    continue
                
                violations.append(
                    f"BESPOKE ID PATTERN BLOCKED: {file_path.name} contains inline ID pattern\n"
                    f"  Line {getattr(node, 'lineno', '?')}: string literal contains ID-pattern token\n"
                    f"  Action: Use canonical patterns module:\n"
                    f"    from {self.canonical_patterns_module} import ID_20_DIGIT_RE, FILENAME_PREFIX_RE"
                )
        
        # Check re.compile calls with ID patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Match: re.compile(...)
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'compile' and
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 're'):
                    
                    if node.args and isinstance(node.args[0], ast.Constant):
                        pattern = node.args[0].value
                        if isinstance(pattern, str) and any(ind in pattern for ind in id_indicators):
                            violations.append(
                                f"BESPOKE REGEX BLOCKED: {file_path.name} defines ID regex via re.compile\n"
                                f"  Line {node.lineno}: re.compile(...) with ID-pattern\n"
                                f"  Action: Use canonical patterns module:\n"
                                f"    from {self.canonical_patterns_module} import FILENAME_PREFIX_RE"
                            )
        
        return violations
    
    def check_adhoc_allocator_definitions(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Check for ad-hoc allocator function definitions."""
        violations = []
        
        # Skip canonical facade itself
        rel_path = str(file_path.relative_to(self.repo_root)).replace('\\', '/')
        if rel_path == 'govreg_core/P_01999000042260125006_id_allocator_facade.py':
            return violations
        
        # Allocator-like function names
        allocator_like = {
            'allocate_id', 'allocate_file_id', 'allocate_enhanced_id',
            'generate_id', 'next_id', 'new_id', 'allocate'
        }
        
        # Check if facade is imported
        imports_facade = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == self.canonical_facade_module:
                imports_facade = True
                break
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == self.canonical_facade_module:
                        imports_facade = True
                        break
        
        # Find function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in allocator_like:
                if not imports_facade:
                    violations.append(
                        f"AD-HOC ALLOCATOR BLOCKED: {file_path.name} defines '{node.name}' without facade\n"
                        f"  Line {node.lineno}: def {node.name}(...)\n"
                        f"  Action: Remove implementation and call facade:\n"
                        f"    from {self.canonical_facade_module} import allocate_id"
                    )
        
        return violations
    
    def check_inventory_freshness(self, staged_files: List[Path]) -> List[str]:
        """Check that new ID scripts are inventoried."""
        violations = []
        id_pattern = re.compile(r'^(?:P_)?\d{20}_.*\.py$')
        
        for file_path in staged_files:
            if id_pattern.match(file_path.name):
                rel_path = str(file_path.relative_to(self.repo_root)).replace('\\', '/')
                if rel_path not in self.inventory_paths:
                    violations.append(
                        f"NEW ID SCRIPT NOT INVENTORIED: {rel_path}\n"
                        f"  New ID-prefixed scripts must be added to inventory before commit.\n"
                        f"  Action: Run inventory analysis:\n"
                        f"    python scripts/P_01999000042260124999_id_canonicality_enforcer.py --action analyze"
                    )
        
        return violations
    
    def run(self) -> int:
        """Run gate checks on staged files."""
        staged_files = self.get_staged_files()
        
        if not staged_files:
            # No Python files staged
            return 0
        
        print(f"ID Canonicality Gate: Checking {len(staged_files)} staged Python files...")
        
        all_violations = []
        
        # Check inventory freshness first
        freshness_violations = self.check_inventory_freshness(staged_files)
        all_violations.extend(freshness_violations)
        
        # Check each staged file
        for file_path in staged_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                print(f"WARNING: Syntax error in {file_path.name}, skipping: {e}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"WARNING: Failed to parse {file_path.name}: {e}", file=sys.stderr)
                continue
            
            # Run all checks
            all_violations.extend(self.check_deprecated_imports(file_path, tree))
            all_violations.extend(self.check_internal_imports(file_path, tree))
            all_violations.extend(self.check_bespoke_regex(file_path, tree))
            all_violations.extend(self.check_adhoc_allocator_definitions(file_path, tree))
        
        # Report results
        if all_violations:
            print("\n" + "="*70, file=sys.stderr)
            print("ID CANONICALITY GATE: VIOLATIONS DETECTED", file=sys.stderr)
            print("="*70, file=sys.stderr)
            
            for i, violation in enumerate(all_violations, 1):
                print(f"\n[{i}] {violation}", file=sys.stderr)
            
            print("\n" + "="*70, file=sys.stderr)
            print(f"COMMIT BLOCKED: {len(all_violations)} violation(s) found", file=sys.stderr)
            print("="*70 + "\n", file=sys.stderr)
            return 1
        
        print("✓ All ID canonicality checks passed")
        return 0


def main():
    """Entry point for pre-commit hook."""
    gate = IDCanonicalityGate()
    sys.exit(gate.run())


if __name__ == '__main__':
    main()
