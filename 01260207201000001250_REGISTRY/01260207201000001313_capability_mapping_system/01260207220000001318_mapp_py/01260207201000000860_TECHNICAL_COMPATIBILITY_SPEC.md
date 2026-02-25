# Technical Compatibility Specification for mapp_py Scripts

**Version**: 2.1
**Date**: 2026-02-02
**Work ID**: WORK-MAPP-PY-001

---

## Overview

This document provides detailed technical specifications for all 18 mapp_py analyzer scripts to ensure cross-platform compatibility, deterministic behavior, and proper integration with the registry system.

---

## Global Compatibility Requirements

### Python Version
- **Minimum**: Python 3.9
- **Maximum**: Python 3.12
- **Tested**: 3.9, 3.10, 3.11
- **Recommended**: 3.11 (best performance + type hints)

### Platform Support
- ✅ Windows (tested on Windows 11)
- ✅ Linux (Ubuntu 20.04+, RHEL 8+)
- ✅ macOS (10.15+)

### File Encoding
- **All files**: UTF-8 with BOM optional
- **Newlines**: LF (Unix) or CRLF (Windows) - normalized internally
- **Encoding detection**: chardet library for non-UTF-8 files

### Registry Integration
- **Format**: JSON (RFC 8259)
- **Schema Version**: v3
- **Column Dictionary**: Min version 4.1.1
- **Write Protocol**: RFC-6902 JSON Patch
- **Atomicity**: Single-writer lock + atomic rename

---

## Script-Specific Technical Details

### 1. python_ast_parser.py ✅ IMPLEMENTED

**Location**: `py_parser_files/DOC-SCRIPT-0996__python_ast_parser.py`

**Technical Specs**:
```python
Input:  Path | str (Python source file)
Output: ParseResult {
    success: bool
    ast_tree: ast.AST | None
    ast_dump: str
    ast_dump_hash: str  # SHA256, 64-char hex
    parse_errors: List[str]
}
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes (no shared state)
- Timeout: 500ms default
- Stdlib only: Yes

**Key Functions**:
```python
def parse_file(path: Path) -> ParseResult
def parse_string(source: str) -> ParseResult
def get_ast_hash(tree: ast.AST) -> str
```

**Error Handling**:
- Syntax errors → Returns `ParseResult(success=False, parse_errors=[...])`
- File not found → Raises `FileNotFoundError`
- Timeout → Raises `TimeoutError`

**Validation**:
- Input: File must be readable UTF-8 or detectable encoding
- Output: `ast_dump_hash` matches `^[0-9a-f]{64}$`

---

### 2. component_extractor.py ⚠️ STUBBED

**Location**: `mapp_py/DOC-SCRIPT-1267__component_extractor.py`

**Technical Specs**:
```python
Input:  ast.AST
Output: List[Component] {
    kind: "function" | "class" | "method"
    name: str
    qualname: str  # e.g., "MyClass.method"
    signature: str  # with type hints
    docstring: str | None
    is_public: bool  # not starts with _
    decorators: List[str]
    lineno: int
}
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes
- Stdlib only: Yes

**Key Functions**:
```python
def extract(ast_tree: ast.AST) -> List[Component]
def extract_functions(node: ast.Module) -> List[FunctionComponent]
def extract_classes(node: ast.Module) -> List[ClassComponent]
def extract_methods(class_node: ast.ClassDef) -> List[MethodComponent]
def get_public_api_signature(components: List) -> str
```

**Error Handling**:
- Invalid AST → Returns empty list
- Missing docstrings → Returns None for docstring field

**Validation**:
- Input: Must be valid `ast.AST` object
- Output: `py_defs_public_api_hash` matches `^[0-9a-f]{64}$`

---

### 3. component_id_generator.py ⚠️ STUBBED

**Location**: `mapp_py/DOC-SCRIPT-1268__component_id_generator.py`

