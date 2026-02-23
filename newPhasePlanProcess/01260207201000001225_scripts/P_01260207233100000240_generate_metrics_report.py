#!/usr/bin/env python3
"""Metrics Report Generator - Generates comprehensive metrics reports"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime

class MetricsReportGenerator:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
    
    def generate(self):
        with open(self.plan_path) as f:
            data = json.load(f)
        
        metrics = data.get('plan', {}).get('metrics', {})
        phases = data.get('plan', {}).get('phases_by_id', {})
        gates = data.get('plan', {}).get('gates_by_id', {})
        
        report = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'plan_id': data.get('meta', {}).get('plan_id', 'unknown'),
            'summary': {
                'total_phases': len(phases),
                'total_gates': len(gates),
                'determinism_score': metrics.get('determinism_score', 0),
                'gate_coverage': metrics.get('gate_coverage_percent', 0),
                'automation_ratio': metrics.get('automation_ratio_percent', 0)
            },
            'details': metrics
        }
        
        return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--output', default='metrics_report.json')
    parser.add_argument('--format', choices=['json', 'html'], default='json')
    args = parser.parse_args()
    
    generator = MetricsReportGenerator(args.plan_file)
    report = generator.generate()
    
    output_path = Path(args.output)
    
    if args.format == 'json':
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    elif args.format == 'html':
        html = f"<html><body><h1>Metrics Report</h1><pre>{json.dumps(report, indent=2)}</pre></body></html>"
        with open(output_path.with_suffix('.html'), 'w') as f:
            f.write(html)
    
    print(f"✅ Report generated: {output_path}")
    sys.exit(0)

if __name__ == '__main__':
    main()
