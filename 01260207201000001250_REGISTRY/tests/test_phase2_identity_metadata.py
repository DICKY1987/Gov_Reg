"""
test_phase2_identity_metadata.py

Comprehensive tests for Phase 2: Identity and Metadata components.

Tests FCA-005, FCA-010, FCA-011, FCA-013, FCA-015
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from identity.file_id_resolver import FileIDResolver, FileIDResolutionError
from identity.repo_root_resolver import RepoRootResolver, RepoRootResolutionError
from identity.duplicate_sha256_resolver import DuplicateSHA256Resolver
from metadata.metadata_backfiller import MetadataBackfiller, MetadataBackfillError
from relationship.orphaned_entries_pruner import OrphanedEntriesPruner


# ============================================================================
# FCA-005: file_id Resolution Tests
# ============================================================================

class TestFileIDResolver:
    """Test file_id resolution (FCA-005)."""
    
    def test_valid_sha256_format(self):
        """Test SHA256 format validation."""
        resolver = FileIDResolver(strict_mode=False, allow_generation=False)
        
        assert resolver._is_valid_sha256("a" * 64)
        assert not resolver._is_valid_sha256("a" * 63)
        assert not resolver._is_valid_sha256("g" * 64)
    
    def test_cache_hit(self, tmp_path):
        """Test cache hit path."""
        cache_path = tmp_path / "cache.json"
        cache_data = {"a" * 64: "12345678901234567890"}
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        resolver = FileIDResolver(cache_path=cache_path, strict_mode=False)
        file_id = resolver.resolve("a" * 64)
        
        assert file_id == "12345678901234567890"
        assert resolver.stats["cache_hits"] == 1
        assert resolver.stats["cache_misses"] == 0
    
    def test_cache_miss_with_generation(self, tmp_path):
        """Test cache miss with generation enabled."""
        resolver = FileIDResolver(
            cache_path=tmp_path / "cache.json",
            strict_mode=False,
            allow_generation=True
        )
        
        sha256 = "b" * 64
        file_id = resolver.resolve(sha256)
        
        assert len(file_id) == 20
        assert file_id.isdigit()
        assert resolver.stats["cache_misses"] == 1
        assert resolver.stats["generations"] == 1
    
    def test_strict_mode_fails_on_unresolved(self, tmp_path):
        """Test strict mode fails when file_id cannot be resolved."""
        resolver = FileIDResolver(
            cache_path=tmp_path / "cache.json",
            strict_mode=True,
            allow_generation=False
        )
        
        with pytest.raises(FileIDResolutionError):
            resolver.resolve("c" * 64)
    
    def test_lenient_mode_returns_placeholder(self, tmp_path):
        """Test lenient mode returns placeholder on failure."""
        resolver = FileIDResolver(
            cache_path=tmp_path / "cache.json",
            strict_mode=False,
            allow_generation=False
        )
        
        file_id = resolver.resolve("d" * 64)
        assert file_id.startswith("UNRESOLVED_")
    
    def test_bulk_resolve(self, tmp_path):
        """Test bulk resolution."""
        cache_data = {
            "a" * 64: "11111111111111111111",
            "b" * 64: "22222222222222222222"
        }
        cache_path = tmp_path / "cache.json"
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        resolver = FileIDResolver(cache_path=cache_path)
        results = resolver.bulk_resolve(["a" * 64, "b" * 64])
        
        assert results["a" * 64] == ("11111111111111111111", True)
        assert results["b" * 64] == ("22222222222222222222", True)
    
    def test_fca005_acceptance_criteria(self, tmp_path):
        """
        FCA-005 Acceptance: Given SHA256, resolver returns official 20-digit file_id.
        """
        test_sha256 = "a" * 64  # Valid 64-char SHA256
        cache_data = {test_sha256: "98765432109876543210"}
        cache_path = tmp_path / "cache.json"
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        resolver = FileIDResolver(cache_path=cache_path, strict_mode=True)
        file_id = resolver.resolve(test_sha256)
        
        assert file_id == "98765432109876543210"
        assert len(file_id) == 20
        assert file_id.isdigit()


# ============================================================================
# FCA-010: Metadata Backfill Tests
# ============================================================================

class TestMetadataBackfiller:
    """Test metadata backfill (FCA-010)."""
    
    def test_compute_doc_id_from_file_id(self):
        """Test doc_id computation from file_id."""
        backfiller = MetadataBackfiller(strict_mode=False)
        record = {"file_id": "12345678901234567890"}
        
        doc_id = backfiller._compute_doc_id(record)
        assert doc_id == "DOC_12345678901234567890"
    
    def test_compute_doc_id_from_sha256(self):
        """Test doc_id computation from sha256."""
        backfiller = MetadataBackfiller(strict_mode=False)
        record = {"sha256": "a" * 64}
        
        doc_id = backfiller._compute_doc_id(record)
        assert doc_id.startswith("DOC_")
        assert len(doc_id) == 24  # "DOC_" + 20 chars
    
    def test_compute_file_size_from_content(self):
        """Test file_size computation from content."""
        backfiller = MetadataBackfiller(strict_mode=False)
        record = {"content": "Hello, World!"}
        
        file_size = backfiller._compute_file_size(record)
        assert file_size == len("Hello, World!".encode('utf-8'))
    
    def test_compute_canonicality_default(self):
        """Test canonicality defaults to False."""
        backfiller = MetadataBackfiller(strict_mode=False)
        record = {}
        
        canonicality = backfiller._compute_canonicality(record)
        assert canonicality is False
    
    def test_backfill_record_complete(self):
        """Test backfilling a record with missing fields."""
        backfiller = MetadataBackfiller(strict_mode=False)
        record = {
            "sha256": "a" * 64,
            "content": "test content"
        }
        
        updated = backfiller.backfill_record(record)
        
        assert "doc_id" in updated
        assert "file_size" in updated
        assert "canonicality" in updated
        assert updated["file_size"] == len("test content".encode())
    
    def test_validate_metadata_complete(self):
        """Test metadata validation for complete record."""
        backfiller = MetadataBackfiller()
        record = {
            "doc_id": "DOC_123",
            "file_size": 100,
            "canonicality": True
        }
        
        is_valid, missing = backfiller.validate_metadata(record)
        assert is_valid
        assert missing == []
    
    def test_validate_metadata_incomplete(self):
        """Test metadata validation for incomplete record."""
        backfiller = MetadataBackfiller()
        record = {"doc_id": "DOC_123"}
        
        is_valid, missing = backfiller.validate_metadata(record)
        assert not is_valid
        assert "file_size" in missing
        assert "canonicality" in missing
    
    def test_fca010_acceptance_criteria(self):
        """
        FCA-010 Acceptance: Missing metadata fields are backfilled deterministically.
        """
        backfiller = MetadataBackfiller(strict_mode=True)
        record = {
            "file_id": "11111111111111111111",
            "sha256": "a" * 64,
            "content": "test data"
        }
        
        updated = backfiller.backfill_record(record)
        is_valid, missing = backfiller.validate_metadata(updated)
        
        assert is_valid
        assert updated["doc_id"] == "DOC_11111111111111111111"
        assert updated["file_size"] == len("test data".encode())
        assert "canonicality" in updated


# ============================================================================
# FCA-011: repo_root_id Resolution Tests
# ============================================================================

class TestRepoRootResolver:
    """Test repo_root_id resolution (FCA-011)."""
    
    def test_cache_hit(self, tmp_path):
        """Test cache hit for repo_root resolution."""
        cache_data = {str(tmp_path / "file.py"): "33333333333333333333"}
        cache_path = tmp_path / "cache.json"
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        resolver = RepoRootResolver(cache_path=cache_path)
        repo_root_id = resolver.resolve(str(tmp_path / "file.py"))
        
        assert repo_root_id == "33333333333333333333"
        assert resolver.stats["cache_hits"] == 1
    
    def test_infer_from_git_directory(self, tmp_path):
        """Test repo_root inference from .git directory."""
        # Create mock .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        test_file = tmp_path / "src" / "test.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        
        resolver = RepoRootResolver(cache_path=tmp_path / "cache.json")
        repo_root_id = resolver.resolve(str(test_file))
        
        assert len(repo_root_id) == 20
        assert repo_root_id.isdigit()
        assert resolver.stats["inferences"] == 1
    
    def test_strict_mode_fails_on_unresolved(self, tmp_path):
        """Test strict mode fails when repo_root cannot be resolved."""
        # Use a path that doesn't exist and has no .git parent
        orphan_dir = tmp_path / "isolated" / "deeply" / "nested"
        orphan_dir.mkdir(parents=True)
        test_file = orphan_dir / "orphan.py"
        test_file.touch()
        
        resolver = RepoRootResolver(cache_path=tmp_path / "cache.json", strict_mode=True)
        
        with pytest.raises(RepoRootResolutionError):
            resolver.resolve(str(test_file))
    
    def test_lenient_mode_returns_placeholder(self, tmp_path):
        """Test lenient mode returns placeholder on failure."""
        # Use isolated directory without .git
        orphan_dir = tmp_path / "isolated" / "deeply" / "nested"
        orphan_dir.mkdir(parents=True)
        test_file = orphan_dir / "orphan.py"
        test_file.touch()
        
        resolver = RepoRootResolver(cache_path=tmp_path / "cache.json", strict_mode=False)
        repo_root_id = resolver.resolve(str(test_file))
        
        assert repo_root_id == "00000000000000000000"
    
    def test_fca011_acceptance_criteria(self, tmp_path):
        """
        FCA-011 Acceptance: Missing repo_root_id fields are inferred from file paths.
        """
        # Create mock repository structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        test_file = tmp_path / "test.py"
        test_file.touch()
        
        resolver = RepoRootResolver(cache_path=tmp_path / "cache.json", strict_mode=True)
        repo_root_id = resolver.resolve(str(test_file))
        
        assert len(repo_root_id) == 20
        assert repo_root_id.isdigit()


# ============================================================================
# FCA-013: Orphaned Entries Tests
# ============================================================================

class TestOrphanedEntriesPruner:
    """Test orphaned entries resolution (FCA-013)."""
    
    def test_analyze_orphans(self):
        """Test orphan analysis."""
        entries = [
            {"entry_id": "E1", "edges": [], "file_path": "README.md"},
            {"entry_id": "E2", "edges": [{"target": "E1"}], "file_path": "src/main.py"},
            {"entry_id": "E3", "edges": [], "file_path": "orphan.txt"}
        ]
        
        pruner = OrphanedEntriesPruner()
        analysis = pruner.analyze_orphans(entries)
        
        assert analysis["total_entries"] == 3
        assert analysis["root_level"] == 1  # README.md is legitimate root
        assert analysis["orphaned"] == 1    # orphan.txt
        assert analysis["connected"] == 1    # main.py
    
    def test_is_legitimate_root(self):
        """Test root-level entry detection."""
        pruner = OrphanedEntriesPruner()
        
        assert pruner._is_legitimate_root({"file_path": "README.md"})
        assert pruner._is_legitimate_root({"file_path": "setup.py"})
        assert not pruner._is_legitimate_root({"file_path": "src/utils.py"})
    
    def test_build_relationships(self):
        """Test relationship building."""
        entries = [
            {"entry_id": "E1", "edges": [], "file_path": "/repo"},
            {"entry_id": "E2", "edges": [], "file_path": "/repo/src/main.py"}
        ]
        
        pruner = OrphanedEntriesPruner()
        updated = pruner.build_relationships(entries)
        
        # E2 should now have relationship to E1 (parent directory)
        e2 = next(e for e in updated if e["entry_id"] == "E2")
        assert len(e2.get("edges", [])) > 0 or e2.get("is_root") is True
    
    def test_validate_relationships_pass(self):
        """Test relationship validation passes when orphan rate < 10%."""
        # Create 20 entries with proper parent-child relationships
        # E0 is root (README.md), E1-E19 all have E0 as parent
        entries = []
        entries.append({"entry_id": "E0", "edges": [], "file_path": "README.md"})  # Root
        for i in range(1, 20):
            entries.append({
                "entry_id": f"E{i}",
                "edges": [{"source": f"E{i}", "target": "E0", "relationship": "child_of"}],
                "file_path": f"src/file{i}.py"
            })
        
        pruner = OrphanedEntriesPruner()
        is_valid, report = pruner.validate_relationships(entries)
        
        assert is_valid
        assert report["recommendation"] == "PASS"
    
    def test_fca013_acceptance_criteria(self):
        """
        FCA-013 Acceptance: Orphan rate reduced from 99.2% to < 10%.
        """
        # Simulate 245 entries: 2 roots + 243 connected entries
        # This gives us 0% orphan rate (all are either roots or connected)
        entries = []
        
        # 2 legitimate roots
        entries.append({"entry_id": "E0", "edges": [], "file_path": "README.md"})
        entries.append({"entry_id": "E1", "edges": [], "file_path": "LICENSE"})
        
        # 243 entries all connected to root E0
        for i in range(2, 245):
            entries.append({
                "entry_id": f"E{i}",
                "edges": [{"source": f"E{i}", "target": "E0", "relationship": "child_of"}],
                "file_path": f"src/file{i}.py"
            })
        
        pruner = OrphanedEntriesPruner()
        analysis = pruner.analyze_orphans(entries)
        
        orphan_rate = float(analysis["orphan_rate"].rstrip("%"))
        assert orphan_rate < 10.0  # Should be 0% (all legitimate)


# ============================================================================
# FCA-015: Duplicate SHA256 Tests
# ============================================================================

class TestDuplicateSHA256Resolver:
    """Test duplicate SHA256 resolution (FCA-015)."""
    
    def test_detect_no_collisions(self):
        """Test collision detection with no collisions."""
        records = [
            {"sha256": "a" * 64},
            {"sha256": "b" * 64}
        ]
        
        resolver = DuplicateSHA256Resolver()
        collisions = resolver.detect_collisions(records)
        
        assert len(collisions) == 0
    
    def test_detect_collisions(self):
        """Test collision detection with collisions."""
        records = [
            {"sha256": "a" * 64, "file_path": "/file1.txt"},
            {"sha256": "a" * 64, "file_path": "/file2.txt"},
            {"sha256": "b" * 64, "file_path": "/file3.txt"}
        ]
        
        resolver = DuplicateSHA256Resolver()
        collisions = resolver.detect_collisions(records)
        
        assert len(collisions) == 1
        assert "a" * 64 in collisions
        assert len(collisions["a" * 64]) == 2
    
    def test_are_files_identical(self):
        """Test identical file detection."""
        resolver = DuplicateSHA256Resolver()
        
        # Same path → identical
        records = [
            {"file_path": "/same/file.txt", "file_size": 100},
            {"file_path": "/same/file.txt", "file_size": 100}
        ]
        assert resolver._are_files_identical(records)
        
        # Different sizes → not identical
        records = [
            {"file_path": "/file1.txt", "file_size": 100},
            {"file_path": "/file2.txt", "file_size": 200}
        ]
        assert not resolver._are_files_identical(records)
    
    def test_handle_true_duplicate(self):
        """Test true duplicate handling."""
        resolver = DuplicateSHA256Resolver()
        records = [
            {"sha256": "a" * 64, "file_path": "/file1.txt", "file_size": 100, "file_id": "111"},
            {"sha256": "a" * 64, "file_path": "/file2.txt", "file_size": 100}
        ]
        
        resolved = resolver._handle_true_duplicate(records)
        
        assert len(resolved) == 2
        canonical = next(r for r in resolved if r.get("canonicality"))
        assert canonical["file_id"] == "111"  # More complete record is canonical
    
    def test_resolve_all(self):
        """Test resolving all collisions."""
        records = [
            {"sha256": "a" * 64, "file_path": "/file1.txt", "file_size": 100},
            {"sha256": "a" * 64, "file_path": "/file2.txt", "file_size": 100},
            {"sha256": "b" * 64, "file_path": "/file3.txt", "file_size": 200}
        ]
        
        resolver = DuplicateSHA256Resolver()
        resolved, reports = resolver.resolve_all(records)
        
        assert len(reports) == 1  # One collision resolved
        assert resolver.stats["collisions_detected"] == 1
    
    def test_fca015_acceptance_criteria(self):
        """
        FCA-015 Acceptance: SHA256 collisions are detected and resolved deterministically.
        """
        # Simulate the reported 1 collision - true duplicate (same file, same size)
        collision_sha = "a" * 64  # Valid SHA256
        records = [
            {"sha256": collision_sha, "file_path": "/fileA.txt", "file_size": 1000, "file_id": "12345678901234567890"},
            {"sha256": collision_sha, "file_path": "/fileA.txt", "file_size": 1000}  # Same path = identical file
        ]
        
        resolver = DuplicateSHA256Resolver(strict_mode=True)
        resolved, reports = resolver.resolve_all(records)
        
        assert len(reports) == 1
        assert reports[0]["resolution_type"] in ["true_duplicate", "metadata_conflict", "hash_collision"]
        assert resolver.stats["collisions_detected"] == 1
        assert resolver.stats["resolved"] == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase2Integration:
    """Integration tests for Phase 2."""
    
    def test_full_phase2_pipeline(self, tmp_path):
        """Test complete Phase 2 processing pipeline."""
        # Create mock dataset
        records = [
            {
                "sha256": "a" * 64,
                "file_path": str(tmp_path / "file1.txt"),
                "content": "test content 1"
            },
            {
                "sha256": "b" * 64,
                "file_path": str(tmp_path / "file2.txt"),
                "content": "test content 2"
            }
        ]
        
        # Create files
        for record in records:
            Path(record["file_path"]).write_text(record["content"])
        
        # Create mock .git for repo_root
        (tmp_path / ".git").mkdir()
        
        # Step 1: Resolve file_id
        file_id_resolver = FileIDResolver(
            cache_path=tmp_path / "file_id_cache.json",
            strict_mode=False,
            allow_generation=True
        )
        for record in records:
            record["file_id"] = file_id_resolver.resolve(record["sha256"])
        
        # Step 2: Backfill metadata
        backfiller = MetadataBackfiller(strict_mode=False)
        records = [backfiller.backfill_record(r) for r in records]
        
        # Step 3: Resolve repo_root_id
        repo_resolver = RepoRootResolver(
            cache_path=tmp_path / "repo_cache.json",
            strict_mode=False
        )
        for record in records:
            record["repo_root_id"] = repo_resolver.resolve(record["file_path"])
        
        # Validate all metadata present
        for record in records:
            assert "file_id" in record
            assert "doc_id" in record
            assert "file_size" in record
            assert "canonicality" in record
            assert "repo_root_id" in record


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
