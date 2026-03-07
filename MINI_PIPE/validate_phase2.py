#!/usr/bin/env python3
"""Phase 2 Core Functionality Validation Script

Validates that Phase 2 components are properly installed and configured.
"""

import sys
from pathlib import Path
from typing import List, Tuple

def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists"""
    if path.exists():
        return True, f'✓ {description}'
    return False, f'✗ {description} - NOT FOUND: {path}'

def check_import(module: str, description: str) -> Tuple[bool, str]:
    """Check if a Python module can be imported"""
    try:
        __import__(module)
        return True, f'✓ {description}'
    except ImportError as e:
        return False, f'✗ {description} - IMPORT ERROR: {e}'

def check_ai_providers() -> List[Tuple[bool, str]]:
    """Check AI provider availability"""
    results = []
    
    # Check GitHub Copilot CLI
    import subprocess
    try:
        result = subprocess.run(
            ["gh", "copilot", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            results.append((True, '✓ GitHub Copilot CLI available'))
        else:
            results.append((False, '⚠️  GitHub Copilot CLI not configured'))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results.append((False, '⚠️  GitHub Copilot CLI not installed'))
    
    # Check OpenAI
    try:
        import openai
        import os
        if os.getenv("OPENAI_API_KEY"):
            results.append((True, '✓ OpenAI API key configured'))
        else:
            results.append((False, '⚠️  OpenAI API key not set (optional)'))
    except ImportError:
        results.append((False, '⚠️  openai package not installed (optional)'))
    
    # Check Anthropic
    try:
        import anthropic
        import os
        if os.getenv("ANTHROPIC_API_KEY"):
            results.append((True, '✓ Anthropic API key configured'))
        else:
            results.append((False, '⚠️  Anthropic API key not set (optional)'))
    except ImportError:
        results.append((False, '⚠️  anthropic package not installed (optional)'))
    
    return results

def validate_phase2() -> List[Tuple[bool, str]]:
    """Run all Phase 2 validation checks"""
    results = []
    base_dir = Path(__file__).parent
    
    # Check Phase 1 components still present
    results.append(check_file_exists(
        base_dir / '.github' / 'workflows' / 'acms-pipeline.yml',
        'Phase 1: ACMS Pipeline workflow'
    ))
    results.append(check_file_exists(
        base_dir / 'src' / 'acms' / 'notifications.py',
        'Phase 1: Notification system'
    ))
    results.append(check_file_exists(
        base_dir / 'src' / 'acms' / 'monitoring.py',
        'Phase 1: Monitoring system'
    ))
    
    # Check Phase 2 components
    results.append(check_file_exists(
        base_dir / 'src' / 'acms' / 'real_minipipe_adapter.py',
        'Phase 2: Real MINI_PIPE adapter'
    ))
    results.append(check_import(
        'src.acms.real_minipipe_adapter',
        'Phase 2: Real adapter import'
    ))
    results.append(check_file_exists(
        base_dir / 'docs' / 'PHASE2_CORE_FUNCTIONALITY.md',
        'Phase 2: Documentation'
    ))
    
    # Check AI adapter enhancements
    try:
        with open(base_dir / 'src' / 'acms' / 'ai_adapter.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            has_openai = '_try_openai_api' in content
            has_anthropic = '_try_anthropic_api' in content
            has_cascade = '_try_gh_copilot_cli' in content
            
            if has_openai and has_anthropic and has_cascade:
                results.append((True, '✓ AI adapter multi-provider support'))
            else:
                results.append((False, '✗ AI adapter missing provider methods'))
    except Exception as e:
        results.append((False, f'✗ AI adapter check failed: {e}'))
    
    # Check controller defaults updated
    try:
        with open(base_dir / 'src' / 'acms' / 'controller.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            has_auto_default = 'ai_adapter_type: str = "auto"' in content
            
            if has_auto_default:
                results.append((True, '✓ Controller defaults to auto (real AI)'))
            else:
                results.append((False, '⚠️  Controller still defaults to mock'))
    except Exception as e:
        results.append((False, f'✗ Controller check failed: {e}'))
    
    # Check orchestrator availability
    results.append(check_file_exists(
        base_dir / 'src' / 'minipipe' / 'orchestrator.py',
        'Orchestrator module available'
    ))
    results.append(check_import(
        'src.minipipe.orchestrator',
        'Orchestrator import'
    ))
    
    # Check AI providers
    provider_results = check_ai_providers()
    results.extend(provider_results)
    
    return results

def main():
    """Main validation entry point"""
    print('='*70)
    print('PHASE 2 CORE FUNCTIONALITY VALIDATION')
    print('='*70)
    print()
    
    results = validate_phase2()
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    warnings = sum(1 for success, msg in results if not success and '⚠️' in msg)
    errors = sum(1 for success, msg in results if not success and '✗' in msg)
    
    for success, message in results:
        print(message)
    
    print()
    print('='*70)
    print(f'RESULTS: {passed}/{total} checks passed')
    if warnings > 0:
        print(f'WARNINGS: {warnings} (optional components)')
    if errors > 0:
        print(f'ERRORS: {errors} (required components)')
    print('='*70)
    
    # Define required checks (errors only, warnings are optional)
    required_pass = total - warnings
    actual_pass = passed + warnings
    
    if actual_pass >= required_pass:
        print()
        print('✅ Phase 2 core components validated successfully!')
        print()
        print('AI Provider Status:')
        print('  At least one AI provider should be configured for production use.')
        print('  Mock fallback will be used if no providers available.')
        print()
        print('Next steps:')
        print('  1. Configure AI provider (optional but recommended):')
        print('     - GitHub Copilot: gh extension install github/gh-copilot')
        print('     - OpenAI: export OPENAI_API_KEY="sk-..."')
        print('     - Anthropic: export ANTHROPIC_API_KEY="sk-ant-..."')
        print('  2. Test execution: python acms_controller.py . --mode analyze_only')
        print('  3. Verify real adapter used (check output for "✓ Using...")')
        print()
        return 0
    else:
        print()
        print('❌ Some Phase 2 required components are missing.')
        print('Please review the errors above and fix any issues.')
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
