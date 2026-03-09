#!/usr/bin/env python3
"""
Comprehensive Pipeline Runner (Week 3 - Component 4/6)

Purpose:
  - Run complete pipeline end-to-end
  - Orchestrate all phases in sequence
  - Generate final consolidated registry
  - Validate and report results

Usage:
  python P_01999000042260305017_pipeline_runner.py --input-dir PATH --output-registry PATH
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from P_01999000042260305014_intake_orchestrator import FileIntakeOrchestrator
from P_01999000042260305002_phase_a_transformer import PhaseATransformer
from P_01999000042260305003_run_metadata_collector import RunMetadataCollector
from P_01999000042260305004_patch_generator import PatchGenerator
import uuid

class PipelineRunner:
    def __init__(self, scripts_dir: Path, output_dir: Path, registry_path: Path = None):
        self.scripts_dir = scripts_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = str(uuid.uuid4())[:8]
        self.orchestrator = FileIntakeOrchestrator(scripts_dir)
        self.transformer = PhaseATransformer()
        self.metadata_collector = RunMetadataCollector(output_dir / ".state/runs")
        self.files_processed = []
        self.registry_path = registry_path
        self._file_id_index = self._build_file_id_index(registry_path) if registry_path else {}
    
    def _build_file_id_index(self, registry_path):
        """Build filename → file_id index from registry."""
        if not registry_path or not Path(registry_path).exists():
            return {}
        with open(registry_path, encoding='utf-8') as f:
            reg = json.load(f)
        return {Path(r["relative_path"]).name: r["file_id"]
                for r in reg.get("files", [])
                if r.get("file_id") and r.get("relative_path")}
        
    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single file through pipeline."""
        # Run analysis
        analysis = self.orchestrator.orchestrate(file_path)
        
        # Transform
        transformed = self.transformer.transform_phase_a_output(analysis)
        
        return {
            "file_path": str(file_path),
            "analysis": analysis,
            "transformed": transformed
        }
    
    def run_pipeline(self, input_files: List[Path]) -> Dict[str, Any]:
        """Run pipeline on multiple files."""
        self.metadata_collector.start_run(self.run_id)
        
        print(f"Pipeline run: {self.run_id}")
        print(f"Processing {len(input_files)} files...")
        
        for file_path in input_files:
            try:
                result = self.process_file(file_path)
                self.files_processed.append(result)
                
                # Stage for patch generation
                transformed = result.get("transformed", {})
                file_name = Path(file_path).name
                file_id = self._file_id_index.get(file_name)
                if file_id and transformed:
                    staging_dir = self.output_dir / "staging"
                    staging_dir.mkdir(exist_ok=True)
                    staging_file = staging_dir / f"{file_name}.json"
                    with open(staging_file, 'w', encoding='utf-8') as sf:
                        json.dump({"file_id": file_id, "data": transformed["data"]}, sf, indent=2)
                else:
                    # Log skip — file not in registry or transform produced no data
                    result["file_id_lookup"] = "not_found" if not file_id else "no_data"
                
                self.metadata_collector.record_script(
                    self.run_id,
                    "intake_orchestrator",
                    str(file_path),
                    "success",
                    0
                )
                
                print(f"  ✓ {file_path.name}")
            
            except Exception as e:
                print(f"  ✗ {file_path.name}: {e}")
                self.metadata_collector.record_script(
                    self.run_id,
                    "intake_orchestrator",
                    str(file_path),
                    "error",
                    1
                )
        
        self.metadata_collector.finish_run(self.run_id)
        
        # Generate patches from staged output (registry NOT modified)
        staging_dir = self.output_dir / "staging"
        if staging_dir.exists() and self.registry_path:
            patches_file = self.output_dir / "registry_patches.json"
            patch_script = Path(__file__).parent / "P_01999000042260305004_patch_generator.py"
            subprocess.run(
                [sys.executable, str(patch_script),
                 "--mode", "generate",
                 "--analysis-dir", str(staging_dir),
                 "--registry", str(self.registry_path),
                 "--patches-file", str(patches_file)],
                check=False
            )
            print(f"Patches written to: {patches_file}")
            print(f"To apply: python P_01999000042260305004_patch_generator.py --mode apply "
                  f"--patches-file {patches_file}")
        
        return {
            "run_id": self.run_id,
            "total_files": len(input_files),
            "successful": len(self.files_processed),
            "results": self.files_processed
        }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline Runner')
    parser.add_argument('--input-dir', required=True, help='Input directory')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--scripts-dir', default='.', help='Scripts directory')
    parser.add_argument('--pattern', default='*.py', help='File pattern')
    parser.add_argument('--registry', default=None,
        help='Path to registry JSON for file_id lookup and patch generation')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    scripts_dir = Path(args.scripts_dir)
    
    # Find files
    files = list(input_dir.glob(args.pattern))
    
    if not files:
        print(f"No files found matching {args.pattern} in {input_dir}")
        sys.exit(1)
    
    # Run pipeline
    runner = PipelineRunner(scripts_dir, output_dir, Path(args.registry) if args.registry else None)
    results = runner.run_pipeline(files)
    
    # Save results
    results_file = output_dir / f"pipeline_results_{runner.run_id}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Pipeline complete")
    print(f"   Processed: {results['successful']}/{results['total_files']}")
    print(f"   Results: {results_file}")

if __name__ == "__main__":
    main()