**Technical Specs**:
```python
Input:  file_id: str (20 digits) + List[Component]
Output: List[str] (component IDs matching COMP-[0-9a-f]{12})

Hash Input Format: "{file_id}|{kind}|{qualname}|{signature}"
Hash Algorithm: SHA256 (first 6 bytes)
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes
- Deterministic: **MUST** be reproducible
- Stdlib only: Yes

**Key Functions**:
```python
def generate_id(file_id: str, kind: str, qualname: str, signature: str) -> str
def validate_id(component_id: str) -> bool
def batch_generate(file_id: str, components: List[Component]) -> List[str]
```

**Error Handling**:
- Invalid `file_id` (not 20 digits) → Raises `ValueError`
- Empty signature → Uses empty string in hash

**Critical Requirements**:
1. ⚠️ **MUST use `file_id` (20 digits), NOT `doc_id`**
2. Hash input MUST be deterministic (same order, same format)
3. IDs MUST be reproducible across runs and Python versions

**Validation**:
- Input: `file_id` matches `^[0-9]{20}$`
- Output: Each ID matches `^COMP-[0-9a-f]{12}$`

---

### 4. dependency_analyzer.py ⚠️ STUBBED

**Location**: `mapp_py/DOC-SCRIPT-1269__dependency_analyzer.py`

**Technical Specs**:
```python
Input:  ast.AST
Output: DependencyReport {
    stdlib: List[str]  # sorted
    third_party: List[str]  # sorted
    local: List[str]  # sorted (relative imports)
    imports_hash: str  # SHA256, 64-char hex
}
```

**Compatibility**:
- Python: **3.10+** (requires `sys.stdlib_module_names`)
- Thread-safe: Yes
- Async-safe: Yes
- Stdlib only: Yes

**Categorization Logic**:
- **stdlib**: Check against `sys.stdlib_module_names` (3.10+)
- **local**: Starts with `.` or `..` (relative imports)
- **third_party**: Everything else

**Key Functions**:
```python
def analyze(ast_tree: ast.AST) -> DependencyReport
def extract_imports(node: ast.Module) -> List[Import]
def categorize_import(module_name: str) -> ImportCategory
def get_imports_hash(imports: List[str]) -> str
```

**Error Handling**:
- Invalid AST → Returns empty lists
- Malformed imports → Skips and logs warning

**Validation**:
- Input: Must be valid `ast.AST`
- Output: All lists sorted alphabetically, hash matches `^[0-9a-f]{64}$`

**Note**: For Python 3.9, maintain manual stdlib list or use `isort.stdlibs`

---

### 5. io_surface_analyzer.py ⚠️ STUBBED

**Location**: `mapp_py/DOC-SCRIPT-1271__io_surface_analyzer.py`

**Technical Specs**:
```python
Input:  ast.AST
Output: IOSurfaceReport {
    io_flags: {
        file_read: bool
        file_write: bool
        network: bool
        subprocess: bool
        env_read: bool
        db_access: bool
    }
    inputs: List[str]  # CLI args, env vars, config files
    outputs: List[str]  # Files written, registries updated
    security_risks: List[str]  # Enum of risk patterns
}
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes
- Stdlib only: Yes

**Detection Patterns**:
```python
file_read: ["open()", "Path.read_text()", "Path.read_bytes()", "io.open()"]
file_write: ["open('w')", "Path.write_text()", "Path.write_bytes()"]
network: ["requests", "urllib", "socket", "http.client", "aiohttp"]
subprocess: ["subprocess", "os.system()", "os.popen()", "os.exec*"]
env_read: ["os.environ", "os.getenv()", "dotenv.load_dotenv()"]
db_access: ["sqlalchemy", "pymongo", "psycopg2", "mysql.connector"]
```

**Security Risk Enum**:
```python
["uses_eval", "shell_injection_risk", "network_access",
 "subprocess_calls", "env_manipulation", "file_system_write"]
```

**Key Functions**:
```python
def analyze(ast_tree: ast.AST) -> IOSurfaceReport
def detect_file_operations(tree: ast.AST) -> FileOps
def detect_network_access(tree: ast.AST) -> bool
def detect_subprocess_calls(tree: ast.AST) -> List[SubprocessCall]
def extract_cli_arguments(tree: ast.AST) -> List[str]
def extract_security_risks(tree: ast.AST) -> List[str]
```

**Error Handling**:
- Invalid AST → Returns all flags as `False`
- Ambiguous patterns → Conservative (flag as present)

---

### 6. text_normalizer.py ❌ MISSING (TO BE CREATED)

**Location**: `mapp_py/DOC-SCRIPT-XXXX__text_normalizer.py`

