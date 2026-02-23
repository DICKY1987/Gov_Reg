"""
FactsExtractor - Per-File Facts Extraction

Extracts AST-based facts from source files:
- Imports, classes, functions, constants
- Capability inference
- Entry point detection

FILE_ID: 01999000042260125145
"""

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from P_01260207233100000010_canonical_hash import hash_canonical_data, hash_file_content


class FactsExtractor:
    """
    Extract facts from source files using AST parsing.
    
    Supports Python (via ast), JSON, YAML, and Markdown files.
    """
    
    def __init__(self, vocab_validator=None):
        """
        Initialize facts extractor.
        
        Args:
            vocab_validator: Optional VocabularyValidator for capability validation
        """
        self.vocab_validator = vocab_validator
    
    def extract(self, file_path: Path, file_id: str) -> Dict[str, Any]:
        """
        Extract facts from a file.
        
        Args:
            file_path: Path to file
            file_id: 20-digit file ID
            
        Returns:
            Facts dict
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine language
        language = self._detect_language(file_path)
        
        # Extract facts based on language
        if language == "python":
            facts = self._extract_python_facts(file_path)
        elif language == "json":
            facts = self._extract_json_facts(file_path)
        else:
            facts = self._extract_generic_facts(file_path)
        
        # Validate capabilities if validator provided
        if self.vocab_validator and facts.get("capabilities"):
            valid, invalid = self.vocab_validator.validate_batch(facts["capabilities"])
            if invalid:
                facts.setdefault("extraction_errors", []).append(
                    f"Invalid capabilities: {', '.join(invalid)}"
                )
        
        # Build complete facts artifact
        artifact = {
            "file_id": file_id,
            "relative_path": str(file_path),
            "source_sha256": hash_file_content(file_path),
            "facts_schema_version": "1.0.0",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "language": language,
            "facts": facts,
            "content_hash": hash_canonical_data(facts)
        }
        
        return artifact
    
    def extract_and_save(
        self,
        file_path: Path,
        file_id: str,
        output_dir: Path
    ) -> Path:
        """
        Extract facts and save to <file_id>.facts.json.
        
        Args:
            file_path: Path to source file
            file_id: 20-digit file ID
            output_dir: Directory to save facts artifact
            
        Returns:
            Path to saved facts file
        """
        facts = self.extract(file_path, file_id)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        facts_path = output_dir / f"{file_id}.facts.json"
        facts_path.write_text(
            json.dumps(facts, indent=2),
            encoding='utf-8'
        )
        
        return facts_path
    
    def batch_extract(
        self,
        file_list: List[Tuple[Path, str]],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Extract facts from multiple files.
        
        Args:
            file_list: List of (file_path, file_id) tuples
            output_dir: Directory to save facts artifacts
            
        Returns:
            Summary dict with counts and errors
        """
        summary = {
            "total": len(file_list),
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }
        
        for file_path, file_id in file_list:
            try:
                self.extract_and_save(file_path, file_id, output_dir)
                summary["succeeded"] += 1
            except Exception as e:
                summary["failed"] += 1
                summary["errors"].append({
                    "file_path": str(file_path),
                    "file_id": file_id,
                    "error": str(e)
                })
        
        return summary
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect file language from extension."""
        suffix = file_path.suffix.lower()
        
        if suffix == ".py":
            return "python"
        elif suffix == ".json":
            return "json"
        elif suffix in [".yml", ".yaml"]:
            return "yaml"
        elif suffix in [".md", ".markdown"]:
            return "markdown"
        else:
            return "unknown"
    
    def _extract_python_facts(self, file_path: Path) -> Dict[str, Any]:
        """Extract facts from Python file using AST."""
        try:
            source = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            return {
                "imports": [],
                "classes": [],
                "functions": [],
                "constants": [],
                "capabilities": [],
                "entry_points": [],
                "extraction_errors": [f"AST parse error: {str(e)}"]
            }
        
        facts = {
            "imports": self._extract_imports(tree),
            "classes": self._extract_classes(tree),
            "functions": self._extract_functions(tree),
            "constants": self._extract_constants(tree),
            "capabilities": self._infer_capabilities(tree, source),
            "entry_points": self._detect_entry_points(tree)
        }
        
        return facts
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import statements."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "names": [],
                        "alias": alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append({
                    "module": module,
                    "names": names,
                    "alias": None
                })
        
        return imports
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_name(base) for base in node.bases]
                methods = []
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        decorators = [self._get_name(d) for d in item.decorator_list]
                        methods.append({
                            "name": item.name,
                            "decorators": decorators
                        })
                
                decorators = [self._get_name(d) for d in node.decorator_list]
                
                classes.append({
                    "name": node.name,
                    "bases": bases,
                    "methods": methods,
                    "decorators": decorators
                })
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract top-level function definitions."""
        functions = []
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                args = [arg.arg for arg in node.args.args]
                decorators = [self._get_name(d) for d in node.decorator_list]
                
                functions.append({
                    "name": node.name,
                    "args": args,
                    "decorators": decorators,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })
        
        return functions
    
    def _extract_constants(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract module-level constants."""
        constants = []
        
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.isupper():  # Convention: constants are uppercase
                            value = None
                            value_type = "unknown"
                            
                            if isinstance(node.value, ast.Constant):
                                value = node.value.value
                                value_type = type(value).__name__
                            
                            constants.append({
                                "name": name,
                                "type": value_type,
                                "value": value
                            })
        
        return constants
    
    def _infer_capabilities(self, tree: ast.AST, source: str) -> List[str]:
        """Infer capability tags from code patterns."""
        capabilities = set()
        
        # Check for FILE_ID pattern in docstrings/comments
        if "FILE_ID:" in source or "file_id:" in source:
            capabilities.add("CAP-IDS-SCAN")
        
        # Check for COUNTER_STORE access
        if "COUNTER_STORE" in source:
            capabilities.add("CAP-IDS-ALLOCATE")
        
        # Check for REGISTRY_file access
        if "REGISTRY_file.json" in source:
            capabilities.add("CAP-REGISTRY-SCAN")
        
        # Check for schema validation imports
        imports = self._extract_imports(tree)
        for imp in imports:
            if "jsonschema" in imp["module"]:
                capabilities.add("CAP-REGISTRY-VALIDATE")
            if "subprocess" in imp["module"]:
                capabilities.add("CAP-ORCHESTRATION-RUN")
        
        return list(capabilities)
    
    def _detect_entry_points(self, tree: ast.AST) -> List[Dict[str, str]]:
        """Detect entry points (main, CLI, etc.)."""
        entry_points = []
        
        # Check for if __name__ == "__main__"
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    if (isinstance(node.test.left, ast.Name) and 
                        node.test.left.id == "__name__"):
                        entry_points.append({
                            "type": "main",
                            "name": "__main__"
                        })
        
        # Check for argparse usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "ArgumentParser":
                        entry_points.append({
                            "type": "cli",
                            "name": "argparse"
                        })
        
        return entry_points
    
    def _extract_json_facts(self, file_path: Path) -> Dict[str, Any]:
        """Extract facts from JSON file."""
        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            
            return {
                "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
                "schema_ref": data.get("$schema") if isinstance(data, dict) else None,
                "is_array": isinstance(data, list),
                "is_object": isinstance(data, dict)
            }
        except Exception as e:
            return {
                "extraction_errors": [f"JSON parse error: {str(e)}"]
            }
    
    def _extract_generic_facts(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic facts from unknown file types."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            return {
                "line_count": content.count('\n') + 1,
                "char_count": len(content),
                "has_file_id": "FILE_ID:" in content or "file_id:" in content
            }
        except Exception as e:
            return {
                "extraction_errors": [f"Read error: {str(e)}"]
            }
    
    @staticmethod
    def _get_name(node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{FactsExtractor._get_name(node.value)}.{node.attr}"
        else:
            return "unknown"
