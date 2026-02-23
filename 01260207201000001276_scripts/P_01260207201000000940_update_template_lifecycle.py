#!/usr/bin/env python3
"""Update template files with lifecycle state tracking."""

import sys
import json
from pathlib import Path
from datetime import datetime


def update_template_lifecycle(template_path, output_path):
    """Update template with lifecycle tracking."""
    print(f"Updating Template with Lifecycle Tracking")
    print("=" * 70)
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
    except FileNotFoundError:
        print(f"Template not found: {template_path}")
        template = {"template_id": "default", "version": "1.0"}
    
    # Add lifecycle fields to template
    template['lifecycle_state'] = 'DRAFT'
    template['lifecycle_history'] = []
    template['lifecycle_metadata'] = {
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'last_modified': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Save
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    print(f"✓ Template updated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    template = sys.argv[1] if len(sys.argv) > 1 else 'templates/default.json'
    output = sys.argv[2] if len(sys.argv) > 2 else 'templates/default_lifecycle.json'
    sys.exit(update_template_lifecycle(template, output))
