#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-ARTIFACT-METADATA-WRITER-001
"""
DOC-CORE-ARTIFACT-METADATA-WRITER-001
Automatic metadata generation for all produced artifacts.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class ArtifactMetadataWriter:
    """Generates and writes artifact metadata for freshness validation."""

    SCHEMA_VERSION = "v1.0.0"

    def __init__(self, run_id: str, repo_root: Optional[Path] = None):
        """
        Initialize metadata writer.

        Args:
            run_id: Unique run identifier (format: RUN-YYYYMMDDHHMMSS)
            repo_root: Repository root path (defaults to current working directory)
        """
        self.run_id = run_id
        self.repo_root = repo_root or Path.cwd()

        if not self._validate_run_id(run_id):
            raise ValueError(f"Invalid run_id format: {run_id}. Expected: RUN-YYYYMMDDHHMMSS")

    @staticmethod
    def _validate_run_id(run_id: str) -> bool:
        """Validate run_id format."""
        import re
        return bool(re.match(r'^RUN-\d{14}$', run_id))

    def compute_file_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def generate_metadata(
        self,
        artifact_path: Path,
        artifact_type: str,
        produced_by_tool: str,
        tool_version: str,
        inputs: Dict[str, Path],
        dependencies: Optional[List[str]] = None,
        max_age_hours: Optional[int] = None,
        command: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate metadata for an artifact.

        Args:
            artifact_path: Path to the artifact file
            artifact_type: Type of artifact (json, yaml, markdown, etc.)
            produced_by_tool: Name/ID of tool that produced the artifact
            tool_version: Version of the producing tool
            inputs: Dictionary mapping input names to their file paths
            dependencies: List of artifact paths this artifact depends on
            max_age_hours: Maximum age before artifact is considered stale
            command: Command line used to produce the artifact (optional)
            custom_metadata: Tool-specific metadata (optional)

        Returns:
            Dictionary containing artifact metadata
        """
        # Convert to relative path
        rel_path = str(artifact_path.relative_to(self.repo_root))

        # Compute input hashes
        input_hashes = {}
        for input_name, input_path in inputs.items():
            if input_path.exists():
                input_hashes[str(input_path.relative_to(self.repo_root))] = self.compute_file_hash(input_path)

        metadata = {
            "schema_version": self.SCHEMA_VERSION,
            "artifact_path": rel_path,
            "artifact_type": artifact_type,
            "produced_by": {
                "tool": produced_by_tool,
                "version": tool_version
            },
            "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "inputs": input_hashes
        }

        if command:
            metadata["produced_by"]["command"] = command

        if dependencies:
            metadata["dependencies"] = dependencies

        if max_age_hours is not None:
            metadata["compatibility"] = {
                "min_schema_version": self.SCHEMA_VERSION,
                "max_age_hours": max_age_hours
            }

        if custom_metadata:
            metadata["custom_metadata"] = custom_metadata

        return metadata

    def write_metadata(
        self,
        artifact_path: Path,
        metadata: Dict[str, Any],
        embed_in_artifact: bool = True
    ) -> Path:
        """
        Write metadata to a sidecar file and optionally embed in artifact.

        Args:
            artifact_path: Path to the artifact file
            metadata: Metadata dictionary
            embed_in_artifact: If True and artifact is JSON, embed metadata

        Returns:
            Path to metadata sidecar file
        """
        # Write sidecar metadata file
        metadata_path = artifact_path.with_suffix(artifact_path.suffix + ".meta.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, sort_keys=True)

        # Optionally embed in JSON artifacts
        if embed_in_artifact and artifact_path.suffix == '.json':
            try:
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    artifact_data = json.load(f)

                if isinstance(artifact_data, dict):
                    artifact_data['_metadata'] = metadata
                    with open(artifact_path, 'w', encoding='utf-8') as f:
                        json.dump(artifact_data, f, indent=2, sort_keys=True)
            except (json.JSONDecodeError, IOError):
                # If we can't embed, that's okay - sidecar still exists
                pass

        return metadata_path

    def generate_and_write(
        self,
        artifact_path: Path,
        artifact_type: str,
        produced_by_tool: str,
        tool_version: str,
        inputs: Dict[str, Path],
        **kwargs
    ) -> Path:
        """
        Convenience method to generate and write metadata in one call.

        Returns:
            Path to metadata sidecar file
        """
        metadata = self.generate_metadata(
            artifact_path=artifact_path,
            artifact_type=artifact_type,
            produced_by_tool=produced_by_tool,
            tool_version=tool_version,
            inputs=inputs,
            **kwargs
        )
        return self.write_metadata(artifact_path, metadata)


def generate_run_id() -> str:
    """Generate a new run ID based on current UTC time."""
    return datetime.utcnow().strftime("RUN-%Y%m%d%H%M%S")


if __name__ == "__main__":
    # Example usage
    writer = ArtifactMetadataWriter(run_id=generate_run_id())

    # Example: Generate metadata for a hypothetical artifact
    example_artifact = Path("example_output.json")
    example_inputs = {
        "input1": Path("data/source1.yaml"),
        "input2": Path("data/source2.json")
    }

    print(f"Metadata writer initialized with schema version: {writer.SCHEMA_VERSION}")
    print(f"Run ID: {writer.run_id}")
