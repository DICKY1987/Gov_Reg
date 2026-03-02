# --- REQUIRED DECLARATIVE METADATA (authoritative) ---
AUTOMATION_META = {
  "schema_version": "1.0",
  "record_kind": "automation_file_descriptor",

  "identity": {
    "status": "active",          # active|deprecated|experimental|draft
    "owner": "SYSTEM",           # person/team/system
    "entrypoint": "cli",         # cli|daemon|library|ci
  },

  "purpose": {
    "one_line_summary": "Describe what this automation does in one sentence.",
    "primary_user_value": "Why this exists / what pain it removes.",
    "scope_in": ["..."],
    "scope_out": ["..."],
  },

  "triggering": {
    "trigger_modes": ["manual"],   # manual|scheduled|watcher|event-driven|pipeline
    "triggers": [
      {"type": "manual", "condition": "Invoked by user", "debounce_ms": 0, "idempotency_key": ""}
    ],
  },

  "state_and_ssot": {
    "ssot_reads": ["..."],         # explicit: which registry/ssot files are read
    "ssot_writes": ["..."],        # explicit: which registry/ssot files are written
  },

  "security_and_safety": {
    "allowed_paths": ["..."],
    "denied_paths": ["..."],
    "destructive_ops": ["delete", "overwrite"],   # explicit list
  },

  "testing": {
    "acceptance_tests": [
      {"id": "AT-001", "scenario": "…", "evidence_required": ["…"]}
    ]
  }
}
# --- END METADATA ---
