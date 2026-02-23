#!/usr/bin/env python3
r"""
FILE_ID: 01999000042260125072
Migrated from: C:\Users\richg\ALL_AI\mapp_py\DOC-SCRIPT-0991__integration_bridge.py
"""

# DOC_ID: DOC-SCRIPT-0991
"""
MAPP-PY Integration Bridge for AI_CLI_PROVENANCE_SOLUTION

This module provides the integration layer between mapp_py Python introspection
and the AI CLI Provenance triage system.

Work ID: WORK-MAPP-PY-001-PHASE-7
Module: integration_bridge.py
Component ID: MAPP_PY_INTEGRATION_BRIDGE
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Add mapp_py src to path
_repo_root = Path(__file__).parents[2]
sys.path.insert(0, str(_repo_root / "01260207201000001313_capability_mapping_system" / "mapp_py"))

from P_01260202173939000068_file_comparator import FileComparator, ComparisonResult


@dataclass
class IntegratedEvidence:
    """Evidence structure compatible with py_identify_solution.yml"""
    file_path: str
    evidence: Dict[str, Any]
    comparison_results: Optional[Dict[str, ComparisonResult]] = None


class MappPyIntegrationBridge:
    """
    Bridge between mapp_py and AI_CLI_PROVENANCE_SOLUTION.

    Features:
    - Converts mapp_py comparison results to evidence schema format
    - Enables rules R_RED_001, R_RED_003, R_RED_004 in py_identify_solution.yml
    - Provides evidence for:
      * evidence.similarity.structural
      * evidence.similarity.semantic
      * evidence.context.dependency_overlap.jaccard
      * evidence.io.surface_overlap.jaccard

    Usage:
        bridge = MappPyIntegrationBridge()
        evidence = bridge.analyze_file_for_triage("script.py", candidate_files)
        # Use evidence in triage decision engine
    """

    def __init__(self, trace_id: str = None, run_id: str = None):
        """
        Initialize integration bridge.

        Args:
            trace_id: Distributed trace ID for observability
            run_id: Execution run ID
        """
        self.comparator = FileComparator(trace_id=trace_id, run_id=run_id)
        self.trace_id = trace_id
        self.run_id = run_id

    def analyze_file_for_triage(
        self,
        target_file: Path,
        candidate_files: List[Path],
        min_similarity: float = 0.85
    ) -> IntegratedEvidence:
        """
        Analyze a Python file against candidates for triage evidence.

        Generates evidence compatible with these rules:
        - R_RED_001: Duplicate set candidate detection
        - R_RED_003: Similar script detection (with I/O overlap)
        - R_RED_004: Canonical preference calculation

        Args:
            target_file: The file being triaged
            candidate_files: List of files to compare against
            min_similarity: Minimum similarity threshold (default: 0.85)

        Returns:
            IntegratedEvidence with evidence dict matching schema
        """
        comparison_results = {}
        best_match = None
        best_score = 0.0

        # Compare target against all candidates
        for candidate in candidate_files:
            if candidate == target_file:
                continue

            result = self.comparator.compare(target_file, candidate)
            comparison_results[str(candidate)] = result

            if result.aggregate_score > best_score:
                best_score = result.aggregate_score
                best_match = result

        # Build evidence structure
        evidence = self._build_evidence_dict(
            target_file,
            best_match,
            comparison_results,
            min_similarity
        )

        return IntegratedEvidence(
            file_path=str(target_file),
            evidence=evidence,
            comparison_results=comparison_results
        )

    def _build_evidence_dict(
        self,
        target_file: Path,
        best_match: Optional[ComparisonResult],
        all_comparisons: Dict[str, ComparisonResult],
        min_similarity: float
    ) -> Dict[str, Any]:
        """
        Build evidence dict matching EVIDENCE_SCHEMA_EXTENDED.yaml format.

        Returns evidence for:
        - evidence.similarity.structural
        - evidence.similarity.semantic
        - evidence.context.dependency_overlap
        - evidence.io.surface_overlap
        - evidence.redundancy.best_match
        """
        evidence = {
            "similarity": {},
            "context": {},
            "io": {},
            "redundancy": {}
        }

        if best_match and not best_match.has_errors:
            # Structural similarity (R_RED_001 requires >= 0.92)
            evidence["similarity"]["structural"] = best_match.dimensions["structural"].score

            # Semantic similarity (R_RED_001 requires >= 0.85)
            evidence["similarity"]["semantic"] = best_match.dimensions["semantic"].score

            # Dependency overlap Jaccard (R_RED_001 requires >= 0.60)
            evidence["context"]["dependency_overlap"] = {
                "jaccard": best_match.dimensions["dependency"].score
            }

            # I/O surface overlap Jaccard (R_RED_003 requires >= 0.50)
            evidence["io"]["surface_overlap"] = {
                "jaccard": best_match.dimensions["io_surface"].score
            }

            # Redundancy best match (for R_OBS_002, R_OBS_004)
            meets_threshold = best_match.aggregate_score >= min_similarity
            evidence["redundancy"]["best_match"] = {
                "exists": meets_threshold,
                "min_similarity": best_match.aggregate_score,
                "min_confidence": best_match.decision_confidence,
                "canonical_candidate": best_match.decision == "SIMILAR",
                "matched_file": best_match.file_b,
                "decision": best_match.decision,
                "dimensions": {
                    "structural": best_match.dimensions["structural"].score,
                    "semantic": best_match.dimensions["semantic"].score,
                    "dependency": best_match.dimensions["dependency"].score,
                    "io_surface": best_match.dimensions["io_surface"].score
                },
                "aggregate_score": best_match.aggregate_score
            }
        else:
            # No matches or errors
            evidence["similarity"]["structural"] = 0.0
            evidence["similarity"]["semantic"] = 0.0
            evidence["context"]["dependency_overlap"] = {"jaccard": 0.0}
            evidence["io"]["surface_overlap"] = {"jaccard": 0.0}
            evidence["redundancy"]["best_match"] = {
                "exists": False,
                "min_similarity": 0.0,
                "min_confidence": 0.0,
                "canonical_candidate": False
            }

        return evidence

    def batch_analyze(
        self,
        files: List[Path],
        min_similarity: float = 0.85
    ) -> Dict[str, IntegratedEvidence]:
        """
        Batch analyze multiple Python files for triage.

        Performs N×N comparison to find all similar pairs.

        Args:
            files: List of Python files to analyze
            min_similarity: Minimum similarity threshold

        Returns:
            Dict mapping file path to IntegratedEvidence
        """
        results = {}

        for target_file in files:
            # Compare against all other files
            candidates = [f for f in files if f != target_file]
            evidence = self.analyze_file_for_triage(
                target_file,
                candidates,
                min_similarity
            )
            results[str(target_file)] = evidence

        return results

    def check_rule_satisfaction(
        self,
        evidence: IntegratedEvidence,
        rule_id: str
    ) -> bool:
        """
        Check if evidence satisfies a specific rule from py_identify_solution.yml

        Args:
            evidence: IntegratedEvidence to check
            rule_id: Rule ID (e.g., "R_RED_001", "R_RED_003")

        Returns:
            True if rule conditions are satisfied
        """
        ev = evidence.evidence

        if rule_id == "R_RED_001":
            # DUPLICATE_SET_CANDIDATE
            # Requires: structural >= 0.92, semantic >= 0.85, dependency >= 0.60
            return (
                ev.get("similarity", {}).get("structural", 0) >= 0.92 and
                ev.get("similarity", {}).get("semantic", 0) >= 0.85 and
                ev.get("context", {}).get("dependency_overlap", {}).get("jaccard", 0) >= 0.60
            )

        elif rule_id == "R_RED_003":
            # SIMILAR_SCRIPT_CANDIDATE
            # Requires: structural >= 0.92, semantic >= 0.85,
            #           dependency >= 0.60, io_surface >= 0.50
            return (
                ev.get("similarity", {}).get("structural", 0) >= 0.92 and
                ev.get("similarity", {}).get("semantic", 0) >= 0.85 and
                ev.get("context", {}).get("dependency_overlap", {}).get("jaccard", 0) >= 0.60 and
                ev.get("io", {}).get("surface_overlap", {}).get("jaccard", 0) >= 0.50
            )

        elif rule_id == "R_OBS_002":
            # OBSOLETE_CANDIDATE (partial check - only redundancy criteria)
            best_match = ev.get("redundancy", {}).get("best_match", {})
            return (
                best_match.get("exists", False) and
                best_match.get("min_similarity", 0) >= 0.90 and
                best_match.get("min_confidence", 0) >= 0.80 and
                best_match.get("canonical_candidate", False)
            )

        else:
            return False


# CLI Interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MAPP-PY Integration Bridge - Connect Python introspection to triage system"
    )
    parser.add_argument("target_file", type=Path, help="Python file to analyze")
    parser.add_argument("candidate_files", type=Path, nargs="+", help="Candidate files to compare against")
    parser.add_argument("--min-similarity", type=float, default=0.85, help="Minimum similarity threshold")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file for evidence")
    parser.add_argument("--check-rules", action="store_true", help="Check rule satisfaction")

    args = parser.parse_args()

    # Initialize bridge
    bridge = MappPyIntegrationBridge()

    # Analyze
    print(f"Analyzing {args.target_file} against {len(args.candidate_files)} candidates...")
    evidence = bridge.analyze_file_for_triage(
        args.target_file,
        args.candidate_files,
        args.min_similarity
    )

    # Print results
    print("\n=== Evidence Generated ===")
    print(f"Structural Similarity: {evidence.evidence['similarity']['structural']:.3f}")
    print(f"Semantic Similarity: {evidence.evidence['similarity']['semantic']:.3f}")
    print(f"Dependency Overlap: {evidence.evidence['context']['dependency_overlap']['jaccard']:.3f}")
    print(f"I/O Surface Overlap: {evidence.evidence['io']['surface_overlap']['jaccard']:.3f}")

    best_match = evidence.evidence['redundancy']['best_match']
    if best_match['exists']:
        print(f"\nBest Match: {best_match['matched_file']}")
        print(f"Aggregate Score: {best_match['aggregate_score']:.3f}")
        print(f"Decision: {best_match['decision']}")
    else:
        print("\nNo similar files found above threshold")

    # Check rules
    if args.check_rules:
        print("\n=== Rule Satisfaction ===")
        print(f"R_RED_001 (DUPLICATE_SET_CANDIDATE): {bridge.check_rule_satisfaction(evidence, 'R_RED_001')}")
        print(f"R_RED_003 (SIMILAR_SCRIPT_CANDIDATE): {bridge.check_rule_satisfaction(evidence, 'R_RED_003')}")
        print(f"R_OBS_002 (OBSOLETE_CANDIDATE - redundancy check): {bridge.check_rule_satisfaction(evidence, 'R_OBS_002')}")

    # Save output
    if args.output:
        output_data = {
            "file_path": evidence.file_path,
            "evidence": evidence.evidence,
            "trace_id": bridge.trace_id,
            "run_id": bridge.run_id
        }
        args.output.write_text(json.dumps(output_data, indent=2))
        print(f"\nEvidence saved to: {args.output}")
