"""
Envelope Normalizer - FCA-001 Remediation

Purpose: Normalize transformer outputs into standard result envelope
         Prevents valid transformation outputs from being silently dropped

Contract: output_result_envelope_contract
Category: Executor
Priority: Critical

Standard Envelope Schema:
{
    "data": <actual_payload>,
    "status": "success" | "error",
    "metadata": {
        "timestamp": "ISO8601",
        "component": "component_name",
        "version": "1.0.0"
    }
}
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class EnvelopeNormalizer:
    """Normalizes transformer outputs into standard result envelope"""
    
    ENVELOPE_VERSION = "1.0.0"
    
    @staticmethod
    def is_valid_envelope(result: Any) -> bool:
        """
        Check if result already has valid envelope structure
        
        Args:
            result: Output from transformer
            
        Returns:
            True if result has required envelope fields
        """
        if not isinstance(result, dict):
            return False
            
        # Check for required envelope fields
        has_data = "data" in result
        has_status = "status" in result
        has_metadata = "metadata" in result
        
        return has_data and has_status and has_metadata
    
    @staticmethod
    def normalize(
        result: Any,
        component: str = "unknown",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Normalize result into standard envelope
        
        Args:
            result: Raw transformer output or existing envelope
            component: Name of component that produced the result
            force: If True, re-wrap even if already has envelope
            
        Returns:
            Normalized envelope with data, status, metadata
            
        Examples:
            >>> # Raw payload (no envelope)
            >>> EnvelopeNormalizer.normalize({"key": "value"}, "transformer")
            {
                "data": {"key": "value"},
                "status": "success",
                "metadata": {"timestamp": "...", "component": "transformer", ...}
            }
            
            >>> # Already has envelope
            >>> EnvelopeNormalizer.normalize(
            ...     {"data": {...}, "status": "success", "metadata": {...}},
            ...     "transformer"
            ... )
            # Returns as-is (validates and passes through)
        """
        # If already valid envelope and not forcing, validate and return
        if EnvelopeNormalizer.is_valid_envelope(result) and not force:
            # Validate existing envelope
            EnvelopeNormalizer._validate_envelope(result)
            return result
        
        # Wrap raw payload in envelope
        envelope = {
            "data": result,
            "status": "success",
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "component": component,
                "version": EnvelopeNormalizer.ENVELOPE_VERSION,
                "normalized": True
            }
        }
        
        return envelope
    
    @staticmethod
    def _validate_envelope(envelope: Dict[str, Any]) -> None:
        """
        Validate envelope structure
        
        Args:
            envelope: Envelope to validate
            
        Raises:
            ValueError: If envelope is invalid
        """
        if "status" in envelope:
            valid_statuses = ["success", "error", "pending"]
            if envelope["status"] not in valid_statuses:
                raise ValueError(
                    f"Invalid status: {envelope['status']}. "
                    f"Must be one of {valid_statuses}"
                )
        
        if "metadata" in envelope:
            metadata = envelope["metadata"]
            if not isinstance(metadata, dict):
                raise ValueError("metadata must be a dictionary")
    
    @staticmethod
    def extract_data(envelope: Dict[str, Any]) -> Any:
        """
        Extract data payload from envelope
        
        Args:
            envelope: Result envelope
            
        Returns:
            Data payload (may be any type)
            
        Raises:
            ValueError: If envelope is invalid
        """
        if not EnvelopeNormalizer.is_valid_envelope(envelope):
            raise ValueError(
                "Cannot extract data from invalid envelope. "
                "Envelope must have 'data', 'status', and 'metadata' fields."
            )
        
        return envelope["data"]
    
    @staticmethod
    def create_error_envelope(
        error_message: str,
        component: str = "unknown",
        error_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create error envelope
        
        Args:
            error_message: Human-readable error description
            component: Component that encountered the error
            error_details: Additional error context
            
        Returns:
            Error envelope
        """
        envelope = {
            "data": None,
            "status": "error",
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "component": component,
                "version": EnvelopeNormalizer.ENVELOPE_VERSION,
                "error_message": error_message
            }
        }
        
        if error_details:
            envelope["metadata"]["error_details"] = error_details
        
        return envelope


# Convenience functions
def normalize_result(result: Any, component: str = "unknown") -> Dict[str, Any]:
    """Convenience wrapper for EnvelopeNormalizer.normalize"""
    return EnvelopeNormalizer.normalize(result, component)


def is_valid_envelope(result: Any) -> bool:
    """Convenience wrapper for EnvelopeNormalizer.is_valid_envelope"""
    return EnvelopeNormalizer.is_valid_envelope(result)


def extract_data(envelope: Dict[str, Any]) -> Any:
    """Convenience wrapper for EnvelopeNormalizer.extract_data"""
    return EnvelopeNormalizer.extract_data(envelope)
