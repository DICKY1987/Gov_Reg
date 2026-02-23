#!/usr/bin/env python3
"""
File Creator - Create files with auto-ID assignment and registry updates

Automatically:
- Allocates a new file ID
- Creates file with proper naming convention
- Optionally updates registry
- Records creation in allocation history

File ID: P_01999000042260124028
Work ID: WORK-MAPP-PY-001
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add scripts directory to path to import id_allocator
sys.path.insert(0, str(Path(__file__).parent))

from P_01999000042260124027_id_allocator import IDAllocator


class FileCreator:
    """Create files with automatic ID assignment."""

    def __init__(self, counter_path: Path, registry_root: Path = None):
        self.allocator = IDAllocator(counter_path)
        self.registry_root = registry_root or Path.cwd()

    def create_file(
        self,
        name: str,
        extension: str,
        content: str = "",
        purpose: str = None,
        directory: Path = None
    ) -> Path:
        """
        Create a new file with auto-assigned ID.

        Args:
            name: Descriptive name for the file (without ID or extension)
            extension: File extension (.py, .json, .yaml, etc.)
            content: Initial file content (optional)
            purpose: Purpose for allocation tracking
            directory: Target directory (default: current directory)

        Returns:
            Path to created file
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'

        # Allocate ID
        purpose = purpose or f"Create {name}{extension}"
        file_id = self.allocator.allocate_single_id(purpose)

        # Determine naming convention
        if extension == '.py':
            filename = f"P_{file_id}_{name}{extension}"
        else:
            filename = f"{file_id}_{name}{extension}"

        # Determine target path
        target_dir = directory or Path.cwd()
        target_path = target_dir / filename

        # Create file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Created: {filename}")
        print(f"   ID: {file_id}")
        print(f"   Path: {target_path}")

        return target_path

    def create_python_script(
        self,
        name: str,
        description: str,
        content: str = "",
        directory: Path = None
    ) -> Path:
        """
        Create a Python script with standard header.

        Args:
            name: Script name (without .py)
            description: Script description
            content: Script content (after header)
            directory: Target directory

        Returns:
            Path to created file
        """
        header = f'''#!/usr/bin/env python3
"""
{description}

Created: {datetime.utcnow().strftime('%Y-%m-%d')}
"""

'''
        full_content = header + content

        return self.create_file(
            name=name,
            extension='.py',
            content=full_content,
            purpose=f"Create Python script: {name}",
            directory=directory
        )

    def create_json_file(
        self,
        name: str,
        data: dict,
        add_file_id: bool = True,
        directory: Path = None
    ) -> Path:
        """
        Create a JSON file with optional file_id field.

        Args:
            name: File name (without .json)
            data: Dictionary to save as JSON
            add_file_id: Whether to add file_id field to JSON
            directory: Target directory

        Returns:
            Path to created file
        """
        import json

        # Allocate ID first if we need to add it to content
        purpose = f"Create JSON: {name}"
        file_id = self.allocator.allocate_single_id(purpose)

        if add_file_id:
            data['file_id'] = file_id

        content = json.dumps(data, indent=2)

        # Create with pre-allocated ID
        filename = f"{file_id}_{name}.json"
        target_dir = directory or Path.cwd()
        target_path = target_dir / filename

        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Created: {filename}")
        print(f"   ID: {file_id}")
        print(f"   Path: {target_path}")

        return target_path

    def create_yaml_file(
        self,
        name: str,
        content: str,
        directory: Path = None
    ) -> Path:
        """
        Create a YAML file.

        Args:
            name: File name (without .yaml)
            content: YAML content
            directory: Target directory

        Returns:
            Path to created file
        """
        return self.create_file(
            name=name,
            extension='.yaml',
            content=content,
            purpose=f"Create YAML: {name}",
            directory=directory
        )


def main():
    """CLI interface for file creator."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Create files with auto-assigned IDs')
    parser.add_argument('--counter', type=Path,
                       default=Path('01999000042260124026_ID_COUNTER.json'),
                       help='Path to ID counter file')
    parser.add_argument('--name', type=str, required=True,
                       help='Descriptive file name (without ID or extension)')
    parser.add_argument('--ext', type=str, required=True,
                       choices=['py', 'json', 'yaml', 'yml', 'ps1'],
                       help='File extension')
    parser.add_argument('--description', type=str,
                       help='Description (for Python files)')
    parser.add_argument('--json-data', type=str,
                       help='JSON data as string (for JSON files)')
    parser.add_argument('--content', type=str,
                       help='File content (for YAML/other files)')
    parser.add_argument('--directory', type=Path,
                       help='Target directory (default: current)')
    parser.add_argument('--no-file-id', action='store_true',
                       help='Do not add file_id to JSON content')

    args = parser.parse_args()

    creator = FileCreator(args.counter)

    if args.ext == 'py':
        if not args.description:
            print("Error: --description required for Python files")
            sys.exit(1)

        created = creator.create_python_script(
            name=args.name,
            description=args.description,
            content=args.content or "",
            directory=args.directory
        )

    elif args.ext == 'json':
        if args.json_data:
            try:
                data = json.loads(args.json_data)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON data: {e}")
                sys.exit(1)
        else:
            data = {}

        created = creator.create_json_file(
            name=args.name,
            data=data,
            add_file_id=not args.no_file_id,
            directory=args.directory
        )

    else:
        created = creator.create_file(
            name=args.name,
            extension=args.ext,
            content=args.content or "",
            directory=args.directory
        )

    print(f"\n✅ File created successfully: {created}")


if __name__ == '__main__':
    main()
