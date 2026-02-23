"""
Calculate Determinism Score from Real Metrics

Implements 7-factor calculation per DtoA_plan_CORRECTED.md Phase 4.
Each factor computed from actual evidence files, not hardcoded.

Factors:
1. decision_ledger - Exists and has entries
2. assumption_validation - Validated assumptions / total
3. file_scope - 1.0 - 0.2 * scope violations
4. ground_truth - Phases with ground truth / total phases
5. parallel_execution - DAG validation exists
6. self_healing - Self-heal attempts within budget
7. metrics_quantified - Metric names found / 8 expected

Version: 2.0
"""
import json
import sys
from pathlib import Path
from typing import Dict, List

def calc_determinism_score(metrics_path: Path) -> Dict:
    """
    Calculate determinism score from real metrics files.
    
    Args:
        metrics_path: Path to metrics.jsonl file
    
    Returns:
        Dict with score, breakdown, and metrics_lines_read proof
    """
    metrics_path = Path(metrics_path)
    lines_read = 0
    factors = {}
    
    # Read metrics.jsonl if it exists
    metrics_events = []
    if metrics_path.exists():
        with open(metrics_path, 'r', encoding='utf-8') as f:
            for line in f:
                lines_read += 1
                try:
                    event = json.loads(line.strip())
                    metrics_events.append(event)
                except json.JSONDecodeError:
                    continue
    
    # Factor 1: decision_ledger (0 or 1)
    factors['decision_ledger'] = calc_decision_ledger()
    
    # Factor 2: assumption_validation (0-1)
    factors['assumption_validation'] = calc_assumption_validation()
    
    # Factor 3: file_scope (0-1, penalized by violations)
    factors['file_scope'] = calc_file_scope(metrics_events)
    
    # Factor 4: ground_truth (0-1)
    factors['ground_truth'] = calc_ground_truth()
    
    # Factor 5: parallel_execution (0 or 1)
    factors['parallel_execution'] = calc_parallel_execution()
    
    # Factor 6: self_healing (0 or 1)
    factors['self_healing'] = calc_self_healing(metrics_events)
    
    # Factor 7: metrics_quantified (0-1)
    factors['metrics_quantified'] = calc_metrics_quantified(metrics_events)
    
    # Calculate weighted average (equal weights)
    score = sum(factors.values()) / len(factors)
    
    return {
        'determinism_score': round(score, 4),
        'factors': factors,
        'metrics_lines_read': lines_read,
        'met_target': score >= 0.95,
        'timestamp': Path('.state/evidence/score_calculated.txt').write_text(
            f"{score:.4f}\n"
        ) or None  # Side effect: write evidence
    }

def calc_decision_ledger() -> float:
    """Factor 1: Check if decision ledger exists with entries."""
    ledger_path = Path('.state/decision_ledger.json')
    
    if not ledger_path.exists():
        return 0.0
    
    try:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            ledger = json.load(f)
        
        # Check if it has entries
        if isinstance(ledger, list) and len(ledger) > 0:
            return 1.0
        elif isinstance(ledger, dict) and len(ledger.get('decisions', [])) > 0:
            return 1.0
    except (json.JSONDecodeError, KeyError):
        pass
    
    return 0.0

def calc_assumption_validation() -> float:
    """Factor 2: Validated assumptions / total assumptions."""
    assume_dir = Path('.state/evidence')
    
    if not assume_dir.exists():
        return 0.0
    
    assume_dirs = list(assume_dir.glob('ASSUME-*'))
    
    if not assume_dirs:
        return 0.0
    
    validated = 0
    total = len(assume_dirs)
    
    for assume_path in assume_dirs:
        validation_log = assume_path / 'validation.log'
        if validation_log.exists():
            with open(validation_log, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'PASS' in content or 'validated' in content.lower():
                    validated += 1
    
    return validated / total if total > 0 else 0.0

def calc_file_scope(metrics_events: List[Dict]) -> float:
    """Factor 3: 1.0 - 0.2 * scope_violations."""
    violations = 0
    
    for event in metrics_events:
        if event.get('event_type') == 'scope_violation':
            violations += 1
    
    # Penalty: -0.2 per violation, floor at 0.0
    score = max(0.0, 1.0 - 0.2 * violations)
    return score

def calc_ground_truth() -> float:
    """Factor 4: Phases with ground truth / total phases."""
    metrics_dir = Path('.state/metrics')
    
    if not metrics_dir.exists():
        return 0.0
    
    phase_dirs = list(metrics_dir.glob('PH-*'))
    
    if not phase_dirs:
        return 0.0
    
    with_gt = 0
    
    for phase_dir in phase_dirs:
        summary = phase_dir / 'summary.json'
        if summary.exists():
            try:
                with open(summary, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('has_ground_truth', False):
                        with_gt += 1
            except (json.JSONDecodeError, KeyError):
                pass
    
    return with_gt / len(phase_dirs) if phase_dirs else 0.0

def calc_parallel_execution() -> float:
    """Factor 5: Check if DAG validation exists."""
    dag_path = Path('.state/evidence/PH-00/dag_validation.json')
    
    if dag_path.exists():
        try:
            with open(dag_path, 'r', encoding='utf-8') as f:
                dag = json.load(f)
                if dag.get('valid', False):
                    return 1.0
        except (json.JSONDecodeError, KeyError):
            pass
    
    return 0.0

def calc_self_healing(metrics_events: List[Dict]) -> float:
    """Factor 6: Self-heal attempts within budget (max 3)."""
    attempts = 0
    
    for event in metrics_events:
        if event.get('event_type') == 'self_heal_attempt':
            attempts += 1
    
    # Within budget if <= 3 attempts
    return 1.0 if attempts <= 3 else 0.0

def calc_metrics_quantified(metrics_events: List[Dict]) -> float:
    """Factor 7: Metric names found / 8 expected."""
    expected_metrics = {
        'determinism_score',
        'test_coverage',
        'transition_count',
        'conflict_rate',
        'resolution_time',
        'gate_pass_rate',
        'immutable_violations',
        'orphan_count'
    }
    
    found_metrics = set()
    
    for event in metrics_events:
        metric_name = event.get('metric_name')
        if metric_name in expected_metrics:
            found_metrics.add(metric_name)
    
    return len(found_metrics) / len(expected_metrics)

if __name__ == '__main__':
    if '--metrics' not in sys.argv:
        print('Usage: python calc_determinism_score.py --metrics <metrics.jsonl>')
        sys.exit(1)
    
    idx = sys.argv.index('--metrics') + 1
    
    if idx >= len(sys.argv):
        print('Error: --metrics requires a file path')
        sys.exit(1)
    
    metrics_file = Path(sys.argv[idx])
    
    result = calc_determinism_score(metrics_file)
    
    # Pretty print result
    print(json.dumps(result, indent=2))
    
    # Write to evidence
    evidence_dir = Path('.state/evidence/final')
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    with open(evidence_dir / 'determinism_score.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Score: {result['determinism_score']:.4f}")
    print(f"✅ Metrics lines read: {result['metrics_lines_read']}")
    print(f"✅ Evidence saved to: {evidence_dir / 'determinism_score.json'}")
