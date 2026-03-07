# DOC_LINK: DOC-CORE-ANALYZERS-ARTIFACT-BUNDLE-ANALYZER-001
"""
Artifact Bundle Analyzer

Extracts semantic artifact dependency relationships from:
1. Pattern templates (*.pattern.yaml) - produces/depends_on declarations
2. DIR_MANIFEST.yaml files - ownership relationships
3. Phase plans (*.yml) - workstream dependencies
4. Convention-based rules - inferred relationships

This analyzer enables automatic population of the artifact DAG that describes
"to create artifact X, you must first create Y, Z, W" relationships.
"""
# DOC_ID: DOC-CORE-ANALYZERS-ARTIFACT-BUNDLE-ANALYZER-001

import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class ArtifactBundleAnalyzer(BaseAnalyzer):
    """
    Analyzes pattern templates, manifests, and phase plans to extract
    semantic artifact generation dependencies.

    This complements code-level analyzers (imports, references) by capturing
    higher-level "artifact bundle" relationships.
    """

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """
        Check if this analyzer can handle pattern/manifest files.

        Args:
            file_path: Path to the file
            file_type: File extension

        Returns:
            True if file is a pattern YAML, DIR_MANIFEST, or phase plan
        """
        filename = file_path.name.lower()

        # Pattern templates
        if file_type.lower() in ["yaml", "yml"]:
            if ".pattern." in filename:
                return True
            if filename == "dir_manifest.yaml":
                return True
            if filename.startswith("phase_plan_") or filename.startswith("ph-"):
                return True

        return False

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Analyze a pattern/manifest file and extract artifact relationships.

        Args:
            file_path: Absolute path to the file
            source_doc_id: Doc ID of the source file

        Returns:
            List of RelationshipEdge objects for artifact dependencies
        """
        edges = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                return edges

            # Analyze based on file type
            if ".pattern." in file_path.name.lower():
                edges.extend(self._analyze_pattern_template(file_path, source_doc_id, data))
            elif file_path.name.lower() == "dir_manifest.yaml":
                edges.extend(self._analyze_dir_manifest(file_path, source_doc_id, data))
            elif "phase_plan" in file_path.name.lower() or file_path.name.lower().startswith("ph-"):
                edges.extend(self._analyze_phase_plan(file_path, source_doc_id, data))

        except yaml.YAMLError:
            # Skip malformed YAML files
            pass
        except Exception:
            # Skip any other errors (file read issues, etc.)
            pass

        return edges

    def _analyze_pattern_template(
        self,
        file_path: Path,
        source_doc_id: str,
        data: Dict[str, Any]
    ) -> List[RelationshipEdge]:
        """
        Extract relationships from pattern template files.

        Patterns may declare:
        - outputs.files_created: List of artifacts this pattern produces
        - dependencies: Patterns or files this pattern depends on
        - execution_steps: Steps that reference other files/patterns
        """
        edges = []

        # Extract "produces" relationships from outputs
        if "outputs" in data:
            outputs = data["outputs"]

            # Check for files_created list
            if "files_created" in outputs and isinstance(outputs["files_created"], dict):
                file_spec = outputs["files_created"]
                if "type" in file_spec and file_spec["type"] == "array":
                    # Pattern declares it creates files, create "produces" edge
                    # Note: We can't resolve specific files without execution context,
                    # but we can mark the pattern as a producer
                    pass  # Future: could link to template files

        # Extract explicit dependencies
        if "dependencies" in data:
            deps = data["dependencies"]
            if isinstance(deps, list):
                for dep in deps:
                    if isinstance(dep, str):
                        # Try to resolve dependency path
                        target_doc_id = self._resolve_pattern_dependency(file_path, dep)
                        if target_doc_id:
                            edge = self._create_edge(
                                source_doc_id=source_doc_id,
                                target_doc_id=target_doc_id,
                                edge_type="depends_on",
                                evidence={
                                    "source_file": str(file_path),
                                    "declaration": f"dependencies: {dep}",
                                    "line_type": "pattern_dependency"
                                }
                            )
                            edges.append(edge)

        # Extract structural_decisions dependencies
        if "structural_decisions" in data:
            decisions = data["structural_decisions"]
            if isinstance(decisions, dict):
                # Look for references to other patterns or files
                for key, value in decisions.items():
                    if isinstance(value, str) and ("pattern:" in value or "file:" in value):
                        # Extract referenced artifact
                        target = value.split(":", 1)[1].strip() if ":" in value else value
                        target_doc_id = self._resolve_pattern_dependency(file_path, target)
                        if target_doc_id:
                            edge = self._create_edge(
                                source_doc_id=source_doc_id,
                                target_doc_id=target_doc_id,
                                edge_type="depends_on",
                                evidence={
                                    "source_file": str(file_path),
                                    "declaration": f"structural_decisions.{key}: {value}",
                                    "line_type": "structural_decision"
                                }
                            )
                            edges.append(edge)

        return edges

    def _analyze_dir_manifest(
        self,
        file_path: Path,
        source_doc_id: str,
        data: Dict[str, Any]
    ) -> List[RelationshipEdge]:
        """
        Extract ownership relationships from DIR_MANIFEST.yaml files.

        Manifests declare:
        - contents: List of files owned by this directory
        - dependencies.required: Dependencies on other directories/modules
        """
        edges = []

        # Extract ownership relationships from contents
        if "contents" in data:
            contents = data["contents"]
            if isinstance(contents, list):
                for item in contents:
                    if isinstance(item, str):
                        # Resolve relative path to absolute
                        target_path = (file_path.parent / item).resolve()
                        target_doc_id = self.registry.lookup_by_path(str(target_path))

                        if target_doc_id:
                            edge = self._create_edge(
                                source_doc_id=source_doc_id,
                                target_doc_id=target_doc_id,
                                edge_type="owns",
                                evidence={
                                    "source_file": str(file_path),
                                    "target_file": item,
                                    "line_type": "manifest_contents"
                                }
                            )
                            edges.append(edge)

        # Extract dependency relationships
        if "dependencies" in data and "required" in data["dependencies"]:
            required = data["dependencies"]["required"]
            if isinstance(required, list):
                for dep in required:
                    if isinstance(dep, dict) and "path" in dep:
                        # Resolve relative path
                        dep_path = (file_path.parent / dep["path"]).resolve()
                        # Look for DIR_MANIFEST.yaml in target directory
                        target_manifest = dep_path / "DIR_MANIFEST.yaml"
                        target_doc_id = self.registry.lookup_by_path(str(target_manifest))

                        if target_doc_id:
                            edge = self._create_edge(
                                source_doc_id=source_doc_id,
                                target_doc_id=target_doc_id,
                                edge_type="depends_on",
                                evidence={
                                    "source_file": str(file_path),
                                    "target_path": dep["path"],
                                    "description": dep.get("description", ""),
                                    "line_type": "manifest_dependency"
                                }
                            )
                            edges.append(edge)

        return edges

    def _analyze_phase_plan(
        self,
        file_path: Path,
        source_doc_id: str,
        data: Dict[str, Any]
    ) -> List[RelationshipEdge]:
        """
        Extract workstream dependencies from phase plan files.

        Phase plans may declare:
        - workstreams: List of workstreams with dependencies
        - dependencies: Phase-level dependencies
        """
        edges = []

        # Extract workstream dependencies
        if "workstreams" in data:
            workstreams = data["workstreams"]
            if isinstance(workstreams, list):
                for ws in workstreams:
                    if isinstance(ws, dict) and "depends_on" in ws:
                        depends = ws["depends_on"]
                        if isinstance(depends, list):
                            for dep in depends:
                                # Try to resolve workstream ID to file
                                target_doc_id = self._resolve_workstream_dependency(file_path, dep)
                                if target_doc_id:
                                    edge = self._create_edge(
                                        source_doc_id=source_doc_id,
                                        target_doc_id=target_doc_id,
                                        edge_type="depends_on",
                                        evidence={
                                            "source_file": str(file_path),
                                            "workstream_id": ws.get("id", "unknown"),
                                            "depends_on": dep,
                                            "line_type": "workstream_dependency"
                                        }
                                    )
                                    edges.append(edge)

        # Extract phase-level dependencies
        if "dependencies" in data:
            deps = data["dependencies"]
            if isinstance(deps, list):
                for dep in deps:
                    if isinstance(dep, str):
                        target_doc_id = self._resolve_phase_dependency(file_path, dep)
                        if target_doc_id:
                            edge = self._create_edge(
                                source_doc_id=source_doc_id,
                                target_doc_id=target_doc_id,
                                edge_type="depends_on",
                                evidence={
                                    "source_file": str(file_path),
                                    "phase_dependency": dep,
                                    "line_type": "phase_dependency"
                                }
                            )
                            edges.append(edge)

        return edges

    def _resolve_pattern_dependency(self, source_path: Path, dep: str) -> Optional[str]:
        """Resolve a pattern dependency reference to a doc_id."""
        # Try relative to source file first
        candidate = (source_path.parent / dep).resolve()
        doc_id = self.registry.lookup_by_path(str(candidate))
        if doc_id:
            return doc_id

        # Try with .pattern.yaml extension
        if not dep.endswith(".pattern.yaml"):
            candidate_with_ext = (source_path.parent / f"{dep}.pattern.yaml").resolve()
            doc_id = self.registry.lookup_by_path(str(candidate_with_ext))
            if doc_id:
                return doc_id

        return None

    def _resolve_workstream_dependency(self, source_path: Path, workstream_id: str) -> Optional[str]:
        """Resolve a workstream ID to a doc_id."""
        # Try to find workstream file in library
        repo_root = source_path
        while repo_root.parent != repo_root:
            if (repo_root / ".git").exists():
                break
            repo_root = repo_root.parent

        # Look in WORKFLOWS/planning/PHASE_1_PLANNING/workstreams/library/
        ws_lib = repo_root / "WORKFLOWS" / "planning" / "PHASE_1_PLANNING" / "workstreams" / "library"
        if ws_lib.exists():
            # Search for workstream_id in JSON files
            for category_dir in ws_lib.iterdir():
                if category_dir.is_dir():
                    for ws_file in category_dir.glob("*.json"):
                        doc_id = self.registry.lookup_by_path(str(ws_file))
                        if doc_id:
                            # Could parse file to check if ID matches, but for now just check filename
                            if workstream_id.lower() in ws_file.name.lower():
                                return doc_id

        return None

    def _resolve_phase_dependency(self, source_path: Path, phase_ref: str) -> Optional[str]:
        """Resolve a phase reference to a doc_id."""
        # Try relative to source
        candidate = (source_path.parent / phase_ref).resolve()
        doc_id = self.registry.lookup_by_path(str(candidate))
        if doc_id:
            return doc_id

        # Try with .yml extension
        if not phase_ref.endswith((".yml", ".yaml")):
            candidate_with_ext = (source_path.parent / f"{phase_ref}.yml").resolve()
            doc_id = self.registry.lookup_by_path(str(candidate_with_ext))
            if doc_id:
                return doc_id

        return None

    def _create_edge(
        self,
        source_doc_id: str,
        target_doc_id: str,
        edge_type: str,
        evidence: Dict[str, str]
    ) -> RelationshipEdge:
        """Create a RelationshipEdge with confidence scoring."""
        # Compute confidence (1.0 if target found, 0.0 if missing)
        confidence = 1.0 if target_doc_id else 0.0
        flags = [] if target_doc_id else ["target_missing"]

        # Generate timestamp
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()

        return RelationshipEdge(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            edge_type=edge_type,
            confidence=confidence,
            evidence=evidence,
            analyzer_id=self.analyzer_id,
            flags=flags,
            last_verified=timestamp
        )
