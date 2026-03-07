#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0990
"""Debug why analyzers aren't finding edges."""

import sys
from pathlib import Path

# Add to path
.parent))

from core.index_builder import SimpleDocIDRegistry
from analyzers import MarkdownLinkAnalyzer, YAMLReferenceAnalyzer, TestLinkAnalyzer
from core.confidence_engine import ConfidenceEngine

# Initialize
registry = SimpleDocIDRegistry()
confidence = ConfidenceEngine()

# Test each analyzer
print("=== Analyzer Tests ===\n")

# 1. Markdown
print("1. MarkdownLinkAnalyzer:")
md_analyzer = MarkdownLinkAnalyzer(registry, confidence)
print(f"   can_analyze(Path('test.md'), 'md'): {md_analyzer.can_analyze(Path('test.md'), 'md')}")
print(f"   Analyzer ID: {md_analyzer.analyzer_id}")

# Count markdown files
md_files = [d for d in registry.data if d.get('file_type') == 'md' and d.get('status') == 'registered']
print(f"   Markdown files in registry: {len(md_files)}")
if md_files:
    print(f"   Sample: {md_files[0]['path']}")

# 2. YAML
print("\n2. YAMLReferenceAnalyzer:")
yaml_analyzer = YAMLReferenceAnalyzer(registry, confidence)
print(f"   can_analyze(Path('test.yaml'), 'yaml'): {yaml_analyzer.can_analyze(Path('test.yaml'), 'yaml')}")
print(f"   Analyzer ID: {yaml_analyzer.analyzer_id}")

# 3. Test
print("\n3. TestLinkAnalyzer:")
test_analyzer = TestLinkAnalyzer(registry, confidence)
print(f"   can_analyze(Path('test_foo.py'), 'py'): {test_analyzer.can_analyze(Path('tests/test_foo.py'), 'py')}")
print(f"   Analyzer ID: {test_analyzer.analyzer_id}")

# Count test files
py_files = [d for d in registry.data if d.get('file_type') == 'py' and 'test' in d.get('path', '').lower()]
print(f"   Python test files in registry: {len(py_files)}")
if py_files:
    print(f"   Sample: {py_files[0]['path']}")
