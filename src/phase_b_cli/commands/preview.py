"""B3: preview - Generate human-readable execution plan preview"""

from pathlib import Path
from datetime import datetime

from .base import BaseCommand


class PreviewCommand(BaseCommand):
    """Generate human-readable execution preview"""
    
    def execute(self) -> int:
        """Execute preview generation"""
        self.logger.info(f"Generating preview for Phase B run: {self.phase_b_run_id}")
        
        # Load execution plan
        compile_dir = self.phase_b_dir / "compile"
        execution_plan_path = compile_dir / "execution_plan.json"
        
        if not execution_plan_path.exists():
            self.logger.error("Execution plan not found. Run 'compile' command first.")
            return 10
        
        execution_plan = self.load_json(execution_plan_path)
        manifest = self.load_json(compile_dir / "execution_manifest.json")
        
        # Determine output path
        preview_dir = self.phase_b_dir / "preview"
        if self.args.out_path:
            output_path = self.args.out_path
        else:
            if self.args.output_format == "markdown":
                output_path = preview_dir / "execution_preview.md"
            elif self.args.output_format == "mermaid":
                output_path = preview_dir / "execution_graph.mermaid"
            else:
                output_path = preview_dir / "execution_preview.json"
        
        # Generate preview
        if self.args.output_format == "markdown":
            content = self._generate_markdown(execution_plan, manifest, compile_dir)
        elif self.args.output_format == "mermaid":
            content = self._generate_mermaid(execution_plan, compile_dir)
        else:
            content = self._generate_json(execution_plan, manifest, compile_dir)
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
        self.logger.info(f"Preview written to: {output_path}")
        print(f"✓ Preview: {output_path}")
        
        return 0
    
    def _generate_markdown(self, execution_plan, manifest, compile_dir) -> str:
        """Generate markdown preview"""
        lines = [
            "# Execution Plan Preview",
            "",
            f"**Plan ID:** {execution_plan['plan_id']}",
            f"**Phase A Run:** {execution_plan['phase_a_run_id']}",
            f"**Compiled:** {execution_plan['metadata']['compiled_at']}",
            f"**Total Tasks:** {execution_plan['metadata']['total_tasks']}",
            f"**Estimated Duration:** {execution_plan['metadata']['estimated_duration_seconds']}s",
            "",
            "## Task Execution Order",
            ""
        ]
        
        for i, task_id in enumerate(execution_plan['task_order'], 1):
            # Load task spec
            safe_id = task_id.replace("-", "_").replace(".", "_")
            task_spec_path = compile_dir / "task_specs" / f"task_spec_{safe_id}.json"
            
            if task_spec_path.exists():
                task_spec = self.load_json(task_spec_path)
                lines.append(f"### {i}. {task_id}")
                lines.append(f"**Summary:** {task_spec.get('summary', 'N/A')}")
                lines.append(f"**Dependencies:** {', '.join(task_spec.get('depends_on', [])) or 'None'}")
                lines.append(f"**Write Operations:** {len(task_spec.get('write_operations', []))}")
                lines.append(f"**Acceptance Tests:** {len(task_spec.get('acceptance_tests', []))}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_mermaid(self, execution_plan, compile_dir) -> str:
        """Generate mermaid graph"""
        lines = [
            "graph TD",
            "    START[Start] --> TASK_0",
        ]
        
        task_order = execution_plan['task_order']
        for i, task_id in enumerate(task_order):
            safe_id = f"TASK_{i}"
            next_safe_id = f"TASK_{i+1}" if i < len(task_order) - 1 else "END"
            
            lines.append(f"    {safe_id}[{task_id}] --> {next_safe_id}")
        
        lines.append("    END[Complete]")
        
        return "\n".join(lines)
    
    def _generate_json(self, execution_plan, manifest, compile_dir) -> str:
        """Generate JSON preview"""
        import json
        
        preview = {
            "plan_id": execution_plan["plan_id"],
            "phase_a_run_id": execution_plan["phase_a_run_id"],
            "metadata": execution_plan["metadata"],
            "task_order": execution_plan["task_order"],
            "total_tasks": len(execution_plan["task_order"])
        }
        
        return json.dumps(preview, indent=2)
