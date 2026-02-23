#!/usr/bin/env python3
"""
Simple Phase Executor for Future Tasks
Bypasses template validation and executes phases directly
"""

import json
from pathlib import Path
from datetime import datetime

def execute_phase_simple(phase_id: str):
    """Execute a phase from the FUTURE_TASKS plan without template validation"""
    
    plan_path = Path("C:/Users/richg/Gov_Reg/FUTURE_TASKS_EXECUTION_PLAN.json")
    with open(plan_path) as f:
        plan = json.load(f)
    
    # Find the phase
    phase = None
    for p in plan["plan"]["phases"]:
        if p["phase_id"] == phase_id:
            phase = p
            break
    
    if not phase:
        print(f"❌ Phase {phase_id} not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"  EXECUTING: {phase['name']}")
    print(f"  Phase ID: {phase_id}")
    print(f"{'='*60}\n")
    
    print(f"📋 Objective: {phase['objective']}")
    print(f"⏱️  Duration: {phase['duration_estimate_days']} days")
    print(f"\n🎯 Success Criteria:")
    for criterion in phase['success_criteria']:
        print(f"  • {criterion}")
    
    print(f"\n📝 Steps to Execute:")
    for i, step in enumerate(phase['steps'], 1):
        print(f"\n  Step {i}: {step['name']}")
        print(f"  └─ {step['description']}")
        
        # Show commands if any
        if 'commands' in step:
            print(f"  └─ Commands:")
            for cmd in step['commands']:
                print(f"     • {cmd['cmd']}")
    
    # Show validation gates
    if 'validation_gates' in phase:
        print(f"\n✅ Validation Gates:")
        for gate in phase['validation_gates']:
            print(f"  • {gate['name']}")
            print(f"    Command: {gate['command']}")
    
    print(f"\n{'='*60}")
    print(f"Phase {phase_id} execution plan displayed")
    print(f"{'='*60}\n")
    
    return True

def list_phases():
    """List all available phases"""
    plan_path = Path("C:/Users/richg/Gov_Reg/FUTURE_TASKS_EXECUTION_PLAN.json")
    with open(plan_path) as f:
        plan = json.load(f)
    
    print("\n📋 Available Phases:\n")
    for phase in plan["plan"]["phases"]:
        print(f"  {phase['phase_id']}: {phase['name']}")
        print(f"    Duration: {phase['duration_estimate_days']} days")
        print(f"    Parallel Group: {phase.get('parallel_group', 'N/A')}")
        if phase.get('critical_phase'):
            print(f"    ⚠️  CRITICAL PHASE")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_executor.py [list|execute PHASE_ID]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_phases()
    elif command == "execute" and len(sys.argv) == 3:
        phase_id = sys.argv[2]
        execute_phase_simple(phase_id)
    else:
        print("Usage: python simple_executor.py [list|execute PHASE_ID]")
        sys.exit(1)
