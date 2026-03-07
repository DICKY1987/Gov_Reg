#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-ARTIFACT-COMPATIBILITY-VALIDATOR-001
"""
DOC-CORE-ARTIFACT-COMPATIBILITY-VALIDATOR-001
Consumer-side validation for artifact freshness and compatibility.
Fail-fast if artifacts are stale or incompatible.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ArtifactCompatibilityError(Exception):
    """Raised when artifact compatibility check fails."""
    pass


class ArtifactCompatibilityValidator:
    """Validates artifact metadata for freshness and compatibility."""

    def __init__(self, repo_root: Optional[Path] = None, strict: bool = True):
        """
        Initialize validator.

        Args:
            repo_root: Repository root path
            strict: If True, raise exceptions on validation failure
        """
        self.repo_root = repo_root or Path.cwd()
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_metadata(self, artifact_path: Path) -> Optional[Dict]:
        """
        Load metadata for an artifact.

        First tries embedded metadata, then sidecar file.

        Args:
            artifact_path: Path to artifact file

        Returns:
            Metadata dictionary or None if not found
        """
        # Try embedded metadata first (for JSON files)
        if artifact_path.suffix == '.json':
            try:
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and '_metadata' in data:
                    return data['_metadata']
            except (json.JSONDecodeError, IOError):
                pass

        # Try sidecar metadata file
        metadata_path = artifact_path.with_suffix(artifact_path.suffix + ".meta.json")
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                error = f"Failed to load metadata from {metadata_path}: {e}"
                if self.strict:
                    raise ArtifactCompatibilityError(error)
                self.errors.append(error)

        return None

    def validate_freshness(
        self,
        metadata: Dict,
        artifact_path: Path,
        max_age_hours: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate artifact freshness.

        Args:
            metadata: Artifact metadata
            artifact_path: Path to artifact
            max_age_hours: Override max age from metadata

        Returns:
            Tuple of (is_valid, error_message)
        """
        if 'generated_at_utc' not in metadata:
            return False, "Missing 'generated_at_utc' in metadata"

        try:
            generated_at = datetime.fromisoformat(metadata['generated_at_utc'].replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            return False, f"Invalid timestamp format: {e}"

        # Get max age from metadata or override
        if max_age_hours is None:
            max_age_hours = metadata.get('compatibility', {}).get('max_age_hours')

        if max_age_hours is not None:
            age = datetime.utcnow() - generated_at.replace(tzinfo=None)
            if age > timedelta(hours=max_age_hours):
                return False, f"Artifact is stale: age={age.total_seconds()/3600:.1f}h, max={max_age_hours}h"

        return True, None

    def validate_schema_version(
        self,
        metadata: Dict,
        required_version: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate schema version compatibility.

        Args:
            metadata: Artifact metadata
            required_version: Required schema version (e.g., "v1.0.0")

        Returns:
            Tuple of (is_valid, error_message)
        """
        if 'schema_version' not in metadata:
            return False, "Missing 'schema_version' in metadata"

        schema_version = metadata['schema_version']

        # If no requirement specified, accept any version
        if required_version is None:
            min_version = metadata.get('compatibility', {}).get('min_schema_version')
            if min_version:
                required_version = min_version
            else:
                return True, None

        # Simple version comparison (assumes semantic versioning)
        try:
            current = tuple(map(int, schema_version.lstrip('v').split('.')))
            required = tuple(map(int, required_version.lstrip('v').split('.')))

            if current < required:
                return False, f"Schema version {schema_version} < required {required_version}"
        except (ValueError, AttributeError) as e:
            return False, f"Invalid version format: {e}"

        return True, None

    def validate_inputs(
        self,
        metadata: Dict,
        artifact_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that input files exist and haven't changed.

        Args:
            metadata: Artifact metadata
            artifact_path: Path to artifact

        Returns:
            Tuple of (is_valid, error_message)
        """
        if 'inputs' not in metadata:
            return True, None  # No inputs specified

        import hashlib

        for input_path_str, expected_hash in metadata['inputs'].items():
            input_path = self.repo_root / input_path_str

            if not input_path.exists():
                return False, f"Input file missing: {input_path_str}"

            # Compute current hash
            sha256_hash = hashlib.sha256()
            with open(input_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()

            if current_hash != expected_hash:
                return False, f"Input file changed: {input_path_str} (hash mismatch)"

        return True, None

    def validate_artifact(
        self,
        artifact_path: Path,
        required_schema_version: Optional[str] = None,
        max_age_hours: Optional[int] = None,
        check_inputs: bool = True
    ) -> bool:
        """
        Perform full validation on an artifact.

        Args:
            artifact_path: Path to artifact file
            required_schema_version: Required schema version
            max_age_hours: Maximum age in hours
            check_inputs: Whether to validate input hashes

        Returns:
            True if valid, False otherwise (or raises exception in strict mode)
        """
        # Load metadata
        metadata = self.load_metadata(artifact_path)
        if metadata is None:
            error = f"No metadata found for artifact: {artifact_path}"
            if self.strict:
                raise ArtifactCompatibilityError(error)
            self.errors.append(error)
            return False

        # Validate freshness
        valid, error = self.validate_freshness(metadata, artifact_path, max_age_hours)
        if not valid:
            if self.strict:
                raise ArtifactCompatibilityError(f"Freshness check failed for {artifact_path}: {error}")
            self.errors.append(f"{artifact_path}: {error}")
            return False

        # Validate schema version
        valid, error = self.validate_schema_version(metadata, required_schema_version)
        if not valid:
            if self.strict:
                raise ArtifactCompatibilityError(f"Schema version check failed for {artifact_path}: {error}")
            self.errors.append(f"{artifact_path}: {error}")
            return False

        # Validate inputs if requested
        if check_inputs:
            valid, error = self.validate_inputs(metadata, artifact_path)
            if not valid:
                warning = f"{artifact_path}: {error}"
                self.warnings.append(warning)
                # Input changes are warnings, not errors

        return True

    def get_report(self) -> Dict:
        """Get validation report."""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "status": "PASS" if len(self.errors) == 0 else "FAIL"
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate artifact compatibility")
    parser.add_argument("artifact", type=Path, help="Path to artifact file")
    parser.add_argument("--max-age-hours", type=int, help="Maximum age in hours")
    parser.add_argument("--schema-version", type=str, help="Required schema version")
    parser.add_argument("--no-strict", action="store_true", help="Don't raise exceptions")
    parser.add_argument("--no-check-inputs", action="store_true", help="Skip input validation")

    args = parser.parse_args()

    validator = ArtifactCompatibilityValidator(strict=not args.no_strict)

    try:
        valid = validator.validate_artifact(
            artifact_path=args.artifact,
            required_schema_version=args.schema_version,
            max_age_hours=args.max_age_hours,
            check_inputs=not args.no_check_inputs
        )

        report = validator.get_report()
        print(json.dumps(report, indent=2))

        sys.exit(0 if valid else 1)

    except ArtifactCompatibilityError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
