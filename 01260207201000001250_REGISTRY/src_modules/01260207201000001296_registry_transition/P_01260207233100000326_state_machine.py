"""
State Machine - Contract Loader + Transition Enforcer

Loads YAML contract and enforces transition rules.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .lifecycle_state import (
    Transition, Condition, Effect, TransitionResult, LifecycleState
)

class StateMachine:
    """Loads contract and enforces state transitions."""
    
    def __init__(self, contract_path: Path):
        """Load transition contract from YAML."""
        with open(contract_path, encoding='utf-8') as f:
            contract = yaml.safe_load(f)
        
        self.contract = contract
        self.transitions = {}
        
        # Build transition lookup
        for trans_name, trans_spec in contract.get('transitions', {}).items():
            from_states = trans_spec['from']
            if isinstance(from_states, str):
                from_states = [from_states]
            
            conditions = [
                Condition(
                    field=c['field'],
                    operator=c['operator'],
                    value=c.get('value')
                )
                for c in trans_spec.get('conditions', [])
            ]
            
            effects = [
                Effect(
                    action=e['action'],
                    target=e['target'],
                    value=e.get('value'),
                    rule=e.get('rule')
                )
                for e in trans_spec.get('effects', [])
            ]
            
            self.transitions[trans_name] = Transition(
                name=trans_name,
                from_states=from_states,
                to_state=trans_spec['to'],
                conditions=conditions,
                effects=effects
            )
    
    def transition(self, record: Dict, target_state: str, transition_name: Optional[str] = None) -> TransitionResult:
        """
        Execute state transition on record.
        
        Args:
            record: Registry record dict
            target_state: Desired target state
            transition_name: Optional specific transition (auto-detected if None)
        
        Returns:
            TransitionResult with success status and details
        """
        current_state = record.get('lifecycle_state', 'PLANNED')
        
        # Find matching transition
        if transition_name:
            trans = self.transitions.get(transition_name)
            if not trans:
                return TransitionResult(
                    success=False,
                    from_state=current_state,
                    to_state=target_state,
                    transition_name=transition_name,
                    errors=[f"Unknown transition: {transition_name}"]
                )
        else:
            trans = self._find_transition(current_state, target_state)
            if not trans:
                return TransitionResult(
                    success=False,
                    from_state=current_state,
                    to_state=target_state,
                    transition_name="",
                    errors=[f"No valid transition from {current_state} to {target_state}"]
                )
        
        # Validate from_state
        if current_state not in trans.from_states:
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=target_state,
                transition_name=trans.name,
                errors=[f"Invalid from_state: {current_state} not in {trans.from_states}"]
            )
        
        # Evaluate conditions
        for condition in trans.conditions:
            if not self._evaluate_condition(record, condition):
                return TransitionResult(
                    success=False,
                    from_state=current_state,
                    to_state=target_state,
                    transition_name=trans.name,
                    errors=[f"Condition failed: {condition.field} {condition.operator} {condition.value}"]
                )
        
        # Apply effects
        mutated_record = record.copy()
        applied = []
        
        for effect in trans.effects:
            result = self._apply_effect(mutated_record, effect)
            applied.append(result)
        
        return TransitionResult(
            success=True,
            from_state=current_state,
            to_state=target_state,
            transition_name=trans.name,
            applied_effects=applied
        )
    
    def available_transitions(self, record: Dict) -> List[str]:
        """Get list of valid transition names from current state."""
        current_state = record.get('lifecycle_state', 'PLANNED')
        available = []
        
        for trans_name, trans in self.transitions.items():
            if current_state in trans.from_states:
                available.append(trans_name)
        
        return available
    
    def _find_transition(self, from_state: str, to_state: str) -> Optional[Transition]:
        """Find transition matching from/to states."""
        for trans in self.transitions.values():
            if from_state in trans.from_states and trans.to_state == to_state:
                return trans
        return None
    
    def _evaluate_condition(self, record: Dict, condition: Condition) -> bool:
        """Evaluate single condition against record."""
        field_value = record.get(condition.field)
        
        if condition.operator == 'eq':
            return field_value == condition.value
        elif condition.operator == 'not_null':
            return field_value is not None
        elif condition.operator == 'in':
            return field_value in condition.value if condition.value else False
        elif condition.operator == 'gt':
            try:
                return field_value > condition.value
            except (TypeError, AttributeError):
                return False
        else:
            return False
    
    def _apply_effect(self, record: Dict, effect: Effect) -> Dict:
        """Apply single effect to record."""
        if effect.action == 'set_field':
            value = effect.value
            
            # Template substitution
            if value == '{{timestamp}}':
                value = datetime.utcnow().isoformat() + 'Z'
            elif value and '{{' in value:
                # Handle other templates like {{conflict_kind}}
                for key, val in record.items():
                    placeholder = '{{' + key + '}}'
                    if placeholder in value:
                        value = value.replace(placeholder, str(val))
            
            record[effect.target] = value
            
            return {
                'action': 'set_field',
                'target': effect.target,
                'value': value
            }
        
        elif effect.action == 'apply':
            # Delegate to field_precedence (handled by caller)
            return {
                'action': 'apply',
                'target': effect.target,
                'rule': effect.rule
            }
        
        return {'action': effect.action, 'target': effect.target}
