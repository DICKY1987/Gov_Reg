#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-MERGE-FILE-CLASSIFIER-PY-001
"""
MERGE-008: Merge File Classifier

Classifies files into categories for conflict resolution strategy.
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-MERGE-FILE-CLASSIFIER-PY-001

import json
import yaml
from pathlib import Path
from fnmatch import fnmatch
from datetime import datetime
import argparse


DEFAULT_RULES = {
    'generated': [
        '**/gen_*', '**/*_generated.*', '**/*.pyc',
        '**/__pycache__/**', '**/build/**', '**/dist/**',
        '**/.pytest_cache/**', '**/*.egg-info/**'
    ],
    'binary': [
        '**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.gif',
        '**/*.pdf', '**/*.zip', '**/*.tar.gz',
        '**/*.exe', '**/*.dll', '**/*.so', '**/*.dylib'
    ],
    'human_text': [
        '**/*.py', '**/*.md', '**/*.txt', '**/*.rst',
        '**/*.yaml', '**/*.yml', '**/*.json',
        '**/*.js', '**/*.ts', '**/*.jsx', '**/*.tsx'
    ],
    'config_sensitive': [
        '**/.gitignore', '**/.gitattributes', '**/.env*',
        '**/config/*.yaml', '**/config/*.yml',
        '**/schema/**', '**/*.json', '**/pyproject.toml',
        '**/setup.py', '**/requirements.txt'
    ],
    'do_not_merge': [
        '**/.git/**', '**/node_modules/**', '**/.venv/**',
        '**/venv/**', '**/__pycache__/**'
    ]
}


def classify_single_file(file_path, rules):
    """Classify a single file by matching against rules."""
    file_str = str(file_path).replace('\\', '/')

    for class_name, patterns in rules.items():
        for pattern in patterns:
            if fnmatch(file_str, pattern):
                return class_name

    return 'unknown'


def classify_files(work_dir, policy_path=None):
    """Classify all files in repository."""

    rules = DEFAULT_RULES.copy()

    # Load custom policy if provided
    if policy_path and Path(policy_path).exists():
        print(f"📖 Loading custom policy: {policy_path}")
        with open(policy_path) as f:
            custom_policy = yaml.safe_load(f)
            if 'file_classes' in custom_policy:
                rules.update(custom_policy['file_classes'])

    # Classify all files
    work_path = Path(work_dir).resolve()
    classifications = {}
    class_counts = {class_name: 0 for class_name in rules.keys()}
    class_counts['unknown'] = 0

    print(f"🔍 Classifying files in: {work_path}")

    for file_path in work_path.rglob('*'):
        if not file_path.is_file():
            continue

        # Skip .git directory
        if '.git' in file_path.parts:
            continue

        rel_path = file_path.relative_to(work_path)
        file_class = classify_single_file(rel_path, rules)

        classifications[str(rel_path)] = file_class
        class_counts[file_class] += 1

    # Generate output
    output = {
        'pattern_id': 'MERGE-008',
        'timestamp': datetime.now().isoformat(),
        'work_dir': str(work_path),
        'rules': rules,
        'classifications': classifications,
        'summary': class_counts,
        'timestamp_safe_classes': ['generated', 'binary'],
        'never_timestamp_classes': ['human_text', 'config_sensitive']
    }

    return output


def main():
    parser = argparse.ArgumentParser(description='MERGE-008: Merge File Classifier')
    parser.add_argument('work_dir', nargs='?', default='.', help='Repository root')
    parser.add_argument('--policy', help='Path to custom merge_policy.yaml')
    parser.add_argument('--output', default='merge_file_classes.json', help='Output file')

    args = parser.parse_args()

    output = classify_files(args.work_dir, args.policy)

    # Save JSON
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Classifications saved: {args.output}")
    print(f"\n📊 Summary:")
    for class_name, count in output['summary'].items():
        if count > 0:
            icon = "📝" if class_name == 'human_text' else \
                   "🤖" if class_name == 'generated' else \
                   "📦" if class_name == 'binary' else \
                   "⚙️" if class_name == 'config_sensitive' else \
                   "🚫" if class_name == 'do_not_merge' else "❓"
            print(f"   {icon} {class_name}: {count} files")

    return 0


if __name__ == '__main__':
    exit(main())
