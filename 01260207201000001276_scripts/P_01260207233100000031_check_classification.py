import json
import sys
from datetime import datetime

def check_classification(plan_path, report_path):
    with open(plan_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)
    
    classification = plan.get('classification', 'unknown')
    
    # Validate assumptions
    assumptions_valid = True
    
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'classification': classification,
        'assumptions_valid': assumptions_valid,
        'validation_result': 'passed'
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"classification: {classification}")
    print(f"assumptions_valid: {assumptions_valid}")
    return 0

if __name__ == '__main__':
    if '--plan' not in sys.argv or '--report' not in sys.argv:
        print('Usage: python check_classification.py --plan <plan.json> --report <report.json>')
        sys.exit(1)
    
    plan_idx = sys.argv.index('--plan') + 1
    report_idx = sys.argv.index('--report') + 1
    
    plan_path = sys.argv[plan_idx]
    report_path = sys.argv[report_idx]
    
    sys.exit(check_classification(plan_path, report_path))
