"""
Pipeline Runner - FCA-001 Remediation

Purpose: Execute transformation pipeline with envelope validation
         Ensures all outputs are normalized before staging

Contract: output_result_envelope_contract
Category: Executor
Priority: Critical

Changes from original:
- Added result envelope validation before staging
- Added automatic normalization of raw payloads
- Added evidence generation for staged outputs
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from utils.envelope_normalizer import EnvelopeNormalizer


class PipelineRunner:
    """
    Executes transformation pipeline with envelope contract enforcement
    
    FCA-001 Fix: Validates and normalizes all transformer outputs
    before staging to prevent silent data loss.
    """
    
    def __init__(
        self,
        component_name: str = "pipeline_runner",
        evidence_dir: Optional[Path] = None,
        strict_mode: bool = True
    ):
        """
        Initialize pipeline runner
        
        Args:
            component_name: Name of this component for logging
            evidence_dir: Directory for evidence artifacts
            strict_mode: If True, reject invalid envelopes; if False, auto-normalize
        """
        self.component_name = component_name
        self.evidence_dir = evidence_dir or Path(".state/evidence/phase1")
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(component_name)
        
        # Ensure evidence directory exists
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_transform(
        self,
        transformer: Callable[[Any], Any],
        input_data: Any
    ) -> Dict[str, Any]:
        """
        Execute transformation with envelope contract enforcement
        
        Args:
            transformer: Transformation function
            input_data: Input to transform
            
        Returns:
            Normalized result envelope
            
        Raises:
            ValueError: If strict_mode=True and result envelope is invalid
        """
        self.logger.info(f"Executing transformation: {transformer.__name__}")
        
        # Execute transformation
        result = transformer(input_data)
        
        # FCA-001 FIX: Validate result envelope before staging
        is_valid = EnvelopeNormalizer.is_valid_envelope(result)
        
        if not is_valid:
            if self.strict_mode:
                # In strict mode, reject invalid envelopes
                error_msg = (
                    f"Transformer {transformer.__name__} returned invalid envelope. "
                    f"Expected envelope with 'data', 'status', 'metadata' fields. "
                    f"Got: {type(result).__name__}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                # In lenient mode, auto-normalize
                self.logger.warning(
                    f"Transformer {transformer.__name__} returned raw payload. "
                    f"Auto-normalizing into standard envelope."
                )
                result = EnvelopeNormalizer.normalize(
                    result,
                    component=transformer.__name__
                )
        
        self.logger.info(
            f"Transformation complete. Status: {result.get('status', 'unknown')}"
        )
        
        return result
    
    def stage_output(
        self,
        result: Dict[str, Any],
        stage_path: Path
    ) -> None:
        """
        Stage validated output for patch generation
        
        FCA-001 FIX: Only stages outputs that pass envelope validation
        
        Args:
            result: Validated result envelope
            stage_path: Path to stage output file
            
        Raises:
            ValueError: If result is not a valid envelope
        """
        # Final validation before staging
        if not EnvelopeNormalizer.is_valid_envelope(result):
            raise ValueError(
                "Cannot stage invalid envelope. "
                "Result must pass envelope validation before staging."
            )
        
        # Create staging directory
        stage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Stage output
        with open(stage_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        self.logger.info(f"Output staged: {stage_path}")
        
        # Generate evidence
        self._generate_staging_evidence(result, stage_path)
    
    def _generate_staging_evidence(
        self,
        result: Dict[str, Any],
        stage_path: Path
    ) -> None:
        """
        Generate evidence artifacts for staged output
        
        Args:
            result: Staged result envelope
            stage_path: Path where output was staged
        """
        evidence = {
            "staged_at": datetime.utcnow().isoformat() + "Z",
            "stage_path": str(stage_path),
            "component": self.component_name,
            "envelope_valid": True,
            "status": result.get("status", "unknown"),
            "has_data": "data" in result,
            "has_metadata": "metadata" in result,
            "metadata": result.get("metadata", {})
        }
        
        evidence_path = self.evidence_dir / "staged_output_manifest.json"
        
        # Append to manifest (supports multiple staging operations)
        if evidence_path.exists():
            with open(evidence_path, 'r') as f:
                manifest = json.load(f)
            if not isinstance(manifest, list):
                manifest = [manifest]
        else:
            manifest = []
        
        manifest.append(evidence)
        
        with open(evidence_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        self.logger.debug(f"Evidence generated: {evidence_path}")
    
    def run_pipeline(
        self,
        transformers: List[Callable[[Any], Any]],
        input_data: Any,
        stage_path: Path
    ) -> Dict[str, Any]:
        """
        Run full transformation pipeline
        
        Args:
            transformers: List of transformation functions to apply
            input_data: Initial input
            stage_path: Path to stage final output
            
        Returns:
            Final result envelope
        """
        self.logger.info(f"Starting pipeline with {len(transformers)} transformers")
        
        current_data = input_data
        
        # Execute transformers in sequence
        for i, transformer in enumerate(transformers):
            self.logger.info(f"Step {i+1}/{len(transformers)}: {transformer.__name__}")
            
            result = self.execute_transform(transformer, current_data)
            
            # Extract data for next transformer
            current_data = EnvelopeNormalizer.extract_data(result)
        
        # Final result
        final_result = EnvelopeNormalizer.normalize(
            current_data,
            component=self.component_name
        )
        
        # Stage final output
        self.stage_output(final_result, stage_path)
        
        self.logger.info("Pipeline complete")
        
        return final_result


# Convenience function
def run_pipeline(
    transformers: List[Callable[[Any], Any]],
    input_data: Any,
    stage_path: Path,
    strict_mode: bool = True
) -> Dict[str, Any]:
    """
    Convenience wrapper for PipelineRunner.run_pipeline
    
    Args:
        transformers: List of transformation functions
        input_data: Input data
        stage_path: Where to stage output
        strict_mode: If True, reject invalid envelopes
        
    Returns:
        Final result envelope
    """
    runner = PipelineRunner(strict_mode=strict_mode)
    return runner.run_pipeline(transformers, input_data, stage_path)