**Technical Specs**:
```python
Input:  bytes | str (raw source code)
Output: NormalizedText {
    normalized: str  # UTF-8, LF newlines
    canonical_hash: str  # SHA256, 64-char hex
    changes_made: List[str]  # e.g., ["CRLF->LF", "removed BOM"]
}
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes
- Stdlib only: Yes

**Normalization Steps**:
1. Detect encoding (prefer UTF-8, fallback to chardet)
2. Convert to UTF-8
3. Remove BOM if present
4. Normalize newlines (CRLF → LF, CR → LF)
5. Strip trailing whitespace per line (optional)
6. Ensure file ends with single newline

**Key Functions**:
```python
def normalize(source: bytes | str) -> NormalizedText
def normalize_encoding(source: bytes) -> str
def normalize_newlines(source: str) -> str
def calculate_canonical_hash(normalized: str) -> str
```

**Error Handling**:
- Undetectable encoding → Raises `UnicodeDecodeError`
- Binary file → Raises `ValueError`

**Validation**:
- Output: `canonical_hash` matches `^[0-9a-f]{64}$`

---

### 7. deliverable_analyzer.py ❌ MISSING (TO BE CREATED)

**Location**: `mapp_py/DOC-SCRIPT-XXXX__deliverable_analyzer.py`

**Technical Specs**:
```python
Input:  AnalysisContext {
    ast_tree: ast.AST
    components: List[Component]
    io_surface: IOSurfaceReport
}
Output: DeliverableReport {
    kinds: List[str]  # from enum
    signature_hash: str  # SHA256, 64-char hex
    inputs: List[str]
    outputs: List[str]
    interfaces: List[str]  # CLI commands + public API
}
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes
- Stdlib only: Yes

**Deliverable Kinds Enum**:
```python
["cli_tool", "library_module", "daemon", "migration_script",
 "validator", "test_suite", "data_transformer", "api_server"]
```

**Classification Rules**:
```python
cli_tool: has argparse/click/typer + main entry point
library_module: has public API (functions/classes without __)
daemon: has infinite loop or service pattern
migration_script: has DB operations + one-time execution pattern
validator: has validation logic + assert/raise patterns
test_suite: filename starts with test_ or in tests/ directory
data_transformer: has read + transform + write pattern
api_server: has Flask/FastAPI/Django patterns
```

**Key Functions**:
```python
def analyze(context: AnalysisContext) -> DeliverableReport
def classify_kinds(ast_tree, components, io_surface) -> List[str]
def extract_interfaces(components, io_surface) -> List[str]
def build_fingerprint(kinds, inputs, outputs, interfaces) -> Dict
def calculate_signature_hash(fingerprint: Dict) -> str
```

**Error Handling**:
- Ambiguous classification → Returns multiple kinds
- No clear pattern → Returns empty list

**Validation**:
- Output: `signature_hash` matches `^[0-9a-f]{64}$`

---

### 8. capability_tagger.py ❌ MISSING (TO BE CREATED)

**Location**: `mapp_py/DOC-SCRIPT-XXXX__capability_tagger.py`

**Technical Specs**:
```python
Input:  AnalysisContext {
    ast_tree: ast.AST
    components: List[Component]
    dependencies: DependencyReport
    io_surface: IOSurfaceReport
}
Output: CapabilityReport {
    tags: List[str]  # from controlled vocabulary
    facts_hash: str  # SHA256, 64-char hex
    confidence: Dict[str, float]  # tag -> confidence score
}
```

**Compatibility**:
- Python: 3.9+
- Thread-safe: Yes
- Async-safe: Yes
- Stdlib only: Yes

**Controlled Vocabulary** (37 tags):
```python
[
    "registry_update", "path_resolve", "schema_validate",
    "file_system", "network_client", "cli_interface",
    "config_management", "logging", "error_handling",
    "async_processing", "parallel_execution", "caching",
    "serialization", "encryption", "compression",
    "testing", "mocking", "benchmarking",
    "database_access", "api_client", "web_scraping",
    "data_transformation", "validation", "normalization",
    "monitoring", "alerting", "reporting",
    "authentication", "authorization", "audit_logging",
    "backup_restore", "migration", "deployment",
    "documentation", "code_generation", "refactoring"
]
```

**Tagging Rules** (pattern matching):
```python
registry_update: writes to JSON/YAML registry files
path_resolve: uses pathlib/os.path extensively
schema_validate: imports jsonschema/pydantic/marshmallow
file_system: high file I/O operations
network_client: makes HTTP/socket requests
cli_interface: uses argparse/click/typer
config_management: reads .yaml/.json/.ini config
logging: uses logging/loguru/structlog
error_handling: extensive try/except + custom exceptions
async_processing: uses asyncio/trio/anyio
...
```

**Key Functions**:
```python
def tag(context: AnalysisContext) -> CapabilityReport
def detect_registry_access(ast_tree: ast.AST) -> bool
def detect_path_operations(ast_tree: ast.AST) -> bool
def detect_validation_patterns(ast_tree: ast.AST) -> bool
def calculate_facts_hash(facts: Dict) -> str
def calculate_confidence(tag: str, evidence: Dict) -> float
```

**Error Handling**:
- Unknown pattern → Skips tagging
- Low confidence (<0.5) → Omits tag

