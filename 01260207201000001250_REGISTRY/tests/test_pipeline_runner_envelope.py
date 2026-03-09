"""
Tests for Envelope Normalizer and Pipeline Runner - FCA-001 Verification

Purpose: Verify that envelope validation and normalization prevent data loss
         Tests the fix for FCA-001 (pipeline_runner silent skip bug)

Test Coverage:
- Envelope validation (valid/invalid detection)
- Normalization (raw payload → envelope)
- Data extraction from envelope
- Error envelope creation
- Pipeline runner with strict/lenient modes
- Evidence generation
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.envelope_normalizer import EnvelopeNormalizer, normalize_result, is_valid_envelope
from pipeline_runner import PipelineRunner


class TestEnvelopeNormalizer:
    """Test suite for EnvelopeNormalizer"""
    
    def test_valid_envelope_detection(self):
        """Test: Valid envelope is correctly identified"""
        valid_envelope = {
            "data": {"key": "value"},
            "status": "success",
            "metadata": {"timestamp": "2024-01-01T00:00:00Z"}
        }
        
        assert EnvelopeNormalizer.is_valid_envelope(valid_envelope) is True
    
    def test_invalid_envelope_detection_missing_fields(self):
        """Test: Invalid envelope (missing fields) is detected"""
        invalid_envelopes = [
            {"data": {"key": "value"}},  # Missing status, metadata
            {"status": "success"},  # Missing data, metadata
            {"data": {}, "status": "success"},  # Missing metadata
        ]
        
        for envelope in invalid_envelopes:
            assert EnvelopeNormalizer.is_valid_envelope(envelope) is False
    
    def test_invalid_envelope_detection_wrong_type(self):
        """Test: Non-dict is not a valid envelope"""
        invalid_types = [
            "string",
            123,
            ["list"],
            None
        ]
        
        for value in invalid_types:
            assert EnvelopeNormalizer.is_valid_envelope(value) is False
    
    def test_normalize_raw_payload(self):
        """Test: Raw payload is wrapped in envelope"""
        raw_payload = {"transformed": "data", "count": 42}
        component = "test_transformer"
        
        result = EnvelopeNormalizer.normalize(raw_payload, component)
        
        # Verify envelope structure
        assert "data" in result
        assert "status" in result
        assert "metadata" in result
        
        # Verify data preserved
        assert result["data"] == raw_payload
        
        # Verify status
        assert result["status"] == "success"
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["component"] == component
        assert "timestamp" in metadata
        assert "version" in metadata
        assert metadata["normalized"] is True
    
    def test_normalize_already_valid_passes_through(self):
        """Test: Valid envelope passes through without re-wrapping"""
        valid_envelope = {
            "data": {"key": "value"},
            "status": "success",
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "component": "original"
            }
        }
        
        result = EnvelopeNormalizer.normalize(valid_envelope, "test")
        
        # Should return as-is (not re-wrapped)
        assert result == valid_envelope
    
    def test_normalize_force_rewrap(self):
        """Test: Force flag causes re-wrapping even if valid"""
        valid_envelope = {
            "data": {"key": "value"},
            "status": "success",
            "metadata": {"component": "original"}
        }
        
        result = EnvelopeNormalizer.normalize(valid_envelope, "test", force=True)
        
        # Should be re-wrapped (data field now contains the original envelope)
        assert result["data"] == valid_envelope
        assert result["metadata"]["component"] == "test"
        assert result["metadata"]["normalized"] is True
    
    def test_extract_data_from_valid_envelope(self):
        """Test: Data extraction from valid envelope"""
        payload = {"transformed": "data"}
        envelope = {
            "data": payload,
            "status": "success",
            "metadata": {}
        }
        
        extracted = EnvelopeNormalizer.extract_data(envelope)
        
        assert extracted == payload
    
    def test_extract_data_from_invalid_raises(self):
        """Test: Extracting data from invalid envelope raises ValueError"""
        invalid_envelope = {"data": {}}  # Missing required fields
        
        with pytest.raises(ValueError, match="invalid envelope"):
            EnvelopeNormalizer.extract_data(invalid_envelope)
    
    def test_create_error_envelope(self):
        """Test: Error envelope creation"""
        error_msg = "Transformation failed"
        component = "test_transformer"
        error_details = {"code": "ERR_001", "line": 42}
        
        result = EnvelopeNormalizer.create_error_envelope(
            error_msg,
            component,
            error_details
        )
        
        assert result["status"] == "error"
        assert result["data"] is None
        assert result["metadata"]["error_message"] == error_msg
        assert result["metadata"]["error_details"] == error_details
        assert result["metadata"]["component"] == component


class TestPipelineRunner:
    """Test suite for PipelineRunner - FCA-001 fix verification"""
    
    @pytest.fixture
    def temp_evidence_dir(self, tmp_path):
        """Create temporary evidence directory"""
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        return evidence_dir
    
    @pytest.fixture
    def temp_stage_dir(self, tmp_path):
        """Create temporary staging directory"""
        stage_dir = tmp_path / "stage"
        stage_dir.mkdir()
        return stage_dir
    
    def test_execute_transform_with_valid_envelope(self, temp_evidence_dir):
        """Test: Transformer returning valid envelope is accepted"""
        def valid_transformer(data):
            return {
                "data": {"result": data},
                "status": "success",
                "metadata": {"component": "valid_transformer"}
            }
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir, strict_mode=True)
        result = runner.execute_transform(valid_transformer, {"input": "data"})
        
        assert EnvelopeNormalizer.is_valid_envelope(result)
        assert result["status"] == "success"
    
    def test_execute_transform_with_raw_payload_strict_raises(self, temp_evidence_dir):
        """Test: FCA-001 - Raw payload in strict mode raises ValueError"""
        def raw_transformer(data):
            # Returns raw dict without envelope (the bug FCA-001 describes)
            return {"transformed": data}
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir, strict_mode=True)
        
        with pytest.raises(ValueError, match="invalid envelope"):
            runner.execute_transform(raw_transformer, {"input": "data"})
    
    def test_execute_transform_with_raw_payload_lenient_normalizes(self, temp_evidence_dir):
        """Test: FCA-001 FIX - Raw payload in lenient mode is auto-normalized"""
        def raw_transformer(data):
            # Returns raw dict without envelope
            return {"transformed": data}
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir, strict_mode=False)
        result = runner.execute_transform(raw_transformer, {"input": "data"})
        
        # Should be auto-normalized
        assert EnvelopeNormalizer.is_valid_envelope(result)
        assert result["status"] == "success"
        assert result["data"] == {"transformed": {"input": "data"}}
        assert result["metadata"]["normalized"] is True
    
    def test_stage_output_valid_envelope(self, temp_evidence_dir, temp_stage_dir):
        """Test: Valid envelope can be staged"""
        valid_envelope = {
            "data": {"result": "data"},
            "status": "success",
            "metadata": {"component": "test"}
        }
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir)
        stage_path = temp_stage_dir / "output.json"
        
        runner.stage_output(valid_envelope, stage_path)
        
        # Verify file was created
        assert stage_path.exists()
        
        # Verify content
        with open(stage_path) as f:
            staged = json.load(f)
        assert staged == valid_envelope
        
        # Verify evidence was generated
        evidence_path = temp_evidence_dir / "staged_output_manifest.json"
        assert evidence_path.exists()
    
    def test_stage_output_invalid_envelope_raises(self, temp_evidence_dir, temp_stage_dir):
        """Test: Invalid envelope cannot be staged"""
        invalid_envelope = {"data": {}}  # Missing required fields
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir)
        stage_path = temp_stage_dir / "output.json"
        
        with pytest.raises(ValueError, match="invalid envelope"):
            runner.stage_output(invalid_envelope, stage_path)
        
        # Verify file was NOT created
        assert not stage_path.exists()
    
    def test_evidence_generation(self, temp_evidence_dir, temp_stage_dir):
        """Test: Evidence artifacts are generated correctly"""
        valid_envelope = {
            "data": {"result": "data"},
            "status": "success",
            "metadata": {"component": "test", "version": "1.0"}
        }
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir)
        stage_path = temp_stage_dir / "output.json"
        
        runner.stage_output(valid_envelope, stage_path)
        
        evidence_path = temp_evidence_dir / "staged_output_manifest.json"
        
        with open(evidence_path) as f:
            evidence = json.load(f)
        
        # Should be a list (supports multiple staging operations)
        if isinstance(evidence, dict):
            evidence = [evidence]
        
        assert len(evidence) > 0
        
        last_evidence = evidence[-1]
        assert "staged_at" in last_evidence
        assert last_evidence["envelope_valid"] is True
        assert last_evidence["status"] == "success"
        assert last_evidence["has_data"] is True
        assert last_evidence["has_metadata"] is True
    
    def test_run_pipeline_success(self, temp_evidence_dir, temp_stage_dir):
        """Test: Full pipeline execution with valid transformers"""
        def transform1(data):
            return {
                "data": {"step1": data},
                "status": "success",
                "metadata": {"component": "transform1"}
            }
        
        def transform2(data):
            return {
                "data": {"step2": data},
                "status": "success",
                "metadata": {"component": "transform2"}
            }
        
        runner = PipelineRunner(evidence_dir=temp_evidence_dir)
        stage_path = temp_stage_dir / "final_output.json"
        
        result = runner.run_pipeline(
            [transform1, transform2],
            {"input": "data"},
            stage_path
        )
        
        # Verify result
        assert EnvelopeNormalizer.is_valid_envelope(result)
        assert result["status"] == "success"
        
        # Verify staging
        assert stage_path.exists()
        
        # Verify evidence
        evidence_path = temp_evidence_dir / "staged_output_manifest.json"
        assert evidence_path.exists()


class TestFCA001Verification:
    """
    FCA-001 Specific Verification Tests
    
    Issue: Valid transformation outputs are silently not staged for patch generation
    Root Cause: Executor assumes wrapped transform envelope with "data" key; 
                transformer returns raw transformed payload in direct-call path
    Fix: Validate result envelope schema before staging; reject or normalize mismatched outputs
    """
    
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories"""
        evidence_dir = tmp_path / "evidence"
        stage_dir = tmp_path / "stage"
        evidence_dir.mkdir()
        stage_dir.mkdir()
        return evidence_dir, stage_dir
    
    def test_fca001_symptom_reproduced_in_strict_mode(self, temp_dirs):
        """Test: Reproduce FCA-001 symptom - raw payload rejected in strict mode"""
        evidence_dir, stage_dir = temp_dirs
        
        # Transformer that returns raw payload (the bug scenario)
        def buggy_transformer(data):
            return {"transformed": data, "count": 42}
        
        runner = PipelineRunner(evidence_dir=evidence_dir, strict_mode=True)
        
        # Should raise error in strict mode
        with pytest.raises(ValueError, match="invalid envelope"):
            runner.execute_transform(buggy_transformer, {"input": "data"})
    
    def test_fca001_fix_verified_lenient_mode(self, temp_dirs):
        """Test: FCA-001 FIX - Raw payload is normalized, preventing data loss"""
        evidence_dir, stage_dir = temp_dirs
        
        # Transformer that returns raw payload
        def raw_transformer(data):
            return {"transformed": data, "count": 42}
        
        runner = PipelineRunner(evidence_dir=evidence_dir, strict_mode=False)
        stage_path = stage_dir / "output.json"
        
        # Execute and stage
        result = runner.execute_transform(raw_transformer, {"input": "data"})
        runner.stage_output(result, stage_path)
        
        # Verify output was staged (NOT silently dropped)
        assert stage_path.exists()
        
        with open(stage_path) as f:
            staged = json.load(f)
        
        # Verify envelope is valid
        assert EnvelopeNormalizer.is_valid_envelope(staged)
        
        # Verify data was preserved
        assert staged["data"] == {"transformed": {"input": "data"}, "count": 42}
        
        # Verify evidence generated
        evidence_path = evidence_dir / "staged_output_manifest.json"
        assert evidence_path.exists()
    
    def test_fca001_acceptance_criteria(self, temp_dirs):
        """
        Test: FCA-001 Acceptance Criteria
        
        Given: Valid transform output without "data" wrapper
        When: Executor stages patch input
        Then: Output is staged exactly once (not silently dropped)
        """
        evidence_dir, stage_dir = temp_dirs
        
        # Valid transform output (no wrapper)
        def transform_without_wrapper(data):
            return {"result": "transformed", "original": data}
        
        runner = PipelineRunner(evidence_dir=evidence_dir, strict_mode=False)
        stage_path = stage_dir / "patch_input.json"
        
        # Execute
        result = runner.execute_transform(transform_without_wrapper, {"test": "data"})
        
        # Stage
        runner.stage_output(result, stage_path)
        
        # Verify staged exactly once
        assert stage_path.exists()
        
        # Verify evidence shows exactly one staging operation
        evidence_path = evidence_dir / "staged_output_manifest.json"
        with open(evidence_path) as f:
            evidence = json.load(f)
        
        if isinstance(evidence, dict):
            evidence = [evidence]
        
        # Should have exactly one entry for this staging operation
        assert len(evidence) == 1
        assert evidence[0]["envelope_valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
