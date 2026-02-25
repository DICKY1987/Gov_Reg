#!/usr/bin/env python3
"""
Governance Registry CLI Application
FILE_ID: P_01999000042260124015

Usage:
    python P_01999000042260124015_govreg.py scan [--write] [--schema PATH]
    python P_01999000042260124015_govreg.py validate [--schema PATH]
    python P_01999000042260124015_govreg.py report [--output PATH]

Commands:
    scan        Scan repository for governance artifacts and update registry
    validate    Validate registry against schema and check completeness
    report      Generate REGISTRY_REPORT.md with status and drift analysis
"""

import sys
import argparse
import importlib.util
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import modules using importlib to handle numeric prefixes
def import_module_from_file(module_name, file_path):
    """Import a module from a file path, handling numeric prefixes"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Get paths to module files
script_dir = Path(__file__).parent
core_dir = script_dir.parent.parent.parent.parent / "01260207201000001173_govreg_core"

# Import modules with ID-prefixed filenames (P_ prefix for Python files)
scanner_mod = import_module_from_file("scanner", Path(__file__).parent / "P_01999000042260124023_scanner.py")
validator_mod = import_module_from_file("validator", core_dir / "P_01999000042260124024_validator.py")
reporter_mod = import_module_from_file("reporter", core_dir / "P_01999000042260124022_reporter.py")
config_mod = import_module_from_file("config", core_dir / "P_01999000042260124021_config.py")

# Extract classes and functions
RegistryScanner = scanner_mod.RegistryScanner
RegistryValidator = validator_mod.RegistryValidator
RegistryReporter = reporter_mod.RegistryReporter
load_repo_roots = config_mod.load_repo_roots
load_registry = config_mod.load_registry


def main():
    parser = argparse.ArgumentParser(
        description="Governance Registry CLI - Manage governance artifact registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan and auto-update registry
  python govreg.py scan --write

  # Validate registry with custom schema
  python govreg.py validate --schema ./custom_schema.json

  # Generate report
  python govreg.py report
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan repository for governance artifacts')
    scan_parser.add_argument('--write', action='store_true', 
                            help='Write discovered changes to registry file')
    scan_parser.add_argument('--schema', type=str, 
                            default='01999000042260124012_governance_registry_schema.v3.json',
                            help='Path to schema file')
    scan_parser.add_argument('--registry', type=str,
                            default='01999000042260124008_governance_registry.json',
                            help='Path to registry file')
    scan_parser.add_argument('--repo-roots', type=str,
                            default='01999000042260124019_repo_roots.json',
                            help='Path to repo roots config')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate registry')
    validate_parser.add_argument('--schema', type=str,
                                default='01999000042260124012_governance_registry_schema.v3.json',
                                help='Path to schema file')
    validate_parser.add_argument('--registry', type=str,
                                default='01999000042260124008_governance_registry.json',
                                help='Path to registry file')
    validate_parser.add_argument('--repo-roots', type=str,
                                default='01999000042260124019_repo_roots.json',
                                help='Path to repo roots config')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate registry report')
    report_parser.add_argument('--output', type=str,
                              default='REGISTRY_REPORT.md',
                              help='Output report file')
    report_parser.add_argument('--registry', type=str,
                              default='01999000042260124008_governance_registry.json',
                              help='Path to registry file')
    report_parser.add_argument('--repo-roots', type=str,
                              default='01999000042260124019_repo_roots.json',
                              help='Path to repo roots config')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Make paths absolute based on script location
        script_dir = Path(__file__).parent
        
        if args.command == 'scan':
            schema_path = (script_dir / args.schema).resolve()
            registry_path = (script_dir / args.registry).resolve()
            repo_roots_path = (script_dir / args.repo_roots).resolve()
            
            print(f"Scanning for governance artifacts...")
            print(f"  Registry: {registry_path}")
            print(f"  Schema: {schema_path}")
            print(f"  Repo Roots: {repo_roots_path}")
            
            scanner = RegistryScanner(
                registry_path=str(registry_path),
                schema_path=str(schema_path),
                repo_roots_path=str(repo_roots_path)
            )
            
            results = scanner.scan()
            
            print(f"\n✓ Scan complete")
            print(f"  Files found: {results['files_found']}")
            print(f"  New entries: {results['new_entries']}")
            print(f"  Updated entries: {results['updated_entries']}")
            print(f"  Orphaned entries: {results['orphaned_entries']}")
            
            if args.write and (results['new_entries'] > 0 or results['updated_entries'] > 0):
                scanner.save_registry()
                print(f"\n✓ Registry saved to: {registry_path}")
            elif not args.write and (results['new_entries'] > 0 or results['updated_entries'] > 0):
                print(f"\n⚠ Changes detected but not written (use --write to save)")
            
            return 0 if results['orphaned_entries'] == 0 else 1
            
        elif args.command == 'validate':
            schema_path = (script_dir / args.schema).resolve()
            registry_path = (script_dir / args.registry).resolve()
            repo_roots_path = (script_dir / args.repo_roots).resolve()
            
            print(f"Validating governance registry...")
            print(f"  Registry: {registry_path}")
            print(f"  Schema: {schema_path}")
            print(f"  Repo Roots: {repo_roots_path}")
            
            validator = RegistryValidator(
                registry_path=str(registry_path),
                schema_path=str(schema_path),
                repo_roots_path=str(repo_roots_path)
            )
            
            results = validator.validate()
            
            print(f"\n{'='*80}")
            print(f"VALIDATION CHECKLIST")
            print(f"{'='*80}")
            
            for check in results['checklist']:
                status_icon = '✓' if check['status'] == 'PASS' else '✗'
                print(f"{status_icon} {check['name']}: {check['status']}")
                if check['status'] != 'PASS' and check.get('details'):
                    print(f"  {check['details']}")
            
            print(f"{'='*80}\n")
            
            if results['errors']:
                print(f"Errors ({len(results['errors'])}):")
                for error in results['errors']:
                    print(f"  • {error}")
                print()
            
            if results['warnings']:
                print(f"Warnings ({len(results['warnings'])}):")
                for warning in results['warnings']:
                    print(f"  • {warning}")
                print()
            
            return 0 if results['valid'] else 1
            
        elif args.command == 'report':
            registry_path = (script_dir / args.registry).resolve()
            repo_roots_path = (script_dir / args.repo_roots).resolve()
            output_path = (script_dir / args.output).resolve()
            
            print(f"Generating registry report...")
            print(f"  Registry: {registry_path}")
            print(f"  Output: {output_path}")
            
            reporter = RegistryReporter(
                registry_path=str(registry_path),
                repo_roots_path=str(repo_roots_path)
            )
            
            report_md = reporter.generate_report()
            
            output_path.write_text(report_md, encoding='utf-8')
            
            print(f"\n✓ Report saved to: {output_path}")
            
            return 0
            
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
