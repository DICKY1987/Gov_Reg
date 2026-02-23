"""
Identity Resolver - 4-Step Matching Algorithm

Resolves observed files to planned registry records using:
1. Exact path matching
2. Rename-intent matching (path_history/path_aliases)
3. Strong identity matching (file_id extraction from filename)
4. Conflict/orphan classification
"""
import re
from pathlib import Path
from typing import Dict, List, Optional
from .lifecycle_state import MatchResult, ConflictKind

class IdentityResolver:
    """4-step identity resolution algorithm."""
    
    def __init__(self, planned_records: List[Dict]):
        """Build indexes for fast lookups."""
        self.planned_records = planned_records
        
        # Build indexes
        self.path_index = {}
        self.file_id_index = {}
        self.path_history_index = {}
        self.path_aliases_index = {}
        
        for record in planned_records:
            # Exact path index
            canonical = record.get('canonical_path', '')
            if canonical:
                norm = self._normalize_path(canonical)
                self.path_index.setdefault(norm, []).append(record)
            
            # File ID index
            file_id = record.get('file_id', '')
            if file_id:
                self.file_id_index.setdefault(file_id, []).append(record)
            
            # Path history index
            for hist_path in record.get('path_history', []):
                norm = self._normalize_path(hist_path)
                self.path_history_index.setdefault(norm, []).append(record)
            
            # Path aliases index
            for alias_path in record.get('path_aliases', []):
                norm = self._normalize_path(alias_path)
                self.path_aliases_index.setdefault(norm, []).append(record)
    
    def resolve_batch(self, observed_files: List[Dict]) -> List[MatchResult]:
        """
        Resolve batch of observed files (two-pass for cross-file conflicts).
        
        Pass 1: Resolve each file independently
        Pass 2: Detect cross-file conflicts (DUPLICATE_PLANS, ID_COLLISION)
        """
        results = []
        
        # Pass 1: Individual resolution
        for observed in observed_files:
            result = self._resolve_single(observed)
            results.append(result)
        
        # Pass 2: Cross-file conflict detection
        self._detect_cross_file_conflicts(results)
        
        return results
    
    def _resolve_single(self, observed: Dict) -> MatchResult:
        """
        4-step ordered matching for single observed file.
        
        Steps:
        1. Exact path match
        2. Rename-intent match (path_history/path_aliases)
        3. Strong identity match (file_id extraction)
        4. Classify as orphaned or conflict
        """
        observed_path = observed.get('observed_path', '')
        
        # Step 1: Exact path
        match = self._step_1_exact_path(observed_path)
        if match:
            if isinstance(match, dict) and 'conflict' in match:
                return MatchResult(
                    observed_path=observed_path,
                    match_kind='conflict',
                    conflict_kind=ConflictKind.MULTI_MATCH,
                    candidates=match['candidates']
                )
            collision_candidates = self._detect_path_collision(observed_path, match)
            if collision_candidates:
                return MatchResult(
                    observed_path=observed_path,
                    match_kind='conflict',
                    conflict_kind=ConflictKind.PATH_COLLISION,
                    candidates=collision_candidates
                )
            return MatchResult(
                observed_path=observed_path,
                match_kind='exact_path',
                matched_record_id=match.get('record_id')
            )
        
        # Step 2: Rename-intent
        match = self._step_2_rename_intent(observed_path)
        if match:
            if isinstance(match, dict) and 'conflict' in match:
                return MatchResult(
                    observed_path=observed_path,
                    match_kind='conflict',
                    conflict_kind=ConflictKind.PATH_COLLISION,
                    candidates=match['candidates']
                )
            return MatchResult(
                observed_path=observed_path,
                match_kind='rename_intent',
                matched_record_id=match.get('record_id')
            )
        
        # Step 3: Strong identity
        match = self._step_3_strong_identity(observed_path)
        if match:
            if isinstance(match, dict) and 'conflict' in match:
                return MatchResult(
                    observed_path=observed_path,
                    match_kind='conflict',
                    conflict_kind=ConflictKind.ID_COLLISION,
                    candidates=match['candidates']
                )
            return MatchResult(
                observed_path=observed_path,
                match_kind='strong_identity',
                matched_record_id=match.get('record_id')
            )
        
        # Step 4: No match - orphaned
        return MatchResult(
            observed_path=observed_path,
            match_kind='orphaned'
        )

    def _detect_path_collision(self, observed_path: str, exact_match: Dict) -> Optional[List[Dict]]:
        """Detect rename-intent collisions against an exact path match."""
        norm = self._normalize_path(observed_path)
        exact_id = exact_match.get('record_id')
        candidates = []
        seen_ids = set()

        for record in self.path_history_index.get(norm, []) + self.path_aliases_index.get(norm, []):
            rec_id = record.get('record_id')
            if rec_id and rec_id != exact_id and rec_id not in seen_ids:
                candidates.append(record)
                seen_ids.add(rec_id)

        if candidates:
            return [exact_match] + candidates
        return None
    
    def _step_1_exact_path(self, observed_path: str) -> Optional[Dict]:
        """Step 1: Exact canonical path match."""
        norm = self._normalize_path(observed_path)
        matches = self.path_index.get(norm, [])
        
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return {'conflict': 'MULTI_MATCH', 'candidates': matches}
        return None
    
    def _step_2_rename_intent(self, observed_path: str) -> Optional[Dict]:
        """
        Step 2: Check path_history and path_aliases.
        
        Returns single match or conflict dict if multiple matches.
        """
        norm = self._normalize_path(observed_path)
        matches = []
        
        # Check path_history
        hist_matches = self.path_history_index.get(norm, [])
        matches.extend(hist_matches)
        
        # Check path_aliases
        alias_matches = self.path_aliases_index.get(norm, [])
        matches.extend(alias_matches)
        
        # Deduplicate by record_id
        unique_matches = []
        seen_ids = set()
        for match in matches:
            rec_id = match.get('record_id')
            if rec_id and rec_id not in seen_ids:
                unique_matches.append(match)
                seen_ids.add(rec_id)
        
        if len(unique_matches) == 1:
            return unique_matches[0]
        elif len(unique_matches) > 1:
            return {'conflict': 'RENAME_AMBIGUITY', 'candidates': unique_matches}
        return None
    
    def _step_3_strong_identity(self, observed_path: str) -> Optional[Dict]:
        """
        Step 3: Extract file_id from filename and match.
        
        Pattern: P_{FILE_ID}_{name}.py
        FILE_ID must be 20 digits starting with "01" (file IDs, not GEU IDs).
        """
        filename = Path(observed_path).name
        extracted_id = self._extract_file_id_from_filename(filename)
        
        if extracted_id:
            matches = self.file_id_index.get(extracted_id, [])
            
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                return {
                    'conflict': 'ID_COLLISION',
                    'file_id': extracted_id,
                    'candidates': matches
                }
        
        return None
    
    def _extract_file_id_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract 20-digit file_id from Python filename.
        
        Pattern: P_{FILE_ID}_{name}.py
        Validates "01" prefix (file IDs), rejects "99" prefix (GEU IDs).
        
        Returns:
            Valid file_id string or None
        """
        match = re.match(r'P_(\d{20})_', filename)
        if match:
            file_id = match.group(1)
            # Validate it's a file ID (starts with "01"), not GEU ID ("99")
            if file_id.startswith('01'):
                return file_id
        return None
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for comparison (lowercase on Windows, resolve relative)."""
        import sys
        norm = str(Path(path).as_posix())
        if sys.platform == 'win32':
            norm = norm.lower()
        return norm
    
    def _detect_cross_file_conflicts(self, results: List[MatchResult]):
        """
        Pass 2: Detect cross-file conflicts.
        
        - DUPLICATE_PLANS: Multiple files matched same planned record
        - ID_COLLISION: Already detected in step 3
        """
        # Track which planned records were matched
        matched_records = {}
        
        for result in results:
            if result.matched_record_id:
                rec_id = result.matched_record_id
                matched_records.setdefault(rec_id, []).append(result)
        
        # Check for duplicate plans (multiple files → same record)
        for rec_id, matching_results in matched_records.items():
            if len(matching_results) > 1:
                for result in matching_results:
                    result.match_kind = 'conflict'
                    result.conflict_kind = ConflictKind.DUPLICATE_PLANS
                    result.candidates = [
                        {'observed_path': r.observed_path}
                        for r in matching_results
                    ]
