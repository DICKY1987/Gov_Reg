"""Registry reporter for generating human-readable reports
FILE_ID: P_01999000042260124022
"""
from datetime import datetime
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Import config module with P_ prefix
def _import_config():
    config_path = Path(__file__).parent / "P_01999000042260124021_config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_config = _import_config()
load_repo_roots = _config.load_repo_roots
load_registry = _config.load_registry
resolve_path = _config.resolve_path


class RegistryReporter:
    """Generates human-readable reports from the governance registry"""
    
    def __init__(self, registry_path: str, repo_roots_path: str):
        self.registry_path = registry_path
        self.repo_roots_path = repo_roots_path
        
        # Load data
        self.repo_roots = load_repo_roots(repo_roots_path)
        self.registry = load_registry(registry_path)
    
    def generate_report(self) -> str:
        """Generate complete registry report in Markdown"""
        sections = []
        
        sections.append(self._generate_header())
        sections.append(self._generate_executive_summary())
        sections.append(self._generate_domain_breakdown())
        sections.append(self._generate_drift_analysis())
        sections.append(self._generate_file_listing())
        sections.append(self._generate_edges_summary())
        
        return '\n\n'.join(sections)
    
    def _generate_header(self) -> str:
        """Generate report header"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        return f"""# Governance Registry Report

**Generated:** {timestamp}  
**Registry:** `{self.registry_path}`  
**Schema Version:** {self.registry.get('schema_version', 'unknown')}

---
"""
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary"""
        files = self.registry.get('files', [])
        edges = self.registry.get('edges', [])
        
        # Count by domain
        domains = defaultdict(int)
        for f in files:
            domains[f.get('governance_domain', 'UNKNOWN')] += 1
        
        # Count by artifact kind
        kinds = defaultdict(int)
        for f in files:
            kinds[f.get('artifact_kind', 'UNKNOWN')] += 1
        
        # Count canonical vs others
        canonicals = sum(1 for f in files if f.get('canonicality') == 'CANONICAL')
        alternates = sum(1 for f in files if f.get('canonicality') == 'ALTERNATE')
        legacy = sum(1 for f in files if f.get('canonicality') == 'LEGACY')
        
        report = [
            "## Executive Summary",
            "",
            f"**Total Files:** {len(files)}  ",
            f"**Total Edges:** {len(edges)}  ",
            f"**Canonical Files:** {canonicals}  ",
            f"**Alternate Files:** {alternates}  ",
            f"**Legacy Files:** {legacy}  ",
            "",
            "### By Domain",
            ""
        ]
        
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{domain}:** {count}")
        
        report.extend([
            "",
            "### By Artifact Kind",
            ""
        ])
        
        for kind, count in sorted(kinds.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{kind}:** {count}")
        
        return '\n'.join(report)
    
    def _generate_domain_breakdown(self) -> str:
        """Generate detailed breakdown by domain"""
        files = self.registry.get('files', [])
        
        # Group by domain
        by_domain = defaultdict(list)
        for f in files:
            domain = f.get('governance_domain', 'UNKNOWN')
            by_domain[domain].append(f)
        
        report = [
            "## Domain Breakdown",
            ""
        ]
        
        for domain in sorted(by_domain.keys()):
            domain_files = by_domain[domain]
            report.extend([
                f"### {domain} ({len(domain_files)} files)",
                ""
            ])
            
            # Group by artifact kind within domain
            by_kind = defaultdict(list)
            for f in domain_files:
                kind = f.get('artifact_kind', 'UNKNOWN')
                by_kind[kind].append(f)
            
            for kind in sorted(by_kind.keys()):
                kind_files = by_kind[kind]
                report.append(f"**{kind}** ({len(kind_files)}):")
                report.append("")
                
                for f in kind_files[:10]:  # Limit to first 10
                    file_id = f.get('file_id', 'N/A')
                    path = f.get('relative_path', 'N/A')
                    canon = f.get('canonicality', 'CANONICAL')
                    purpose = f.get('one_line_purpose', '')
                    
                    if purpose:
                        report.append(f"- `{file_id}` - {path} - {purpose}")
                    else:
                        report.append(f"- `{file_id}` - {path} [{canon}]")
                
                if len(kind_files) > 10:
                    report.append(f"- *(and {len(kind_files) - 10} more...)*")
                
                report.append("")
        
        return '\n'.join(report)
    
    def _generate_drift_analysis(self) -> str:
        """Generate drift analysis section"""
        files = self.registry.get('files', [])
        
        # Check for files missing on disk
        missing_files = []
        for f in files:
            if f.get('is_directory', False):
                continue
            
            relative_path = f.get('relative_path')
            repo_root_id = f.get('repo_root_id')
            
            abs_path = resolve_path(relative_path, repo_root_id, self.repo_roots)
            if abs_path and not abs_path.exists():
                missing_files.append(f)
        
        report = [
            "## Drift Analysis",
            ""
        ]
        
        if missing_files:
            report.extend([
                f"⚠ **{len(missing_files)} file(s) in registry not found on disk:**",
                ""
            ])
            for f in missing_files[:20]:
                file_id = f.get('file_id', 'N/A')
                path = f.get('relative_path', 'N/A')
                report.append(f"- `{file_id}` - {path}")
            
            if len(missing_files) > 20:
                report.append(f"- *(and {len(missing_files) - 20} more...)*")
        else:
            report.append("✓ All registry entries point to existing files")
        
        return '\n'.join(report)
    
    def _generate_file_listing(self) -> str:
        """Generate complete file listing"""
        files = self.registry.get('files', [])
        
        report = [
            "## Complete File Listing",
            "",
            "| File ID | Path | Domain | Kind | Canonical |",
            "|---------|------|--------|------|-----------|"
        ]
        
        for f in files[:50]:  # Limit to first 50
            file_id = f.get('file_id', 'N/A')
            path = f.get('relative_path', 'N/A')
            domain = f.get('governance_domain', 'N/A')
            kind = f.get('artifact_kind', 'N/A')
            canon = f.get('canonicality', 'CANONICAL')
            
            # Truncate long paths
            if len(path) > 40:
                path = '...' + path[-37:]
            
            report.append(f"| `{file_id[-8:]}` | `{path}` | {domain} | {kind} | {canon} |")
        
        if len(files) > 50:
            report.append("")
            report.append(f"*(Showing 50 of {len(files)} files)*")
        
        return '\n'.join(report)
    
    def _generate_edges_summary(self) -> str:
        """Generate edges summary"""
        edges = self.registry.get('edges', [])
        
        report = [
            "## Relationships (Edges)",
            ""
        ]
        
        if not edges:
            report.append("*No edges defined in registry*")
            return '\n'.join(report)
        
        # Group by edge type
        by_type = defaultdict(list)
        for e in edges:
            edge_type = e.get('edge_type', 'UNKNOWN')
            by_type[edge_type].append(e)
        
        for edge_type in sorted(by_type.keys()):
            type_edges = by_type[edge_type]
            report.extend([
                f"### {edge_type} ({len(type_edges)})",
                ""
            ])
            
            for e in type_edges[:10]:
                source = e.get('source_file_id', 'N/A')
                target = e.get('target_file_id') or e.get('target_schema_id', 'N/A')
                evidence = e.get('evidence', {})
                ev_type = evidence.get('evidence_type', 'N/A')
                
                report.append(f"- `{source[-8:]}` → `{target[-8:]}` (via {ev_type})")
            
            if len(type_edges) > 10:
                report.append(f"- *(and {len(type_edges) - 10} more...)*")
            
            report.append("")
        
        return '\n'.join(report)
