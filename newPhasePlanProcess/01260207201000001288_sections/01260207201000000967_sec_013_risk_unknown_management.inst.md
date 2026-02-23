# SEC-013: Risk + Unknown Management Instructions

**Schema File:** `sections/sec_013_risk_unknown_management.json`  
**Section ID:** `sec_013_risk_unknown_management`  
**Required:** Yes  
**Updated:** 2026-01-28

---

## What To Do

Track risks, unknowns, and open questions across the plan.

---

## How To Do It

### Step 1: Build Risk Register

For each identified risk:
```json
{
  "risk_id": "RISK-001",
  "type": "risk",
  "category": "technical",
  "description": "External API might rate-limit requests",
  "impact": "MEDIUM",
  "probability": "HIGH",
  "risk_score": 7,
  "mitigation": "Implement exponential backoff and request caching",
  "fallback": "Switch to alternative API provider",
  "detection_signal": "HTTP 429 responses in logs",
  "owner": "{{DRI}}",
  "status": "open"
}
```

**Categories:** technical, process, resource, external

**Risk score:** impact (1-5) × probability (1-2) = 1-10

Aim for **10-15 risks** - be thorough.

### Step 2: Build Unknown Register

For genuine uncertainties:
```json
{
  "unknown_id": "UNK-001",
  "type": "unknown",
  "category": "technical",
  "description": "Unclear if library supports draft-2020-12 schemas",
  "impact": "HIGH",
  "investigation_plan": "Test with sample draft-2020-12 schema",
  "investigation_budget": "2 hours",
  "fallback": "Use draft-07 schemas instead",
  "owner": "{{DRI}}",
  "status": "open"
}
```

**Categories:** technical, requirements, data, integration

### Step 3: Capture Open Questions

For questions needing answers:
```json
{
  "question_id": "Q-001",
  "question": "Should CLI output JSON or human-readable text by default?",
  "why_it_matters": "Affects CLI interface design and testing",
  "options": ["JSON", "human-readable", "both with --format flag"],
  "resolution_step": "Ask user for preference",
  "blocking": "YES",
  "owner": "{{DRI}}",
  "status": "open"
}
```

**Blocking:**
- YES: Cannot proceed without answer
- NO: Can defer to later phase

---

## Validation Rules

1. ≥5 risks in register
2. Each risk has: description, impact, probability, mitigation, fallback
3. Each unknown has: description, investigation_plan, fallback
4. Each question has: question, options, resolution_step, blocking

---

## AI Agent Notes

- Risks are "known unknowns" (we know what might go wrong)
- Unknowns are "unknown unknowns" (genuine uncertainty)
- Questions are decision points needing stakeholder input
- Update status as risks are mitigated / unknowns resolved
