import sys
import yaml
import json
from datetime import datetime

def validate_yaml_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        result = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'file': filepath,
            'valid': True,
            'message': 'YAML parsed successfully'
        }
        
        print(f"{filepath}: valid")
        return 0, result
    except Exception as e:
        result = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'file': filepath,
            'valid': False,
            'error': str(e)
        }
        print(f"{filepath}: invalid - {e}")
        return 1, result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python validate_yaml.py <file.yaml>')
        sys.exit(1)
    
    filepath = sys.argv[1]
    exit_code, result = validate_yaml_file(filepath)
    
    # Save evidence based on filename
    if 'contract' in filepath:
        evidence_path = '.state/evidence/PH-02/contract_yaml.json'
    elif 'vectors' in filepath:
        evidence_path = '.state/evidence/PH-02/vectors_yaml.json'
    else:
        evidence_path = '.state/evidence/PH-02/yaml_validation.json'
    
    with open(evidence_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    sys.exit(exit_code)
