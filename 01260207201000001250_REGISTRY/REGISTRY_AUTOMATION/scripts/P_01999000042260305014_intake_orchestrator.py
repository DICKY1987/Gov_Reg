#!/usr/bin/env python3
"""
File Intake Orchestrator (Week 3 - Component 1/6)

Purpose:
  - Orchestrate file intake and analysis pipeline
  - Call Phase A, B, C analyzers in sequence
  - Collect all outputs into unified result
  - Handle errors and retries

Usage:
  python P_01999000042260305014_intake_orchestrator.py --file PATH --output PATH
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time

class FileIntakeOrchestrator:
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir
        self.results = {}
        self.errors = []
    
    def run_analyzer(self, script_name: str, file_path: Path, 
                    extra_args: list = None) -> Optional[Dict[str, Any]]:
        """Run an analyzer script and capture JSON output."""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            self.errors.append(f"Script not found: {script_name}")
            return None
        
        args = ["python", str(script_path), str(file_path)]
        if extra_args:
            args.extend(extra_args)
        
        try:
            start_time = time.time()
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=60
            )
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                # Parse JSON output
                try:
                    output = json.loads(result.stdout)
                    output["_execution_time_ms"] = duration_ms
                    return output
                except json.JSONDecodeError:
                    self.errors.append(f"{script_name}: Invalid JSON output")
                    return None
            else:
                self.errors.append(f"{script_name}: Exit code {result.returncode}")
                return None
        
        except subprocess.TimeoutExpired:
            self.errors.append(f"{script_name}: Timeout (60s)")
            return None
        except Exception as e:
            self.errors.append(f"{script_name}: {str(e)}")
            return None
    
    def run_phase_a(self, file_path: Path) -> Dict[str, Any]:
        """Run Phase A analyzers."""
        phase_a = {}
        
        # Text normalization
        result = self.run_analyzer("P_01260202173939000060_text_normalizer.py", file_path, ["--json", "-"])
        if result:
            phase_a.update(result)
        
        # Component extraction
        result = self.run_analyzer("P_01260202173939000061_component_extractor.py", file_path, ["--json", "-"])
        if result:
            phase_a.update(result)
        
        # Dependencies
        result = self.run_analyzer("P_01260202173939000063_dependency_analyzer.py", file_path, ["--json", "-"])
        if result:
            phase_a.update(result)
        
        # Capabilities
        result = self.run_analyzer("P_01260202173939000076_capability_detector.py", file_path, ["--json", "-"])
        if result:
            phase_a.update(result)
        
        return phase_a
    
    def run_phase_b(self, file_path: Path, phase_a_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Phase B analyzers (complexity, tests, lint)."""
        phase_b = {}
        
        # Complexity
        result = self.run_analyzer("P_01260202173939000071_complexity_visitor.py", file_path, ["--json", "-"])
        if result:
            phase_b.update(result)
        
        # Tests (if test file)
        if "test" in str(file_path).lower():
            result = self.run_analyzer("P_01260202173939000069_analyze_tests.py", file_path, ["--json", "-"])
            if result:
                phase_b.update(result)
        
        # Lint
        result = self.run_analyzer("P_01260202173939000070_run_pylint_on_file.py", file_path, ["--json", "-"])
        if result:
            phase_b.update(result)
        
        return phase_b
    
    def run_phase_c(self, file_path: Path, prior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Phase C quality scoring."""
        phase_c = {}
        
        # Quality scorer (requires prior phases)
        # For now, skip as it needs integrated metrics
        
        return phase_c
    
    def orchestrate(self, file_path: Path) -> Dict[str, Any]:
        """Orchestrate complete analysis pipeline."""
        print(f"Analyzing: {file_path}")
        
        # Phase A
        print("  Running Phase A...")
        phase_a = self.run_phase_a(file_path)
        self.results["phase_a"] = phase_a
        
        # Phase B
        print("  Running Phase B...")
        phase_b = self.run_phase_b(file_path, phase_a)
        self.results["phase_b"] = phase_b
        
        # Phase C
        print("  Running Phase C...")
        phase_c = self.run_phase_c(file_path, {**phase_a, **phase_b})
        self.results["phase_c"] = phase_c
        
        # Combine
        combined = {
            **phase_a,
            **phase_b,
            **phase_c,
            "_metadata": {
                "file_path": str(file_path),
                "analyzed_at": datetime.utcnow().isoformat() + "Z",
                "orchestrator": "P_01999000042260305014_intake_orchestrator.py",
                "errors": self.errors
            }
        }
        
        return combined

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='File Intake Orchestrator')
    parser.add_argument('--file', required=True, help='File to analyze')
    parser.add_argument('--output', required=True, help='Output JSON')
    parser.add_argument('--scripts-dir', 
                       default='.',
                       help='Directory with analyzer scripts')
    args = parser.parse_args()
    
    file_path = Path(args.file)
    output_path = Path(args.output)
    scripts_dir = Path(args.scripts_dir)
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    orchestrator = FileIntakeOrchestrator(scripts_dir)
    result = orchestrator.orchestrate(file_path)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    if orchestrator.errors:
        print(f"⚠️  {len(orchestrator.errors)} errors during analysis")
        for err in orchestrator.errors:
            print(f"  • {err}")
    
    print(f"✅ Analysis complete: {output_path}")

if __name__ == "__main__":
    main()
