#!/usr/bin/env python3
"""Validate training completion for all teams."""

import sys
import json
from pathlib import Path


REQUIRED_TEAMS = ['engineering', 'operations']
COMPLETION_THRESHOLD = 80.0  # 80% minimum completion rate


def validate_training_completion():
    """Validate that all teams have completed training."""
    print("Training Completion Validation")
    print("=" * 70)
    
    all_teams_passed = True
    team_results = []
    
    for team in REQUIRED_TEAMS:
        attendance_file = Path(f"training/attendance/{team}.json")
        
        if attendance_file.exists():
            try:
                with open(attendance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                completion_rate = data.get('statistics', {}).get('completion_rate', 0.0)
                cert_rate = data.get('statistics', {}).get('certification_rate', 0.0)
                total_attendees = data.get('statistics', {}).get('total_attendees', 0)
                
                passed = completion_rate >= COMPLETION_THRESHOLD
                marker = "✓" if passed else "✗"
                
                print(f"{marker} {team.capitalize():15s} Completion: {completion_rate:5.1f}% | "
                      f"Certification: {cert_rate:5.1f}% | Attendees: {total_attendees}")
                
                team_results.append({
                    'team': team,
                    'passed': passed,
                    'completion_rate': completion_rate,
                    'cert_rate': cert_rate
                })
                
                if not passed:
                    all_teams_passed = False
                    
            except Exception as e:
                print(f"✗ {team.capitalize():15s} ERROR reading attendance file: {e}")
                all_teams_passed = False
                team_results.append({
                    'team': team,
                    'passed': False,
                    'completion_rate': 0.0,
                    'cert_rate': 0.0
                })
        else:
            print(f"✗ {team.capitalize():15s} No attendance record found")
            all_teams_passed = False
            team_results.append({
                'team': team,
                'passed': False,
                'completion_rate': 0.0,
                'cert_rate': 0.0
            })
    
    print("=" * 70)
    
    if all_teams_passed:
        avg_completion = sum(t['completion_rate'] for t in team_results) / len(team_results)
        print(f"✓ TRAINING COMPLETE - Average completion: {avg_completion:.1f}%")
        print(f"  All teams meet {COMPLETION_THRESHOLD}% threshold")
        return 0
    else:
        print(f"✗ TRAINING INCOMPLETE")
        failed_teams = [t['team'] for t in team_results if not t['passed']]
        print(f"  Teams below threshold: {', '.join(failed_teams)}")
        return 1


if __name__ == '__main__':
    sys.exit(validate_training_completion())
