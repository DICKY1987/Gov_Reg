"""
Validate imports from modules_to_import.json.
"""
import json
import sys
import importlib
from pathlib import Path
from datetime import datetime


def validate_imports(modules_json_path, output_path, pythonpath_root=None):
    """
    Test imports of all modules from modules_to_import.json.

    Args:
        modules_json_path: Path to modules_to_import.json
        output_path: Where to save validation results
        pythonpath_root: Optional root to add to sys.path
    """
    # Setup PYTHONPATH if provided
    if pythonpath_root:
        pythonpath_root = str(Path(pythonpath_root).resolve())
        if pythonpath_root not in sys.path:
            sys.path.insert(0, pythonpath_root)
            print(f"Added to PYTHONPATH: {pythonpath_root}")

    # Load modules to test
    with open(modules_json_path, 'r', encoding='utf-8') as f:
        modules_data = json.load(f)

    modules = modules_data.get('modules', [])

    print(f"Testing {len(modules)} module imports...")

    results = []
    success_count = 0
    failure_count = 0

    for i, module_info in enumerate(modules, 1):
        module_name = module_info['module']

        try:
            # Clear module from cache if already imported
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Try to import
            importlib.import_module(module_name)

            results.append({
                'order': i,
                'module': module_name,
                'file': module_info.get('file'),
                'status': 'SUCCESS',
                'error': None
            })
            success_count += 1
            print(f"  [{i}/{len(modules)}] ✓ {module_name}")

        except Exception as e:
            results.append({
                'order': i,
                'module': module_name,
                'file': module_info.get('file'),
                'status': 'FAILED',
                'error': str(e)
            })
            failure_count += 1
            print(f"  [{i}/{len(modules)}] ✗ {module_name}: {e}")

    # Calculate success rate
    success_rate = (success_count / len(modules) * 100) if modules else 0

    result = {
        'results': results,
        'summary': {
            'total_modules': len(modules),
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': success_rate
        },
        'all_passed': failure_count == 0,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Import Validation Results:")
    print(f"  Total: {len(modules)}")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failure_count}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"{'='*60}")

    if failure_count > 0:
        print("\n⚠ Import validation FAILED - see details above")
        return False
    else:
        print("\n✓ All imports validated successfully")
        return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate module imports')
    parser.add_argument('--modules', default='.migration/mapping/modules_to_import.json',
                        help='Path to modules_to_import.json')
    parser.add_argument('--output', default='.migration/reports/IMPORT_VALIDATION.json',
                        help='Output path for validation results')
    parser.add_argument('--pythonpath', default='C:\\Users\\richg\\Gov_Reg',
                        help='Root directory to add to PYTHONPATH')

    args = parser.parse_args()

    success = validate_imports(args.modules, args.output, args.pythonpath)
    sys.exit(0 if success else 1)
