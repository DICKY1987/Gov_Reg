"""B4: package - Bundle Phase B artifacts into deployable archive"""

import tarfile
import zipfile
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from .base import BaseCommand


class PackageCommand(BaseCommand):
    """Bundle all Phase B artifacts into deployable archive"""
    
    def execute(self) -> int:
        """Execute packaging"""
        self.logger.info(f"Packaging Phase B run: {self.phase_b_run_id}")
        
        compile_dir = self.phase_b_dir / "compile"
        
        # G20: Check required artifacts exist
        required_artifacts = [
            "execution_plan.json",
            "execution_manifest.json",
            "execution_policy_snapshot.json",
            "rollback_plan.json"
        ]
        
        for artifact in required_artifacts:
            artifact_path = compile_dir / artifact
            if not artifact_path.exists():
                self.logger.error(f"Required artifact missing: {artifact}")
                return 10
        
        # Check test harness
        harness_sh = compile_dir / "test_harness.sh"
        harness_py = compile_dir / "test_harness.py"
        if not harness_sh.exists() and not harness_py.exists():
            self.logger.error("Test harness missing")
            return 10
        
        # Determine output path
        package_dir = self.phase_b_dir / "package"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        if self.args.out_path:
            archive_path = self.args.out_path
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            ext = self.args.archive_format
            archive_path = package_dir / f"phase_b_execution_package_{timestamp}.{ext}"
        
        # Create archive
        if self.args.archive_format == "tar.gz":
            self._create_tarball(archive_path, compile_dir)
        else:
            self._create_zip(archive_path, compile_dir)
        
        # G21: Record archive hash
        archive_hash = self._hash_file(archive_path)
        envelope_path = Path(str(archive_path) + ".envelope.json")
        self.write_json(envelope_path, {
            "artifact_path": str(archive_path.relative_to(self.phase_a_dir)),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256": archive_hash
        })
        
        self.logger.info(f"Package created: {archive_path}")
        self.logger.info(f"SHA-256: {archive_hash}")
        
        print(f"✓ Package: {archive_path}")
        print(f"  SHA-256: {archive_hash}")
        
        return 0
    
    def _create_tarball(self, output_path: Path, compile_dir: Path):
        """Create tar.gz archive"""
        manifest_lines = []
        
        with tarfile.open(output_path, "w:gz") as tar:
            # Add compile artifacts
            for item in compile_dir.rglob("*"):
                if item.is_file() and ".envelope.json" not in item.name:
                    arcname = item.relative_to(compile_dir)
                    tar.add(item, arcname=arcname)
                    
                    file_hash = self._hash_file(item)
                    manifest_lines.append(f"{file_hash}  {arcname}")
            
            # Add preview if exists
            preview_dir = self.phase_b_dir / "preview"
            if preview_dir.exists():
                for item in preview_dir.rglob("*"):
                    if item.is_file():
                        arcname = Path("preview") / item.relative_to(preview_dir)
                        tar.add(item, arcname=arcname)
                        
                        file_hash = self._hash_file(item)
                        manifest_lines.append(f"{file_hash}  {arcname}")
            
            # Add lineage if requested
            if self.args.include_lineage:
                lineage_artifacts = [
                    "init/planning_policy_snapshot.json",
                    "loop/refinement_termination_record.json"
                ]
                
                for artifact in lineage_artifacts:
                    artifact_path = self.phase_a_artifacts / artifact
                    if artifact_path.exists():
                        arcname = Path("lineage") / artifact_path.name
                        tar.add(artifact_path, arcname=arcname)
                        
                        file_hash = self._hash_file(artifact_path)
                        manifest_lines.append(f"{file_hash}  {arcname}")
            
            # Add MANIFEST.txt
            manifest_content = "\n".join(sorted(manifest_lines))
            import io
            manifest_bytes = manifest_content.encode("utf-8")
            info = tarfile.TarInfo(name="MANIFEST.txt")
            info.size = len(manifest_bytes)
            tar.addfile(info, io.BytesIO(manifest_bytes))
    
    def _create_zip(self, output_path: Path, compile_dir: Path):
        """Create zip archive"""
        manifest_lines = []
        
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add compile artifacts
            for item in compile_dir.rglob("*"):
                if item.is_file() and ".envelope.json" not in item.name:
                    arcname = item.relative_to(compile_dir)
                    zf.write(item, arcname=arcname)
                    
                    file_hash = self._hash_file(item)
                    manifest_lines.append(f"{file_hash}  {arcname}")
            
            # Add preview if exists
            preview_dir = self.phase_b_dir / "preview"
            if preview_dir.exists():
                for item in preview_dir.rglob("*"):
                    if item.is_file():
                        arcname = Path("preview") / item.relative_to(preview_dir)
                        zf.write(item, arcname=arcname)
                        
                        file_hash = self._hash_file(item)
                        manifest_lines.append(f"{file_hash}  {arcname}")
            
            # Add lineage if requested
            if self.args.include_lineage:
                lineage_artifacts = [
                    "init/planning_policy_snapshot.json",
                    "loop/refinement_termination_record.json"
                ]
                
                for artifact in lineage_artifacts:
                    artifact_path = self.phase_a_artifacts / artifact
                    if artifact_path.exists():
                        arcname = Path("lineage") / artifact_path.name
                        zf.write(artifact_path, arcname=arcname)
                        
                        file_hash = self._hash_file(artifact_path)
                        manifest_lines.append(f"{file_hash}  {arcname}")
            
            # Add MANIFEST.txt
            manifest_content = "\n".join(sorted(manifest_lines))
            zf.writestr("MANIFEST.txt", manifest_content)
    
    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
