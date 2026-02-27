#!/usr/bin/env python3
"""
Registry Integration Pipeline - Main Orchestrator
DOC-SCRIPT-XXXX-PIPELINE

Produces: 
  - py_analysis_run_id
  - py_analyzed_at_utc
  - py_toolchain_id
  - py_tool_versions
  - py_analysis_success
  - py_component_artifact_path

Main orchestrator for mapp_py analysis pipeline. Coordinates all Phase A/B/C
analyzers and integrates results into SSOT registry.
"""
import json
import sys
import hashlib
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from script_name_resolver import resolve_script_path
except ImportError:
    def resolve_script_path(name: str, base_dir: Path) -> Path:
        return base_dir / name


class RegistryIntegrationPipeline:
    """Main orchestrator for Python file analysis pipeline."""
    
    def __init__(self, mapp_py_dir: Path, registry_path: Path, evidence_root: Optional[Path] = None):
        self.mapp_py_dir = mapp_py_dir
        self.registry_path = registry_path
        self.evidence_root = evidence_root or Path('.state/evidence/mapp_py')
        self.run_id = self.generate_run_id()
        self.toolchain_id = "MAPP_PY_V1"
        self.tool_versions = self.collect_tool_versions()
        self.analyzed_at = datetime.utcnow().isoformat() + 'Z'
    
    def generate_run_id(self) -> str:
        """
        Generate unique run ID.
        Format: RUN-YYYYMMDD-HHMMSS-{6-hex}
        """
        now = datetime.utcnow()
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        random_hex = hashlib.sha256(str(now.timestamp()).encode()).hexdigest()[:6]
        return f"RUN-{date_part}-{time_part}-{random_hex}"
    
    def collect_tool_versions(self) -> dict:
        """Collect tool versions for reproducibility."""
        versions = {
            'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform,
        }
        
        # Try to get optional tool versions
        optional_tools = ['pytest', 'ruff', 'mypy', 'radon', 'black']
        for tool in optional_tools:
            try:
                result = subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    versions[tool] = result.stdout.strip().split('\n')[0]
                else:
                    versions[tool] = None
            except (FileNotFoundError, subprocess.TimeoutExpired):
                versions[tool] = None
        
        return versions
    
    def analyze_file(self, file_path: Path, phase: str = 'A') -> dict:
        """
        Run analyzers on a single file.
        
        Args:
            file_path: Path to Python file to analyze
            phase: 'A' (static only), 'B' (+ quality), 'C' (+ similarity)
            
        Returns:
            Dict with all py_* columns populated
        """
        results = {
            'file_path': str(file_path),
            'py_analysis_run_id': self.run_id,
            'py_analyzed_at_utc': self.analyzed_at,
            'py_toolchain_id': self.toolchain_id,
            'py_tool_versions': self.tool_versions,
            'py_analysis_success': True,
            'errors': []
        }
        
        # Phase A: Core static analysis (always run)
        phase_a_scripts = [
            'text_normalizer.py',
            'component_extractor.py',
            'component_id_generator.py',
            'dependency_analyzer.py',
            'io_surface_analyzer.py',
            'deliverable_analyzer.py',
            'capability_tagger.py',
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            for script_name in phase_a_scripts:
                try:
                    script_path = resolve_script_path(script_name, self.mapp_py_dir)
                    
                    if not script_path.exists():
                        results['errors'].append(f"{script_name} not found at {script_path}")
                        continue
                    
                    output_file = tmp_path / f"{script_name}.output.json"
                    
                    # Run script
                    result = subprocess.run(
                        [sys.executable, str(script_path), str(file_path), '--json', str(output_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    # Parse output
                    if output_file.exists():
                        with open(output_file) as f:
                            script_output = json.load(f)
                            results.update(script_output)
                    elif result.returncode == 0 and result.stdout:
                        # Try parsing stdout as JSON
                        try:
                            script_output = json.loads(result.stdout)
                            results.update(script_output)
                        except json.JSONDecodeError:
                            results['errors'].append(f"{script_name} output not valid JSON")
                    else:
                        results['errors'].append(f"{script_name} failed: {result.stderr[:200]}")
                        
                except FileNotFoundError as e:
                    results['errors'].append(f"{script_name} not found: {str(e)}")
                except Exception as e:
                    results['errors'].append(f"{script_name} error: {str(e)}")
                    results['py_analysis_success'] = False
            
            # Phase B: Quality metrics (optional)
            if phase in ('B', 'C'):
                phase_b_scripts = [
                    'test_runner.py',
                    'linter_runner.py',
                    'complexity_analyzer.py',
                    'quality_scorer.py',
                ]
                
                for script_name in phase_b_scripts:
                    try:
                        script_path = resolve_script_path(script_name, self.mapp_py_dir)
                        if script_path.exists():
                            # Similar execution pattern
                            pass  # Implement if needed
                    except FileNotFoundError:
                        # Phase B/C tools are optional
                        pass
            
            # Write evidence bundle
            evidence_path = self.write_artifacts(self.run_id, results, tmp_path)
            results['py_component_artifact_path'] = str(evidence_path)
        
        # Set success flag
        if results['errors']:
            results['py_analysis_success'] = False
        
        return results
    
    def write_artifacts(self, run_id: str, evidence: dict, tmp_dir: Path) -> Path:
        """
        Write evidence bundle and return path.
        
        Args:
            run_id: Analysis run ID
            evidence: Complete evidence dict
            tmp_dir: Temporary directory with intermediate outputs
            
        Returns:
            Path to evidence file
        """
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped evidence file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        evidence_file = self.evidence_root / f"analysis_{run_id}_{timestamp}.json"
        
        # Add metadata
        evidence_bundle = {
            'run_id': run_id,
            'analyzed_at_utc': self.analyzed_at,
            'toolchain_id': self.toolchain_id,
            'tool_versions': self.tool_versions,
            'results': evidence,
            'evidence_hash': None  # Computed after serialization
        }
        
        # Compute evidence hash
        evidence_json = json.dumps(evidence_bundle, sort_keys=True, separators=(',', ':'))
        evidence_hash = hashlib.sha256(evidence_json.encode('utf-8')).hexdigest()
        evidence_bundle['evidence_hash'] = evidence_hash
        
        # Write to file
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence_bundle, f, indent=2, sort_keys=True)
        
        return evidence_file
    
    def update_registry(self, analysis_results: List[dict], dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply results to SSOT registry via RFC-6902 patches.
        
        Args:
            analysis_results: List of analysis result dicts
            dry_run: If True, generate patches but don't apply
            
        Returns:
            Dict with patch statistics and paths
        """
        patches = []
        
        # Load registry
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        files = registry.get('files', [])
        file_index = {f.get('file_id'): idx for idx, f in enumerate(files) if f.get('file_id')}
        
        # Generate patches for each result
        for result in analysis_results:
            file_id = result.get('file_id')
            if not file_id or file_id not in file_index:
                continue
            
            idx = file_index[file_id]
            
            # Create patches for py_* columns
            for key, value in result.items():
                if key.startswith('py_') and value is not None:
                    patches.append({
                        'op': 'add',
                        'path': f'/files/{idx}/{key}',
                        'value': value
                    })
        
        # Write patch file
        patch_file = self.evidence_root / f"patches_{self.run_id}.json"
        with open(patch_file, 'w', encoding='utf-8') as f:
            json.dump(patches, f, indent=2)
        
        patch_summary = {
            'patches_generated': len(patches),
            'patch_file': str(patch_file),
            'dry_run': dry_run,
            'applied': False
        }
        
        if not dry_run:
            # Apply patches (requires jsonpatch library or manual application)
            # For now, just log what would be applied
            print(f"Would apply {len(patches)} patches to registry")
            patch_summary['applied'] = False  # Set to True after actual application
        
        return patch_summary
    
    def analyze_batch(self, file_paths: List[Path], phase: str = 'A') -> List[dict]:
        """
        Analyze multiple files.
        
        Args:
            file_paths: List of Python file paths
            phase: Analysis phase ('A', 'B', or 'C')
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path in file_paths:
            print(f"Analyzing: {file_path}", file=sys.stderr)
            result = self.analyze_file(file_path, phase)
            results.append(result)
        return results


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Registry Integration Pipeline - mapp_py Orchestrator'
    )
    parser.add_argument('--file', type=Path, help='Single file to analyze')
    parser.add_argument('--registry', type=Path, required=True, help='Registry JSON path')
    parser.add_argument('--batch', action='store_true', help='Analyze all Python files in registry')
    parser.add_argument('--phase', choices=['A', 'B', 'C'], default='A', 
                       help='Analysis phase (A=static, B=+quality, C=+similarity)')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, no updates')
    parser.add_argument('--output', type=Path, help='Output JSON file')
    parser.add_argument('--evidence-root', type=Path, help='Evidence output directory')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    mapp_py_dir = Path(__file__).parent
    evidence_root = args.evidence_root or Path('.state/evidence/mapp_py')
    
    pipeline = RegistryIntegrationPipeline(
        mapp_py_dir=mapp_py_dir,
        registry_path=args.registry,
        evidence_root=evidence_root
    )
    
    print(f"Pipeline initialized: {pipeline.run_id}", file=sys.stderr)
    print(f"Toolchain: {pipeline.toolchain_id}", file=sys.stderr)
    print(f"Phase: {args.phase}", file=sys.stderr)
    
    # Execute analysis
    if args.file:
        # Single file mode
        result = pipeline.analyze_file(args.file, args.phase)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, sort_keys=True)
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        
        # Exit code based on success
        sys.exit(0 if result['py_analysis_success'] else 1)
    
    elif args.batch:
        # Batch mode - analyze all Python files in registry
        with open(args.registry, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        py_files = [
            Path(f['absolute_path']) for f in registry.get('files', [])
            if f.get('extension') == '.py' and Path(f.get('absolute_path', '')).exists()
        ]
        
        print(f"Found {len(py_files)} Python files to analyze", file=sys.stderr)
        
        results = pipeline.analyze_batch(py_files, args.phase)
        
        if not args.dry_run:
            patch_summary = pipeline.update_registry(results, dry_run=False)
            print(f"\nPatch Summary:", file=sys.stderr)
            print(json.dumps(patch_summary, indent=2), file=sys.stderr)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, sort_keys=True)
        
        # Summary
        success_count = sum(1 for r in results if r['py_analysis_success'])
        print(f"\nCompleted: {success_count}/{len(results)} successful", file=sys.stderr)
        
        sys.exit(0 if success_count == len(results) else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
