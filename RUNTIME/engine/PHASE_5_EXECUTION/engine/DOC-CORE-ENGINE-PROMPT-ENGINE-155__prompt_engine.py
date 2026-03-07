# DOC_LINK: DOC-CORE-ENGINE-PROMPT-ENGINE-155
"""
Prompt Engine V1.1 for Pipeline Plus
WORKSTREAM_V1.1 template rendering with classification inference
"""

# DOC_ID: DOC-CORE-ENGINE-PROMPT-ENGINE-155
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass
class Classification:
    """Workstream classification"""

    complexity: str  # simple|moderate|complex|enterprise
    quality: str  # standard|production
    domain: str  # code|docs|tests|analysis
    operation: str  # refactor|bugfix|feature|analysis_only


@dataclass
class PromptContext:
    """Context for prompt rendering"""

    target_app: str  # aider|codex|claude|universal
    repo_path: str
    worktree_path: str
    additional_context: Dict[str, Any] = None


class PromptEngine:
    """
    Enhanced prompt generation with WORKSTREAM_V1.1 templates
    """

    def __init__(self, template_dir: str = "aider/templates/prompts"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_v11(self, bundle: Dict[str, Any], context: PromptContext) -> str:
        """
        Render WORKSTREAM_V1.1 prompt from bundle

        Args:
            bundle: Workstream bundle dictionary
            context: Prompt rendering context

        Returns:
            Rendered prompt as ASCII-only string
        """
        # 1. Infer classification if not explicit
        classification = self._infer_classification(bundle)

        # 2. Infer role/persona
        role = self._infer_role(classification)

        # 3. Select template variant
        template_name = self._select_template(context.target_app)

        # 4. Prepare template variables
        template_vars = {
            "bundle": bundle,
            "classification": classification,
            "role": role,
            "context": context,
            "ws_id": bundle.get("id", "unknown"),
            "openspec_change": bundle.get("openspec_change", ""),
            "ccpm_issue": bundle.get("ccpm_issue", ""),
            "gate": bundle.get("gate", 1),
            "files_scope": bundle.get("files_scope", []),
            "files_create": bundle.get("files_create", []),
            "tasks": bundle.get("tasks", []),
            "acceptance_tests": bundle.get("acceptance_tests", []),
            "tool": bundle.get("tool", "aider"),
            "metadata": bundle.get("metadata", {}),
        }

        # 5. Render template
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**template_vars)

            # Ensure ASCII-only
            return rendered.encode("ascii", errors="replace").decode("ascii")
        except Exception:
            # Fallback to basic rendering if template not found
            return self._render_fallback(bundle, context, classification, role)

    def _infer_classification(self, bundle: Dict[str, Any]) -> Classification:
        """
        Infer classification from bundle metadata

        Args:
            bundle: Workstream bundle

        Returns:
            Classification object
        """
        # Check if classification is explicit in metadata
        metadata = bundle.get("metadata", {})
        if "classification" in metadata:
            c = metadata["classification"]
            return Classification(
                complexity=c.get("complexity", "moderate"),
                quality=c.get("quality", "standard"),
                domain=c.get("domain", "code"),
                operation=c.get("operation", "refactor"),
            )

        # Infer from bundle properties
        file_count = len(bundle.get("files_scope", []))
        task_count = len(bundle.get("tasks", []))

        # Infer complexity
        if file_count <= 2 and task_count <= 3:
            complexity = "simple"
        elif file_count <= 5 and task_count <= 5:
            complexity = "moderate"
        elif file_count <= 10:
            complexity = "complex"
        else:
            complexity = "enterprise"

        # Infer quality
        quality = "production" if bundle.get("gate", 1) >= 2 else "standard"

        # Infer domain from file extensions
        files = bundle.get("files_scope", [])
        if any(".md" in f for f in files):
            domain = "docs"
        elif any("test" in f.lower() for f in files):
            domain = "tests"
        else:
            domain = "code"

        # Infer operation from tasks
        tasks_text = " ".join(bundle.get("tasks", [])).lower()
        if "refactor" in tasks_text:
            operation = "refactor"
        elif "fix" in tasks_text or "bug" in tasks_text:
            operation = "bugfix"
        elif "analyze" in tasks_text or "review" in tasks_text:
            operation = "analysis_only"
        else:
            operation = "feature"

        return Classification(
            complexity=complexity, quality=quality, domain=domain, operation=operation
        )

    def _infer_role(self, classification: Classification) -> str:
        """
        Infer role/persona from classification

        Args:
            classification: Classification object

        Returns:
            Role/persona string
        """
        base_role = {
            "code": "Software Engineer",
            "docs": "Technical Writer",
            "tests": "QA Engineer",
            "analysis": "Code Reviewer",
        }.get(classification.domain, "Software Engineer")

        experience = {
            "simple": "",
            "moderate": "experienced",
            "complex": "Senior",
            "enterprise": "Principal",
        }.get(classification.complexity, "")

        specialization = {
            "refactor": "specializing in code refactoring",
            "bugfix": "specializing in debugging",
            "feature": "specializing in feature development",
            "analysis_only": "focused on code analysis",
        }.get(classification.operation, "")

        # Combine parts
        parts = [p for p in [experience, base_role, specialization] if p]
        return " ".join(parts)

    def _select_template(self, target_app: str) -> str:
        """
        Select template variant based on target app

        Args:
            target_app: Target application (aider|codex|claude|universal)

        Returns:
            Template filename
        """
        template_map = {
            "aider": "workstream_v1.1_aider.txt.j2",
            "codex": "workstream_v1.1_codex.txt.j2",
            "claude": "workstream_v1.1_universal.txt.j2",  # Use universal for claude
            "universal": "workstream_v1.1_universal.txt.j2",
        }

        return template_map.get(target_app.lower(), "workstream_v1.1_universal.txt.j2")

    def _render_fallback(
        self,
        bundle: Dict[str, Any],
        context: PromptContext,
        classification: Classification,
        role: str,
    ) -> str:
        """
        Fallback rendering when templates are not available

        Args:
            bundle: Workstream bundle
            context: Prompt context
            classification: Inferred classification
            role: Inferred role

        Returns:
            Basic rendered prompt
        """
        lines = [
            "=" * 80,
            f"WORKSTREAM: {bundle.get('id', 'unknown')}",
            f"CLASSIFICATION: {classification.complexity} | {classification.quality} | {classification.domain} | {classification.operation}",
            f"ROLE: {role}",
            "=" * 80,
            "",
            "OBJECTIVE:",
            f"OpenSpec Change: {bundle.get('openspec_change', 'N/A')}",
            f"CCPM Issue: {bundle.get('ccpm_issue', 'N/A')}",
            f"Gate: {bundle.get('gate', 1)}",
            "",
            "FILE SCOPE:",
        ]

        for f in bundle.get("files_scope", []):
            lines.append(f"  - {f}")

        if bundle.get("files_create"):
            lines.append("")
            lines.append("FILES TO CREATE:")
            for f in bundle.get("files_create", []):
                lines.append(f"  - {f}")

        lines.append("")
        lines.append("TASKS:")
        for i, task in enumerate(bundle.get("tasks", []), 1):
            lines.append(f"{i}. {task}")

        if bundle.get("acceptance_tests"):
            lines.append("")
            lines.append("ACCEPTANCE TESTS:")
            for test in bundle.get("acceptance_tests", []):
                lines.append(f"  - {test}")

        lines.append("")
        lines.append("CONSTRAINTS:")
        lines.append("- Modify only files within the declared scope")
        lines.append("- Keep changes minimal and focused")
        lines.append("- Ensure all tests pass")

        lines.append("")
        lines.append("=" * 80)

        result = "\n".join(lines)
        # Ensure ASCII-only
        return result.encode("ascii", errors="replace").decode("ascii")
