#!/usr/bin/env python3
"""Generate lifecycle state validator."""

import sys
from pathlib import Path


VALIDATOR_CODE = '''#!/usr/bin/env python3
"""Lifecycle state validator for Gov_Reg artifacts."""

import json
from typing import Dict, List, Optional
from datetime import datetime


LIFECYCLE_STATES = [
    "DRAFT", "PROPOSED", "APPROVED", "DEPLOYED",
    "MONITORING", "STABLE", "DEPRECATED", "ARCHIVED"
]

VALID_TRANSITIONS = {
    "DRAFT": ["PROPOSED", "ARCHIVED"],
    "PROPOSED": ["APPROVED", "DRAFT"],
    "APPROVED": ["DEPLOYED", "PROPOSED"],
    "DEPLOYED": ["MONITORING", "APPROVED"],
    "MONITORING": ["STABLE", "DEPLOYED"],
    "STABLE": ["DEPRECATED"],
    "DEPRECATED": ["ARCHIVED"],
    "ARCHIVED": []
}


class LifecycleValidator:
    """Validates lifecycle state transitions."""
    
    def __init__(self):
        self.errors = []
    
    def validate_state(self, state: str) -> bool:
        """Validate that state is a valid lifecycle state."""
        if state not in LIFECYCLE_STATES:
            self.errors.append(f"Invalid state: {state}")
            return False
        return True
    
    def validate_transition(self, from_state: str, to_state: str) -> bool:
        """Validate state transition is allowed."""
        if from_state not in VALID_TRANSITIONS:
            self.errors.append(f"Invalid from_state: {from_state}")
            return False
        
        if to_state not in VALID_TRANSITIONS[from_state]:
            self.errors.append(
                f"Invalid transition: {from_state} -> {to_state}. "
                f"Allowed: {', '.join(VALID_TRANSITIONS[from_state])}"
            )
            return False
        
        return True
    
    def validate_artifact(self, artifact: Dict) -> bool:
        """Validate artifact lifecycle information."""
        self.errors = []
        
        # Check required fields
        if 'lifecycle_state' not in artifact:
            self.errors.append("Missing required field: lifecycle_state")
            return False
        
        # Validate current state
        current_state = artifact['lifecycle_state']
        if not self.validate_state(current_state):
            return False
        
        # Validate history if present
        if 'lifecycle_history' in artifact:
            history = artifact['lifecycle_history']
            if not isinstance(history, list):
                self.errors.append("lifecycle_history must be an array")
                return False
            
            # Validate each transition
            prev_state = None
            for i, transition in enumerate(history):
                if 'to_state' not in transition:
                    self.errors.append(f"History entry {i}: missing to_state")
                    return False
                
                to_state = transition['to_state']
                
                if prev_state is not None:
                    from_st = prev_state
                    if 'from_state' in transition:
                        from_st = transition['from_state']
                    
                    if not self.validate_transition(from_st, to_state):
                        return False
                
                prev_state = to_state
            
            # Verify final state matches current state
            if history and history[-1]['to_state'] != current_state:
                self.errors.append(
                    f"Current state ({current_state}) does not match "
                    f"final history state ({history[-1]['to_state']})"
                )
                return False
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self.errors


def validate_file(file_path: str) -> bool:
    """Validate lifecycle states in a file."""
    validator = LifecycleValidator()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            artifacts = [data]
        elif isinstance(data, list):
            artifacts = data
        else:
            print(f"ERROR: Unexpected data type in {file_path}")
            return False
        
        all_valid = True
        for i, artifact in enumerate(artifacts):
            if not validator.validate_artifact(artifact):
                all_valid = False
                print(f"Validation failed for artifact {i}:")
                for error in validator.get_errors():
                    print(f"  - {error}")
        
        if all_valid:
            print(f"✓ All artifacts in {file_path} have valid lifecycle states")
            return True
        else:
            return False
            
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {file_path}: {e}")
        return False


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lifecycle_validator.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = validate_file(file_path)
    sys.exit(0 if success else 1)
'''


def generate_lifecycle_validator(output_path):
    """Generate lifecycle validator script."""
    print(f"Generating Lifecycle Validator")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(VALIDATOR_CODE)
    
    # Make executable on Unix systems
    try:
        output.chmod(0o755)
    except:
        pass
    
    print(f"✓ Validator generated: {output_path}")
    print(f"  Features:")
    print(f"    - State validation")
    print(f"    - Transition validation")
    print(f"    - History validation")
    print(f"    - File validation")
    print("=" * 70)
    print(f"✓ VALIDATOR GENERATED")
    
    return 0


if __name__ == '__main__':
    output = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output = sys.argv[i + 1]
    
    if not output:
        print("Usage: python generate_lifecycle_validator.py --output <validator.py>")
        sys.exit(1)
    
    sys.exit(generate_lifecycle_validator(output))