**Validation**:
- Output: All tags in controlled vocabulary, facts_hash matches `^[0-9a-f]{64}$`

---

### Phase B & C Scripts (Summary)

**Phase B (Dynamic Analysis)**:
- `test_runner.py`: Runs pytest, requires pytest/pytest-cov
- `linter_runner.py`: Runs ruff/mypy, requires external tools
- `complexity_analyzer.py`: Uses radon for McCabe complexity
- `quality_scorer.py`: Aggregates metrics, stdlib only

**Phase C (Similarity)**:
- `structural_similarity.py`: Tree edit distance, stdlib only
- `semantic_similarity.py`: Embeddings/TF-IDF, may require scikit-learn
- `file_comparator.py`: Composite scoring, stdlib only
- `similarity_clusterer.py`: Hash-based clustering, stdlib only
- `canonical_ranker.py`: Weighted ranking, stdlib only

**Phase Orchestrator**:
- `registry_integration_pipeline.py`: Main orchestrator
  - Coordinates all analyzers
  - Generates run_id, toolchain_id
  - Writes evidence to `.runs/{run_id}/`
  - Integrates with registry write protocol

---

## Encoding & Serialization Standards

### JSON Encoding (for registry)
```python
def canonical_json(obj: Any) -> str:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True
    )
```

### List Serialization
- **Always sort** unless order is semantically meaningful
- **Use alphabetical** sort for imports, tags, interfaces
- **Preserve order** for execution sequences (e.g., migration steps)

### Hash Generation (HASH_V1)
```python
def generate_hash(data: Any) -> str:
    canonical = canonical_json(data)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

---

## Error Handling Standards

### Error Categories

**Fatal Errors** (raise exception):
- File not found
- Invalid file_id format
- Registry corruption
- Lock acquisition timeout

**Recoverable Errors** (return safe default):
- Syntax errors in target file → `ParseResult(success=False)`
- Invalid AST → Empty component list
- Missing optional data → None/empty values

**Warnings** (log but continue):
- Ambiguous patterns
- Low confidence tags
- Performance degradation

### Logging Standards
```python
from GOVERNANCE.ssot.SSOT_System.SSOT_SYS_tools.observable_logger import ObservableLogger

logger = ObservableLogger(__name__, component_id="MAPP_PY_COMPONENT")
```

---

## Performance Requirements

### Per-File Analysis (Phase A)
- **Target**: <2 seconds per file
- **Timeout**: 5 seconds max
- **Memory**: <100MB per file

### Batch Operations (Phase C)
- **Target**: <10 minutes for 1,000 files
- **Candidate selection**: O(N) bucketing
- **Similarity comparison**: O(K) where K << N²

### Registry Writes
- **Target**: <500ms per write
- **Lock timeout**: 30 seconds
- **Atomic operation**: Yes (temp + rename)

---

## Testing Requirements

### Unit Tests
- **Coverage**: >85%
- **Framework**: pytest
- **Isolation**: Mock external dependencies

### Integration Tests
- **Test corpus**: 50+ Python files of varying complexity
- **Expected output**: Known-good analysis results
- **Performance benchmarks**: Within target times

### Compatibility Tests
- **Python versions**: 3.9, 3.10, 3.11
- **Platforms**: Windows, Linux, macOS
- **Edge cases**: Invalid syntax, huge files, edge encodings

---

## Dependencies Summary

### Stdlib (All Scripts)
```
ast, hashlib, json, pathlib, re, sys, io, os, typing
```

### External (Optional, Phase B)
```
pytest >= 7.4.0
pytest-cov >= 4.1.0
ruff >= 0.1.0
mypy >= 1.7.0
radon >= 6.0.0
```

### External (Optional, Phase C)
```
scikit-learn >= 1.3.0  (for semantic similarity)
numpy >= 1.24.0  (for embeddings)
```

---

## Deployment Checklist

- [ ] Python 3.9+ installed
- [ ] All stdlib dependencies available
- [ ] External tools installed (if using Phase B)
- [ ] Registry schema updated with py_* columns
- [ ] Column Dictionary updated
- [ ] Write policies defined
- [ ] Lock directory writable
- [ ] Evidence directory created (`.runs/`)
- [ ] Backup directory configured
- [ ] Logging configured
- [ ] Test suite passing

---

**References**:
- Column mapping: `COLUMN_TO_SCRIPT_MAPPING.json` v2.1
- Integration spec: `DOC-INTEGRATION-MAPP-PY-REGISTRY-001__Registry_Integration.md`
- Corrections: `CORRECTIONS_APPLIED_V2.md`
