# DOC_LINK: DOC-SCRIPT-CHECK-WORKSTREAM-STATUS-SH-056
#!/usr/bin/env bash
set -euo pipefail

echo "WORKSTREAM STATUS CHECKER - PH-01 to PH-03"
echo

write_section() {
  printf '%0.s?' {1..62}; echo
  echo "?? $1"
  printf '%0.s?' {1..62}; echo
}

check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    echo "    ? EXISTS"
    return 0
  fi
  if git show "main:$path" >/dev/null 2>&1; then
    echo "    ? EXISTS in main"
    return 0
  fi
  echo "    ? NOT FOUND"
  return 1
}

check_impl() {
  local path="$1"
  local func="$2"
  local pattern="def[[:space:]]\+${func}\b"
  if [[ -f "$path" ]] && grep -Eq "$pattern" "$path"; then
    echo "    ? IMPLEMENTED"
    return 0
  fi
  if content=$(git show "main:$path" 2>/dev/null) && echo "$content" | grep -Eq "$pattern"; then
    echo "    ? IMPLEMENTED in main"
    return 0
  fi
  echo "    ? STUB ONLY"
  return 1
}

resolve_or() {
  local key="$1" default="$2"
  if [[ -x scripts/paths_resolve_cli.py ]]; then
    if out=$(python scripts/paths_resolve_cli.py resolve "$key" 2>/dev/null); then
      printf '%s' "$out"
      return
    fi
  fi
  printf '%s' "$default"
}

write_section "ACTIVE WORKSTREAM BRANCHES"
git branch -a | grep 'workstream/' | sed 's/^[* ]*//' | sed 's#remotes/origin/##' || echo "  (none)"
echo

write_section "ACTIVE WORKTREES"
git worktree list | grep 'ws-ph' || echo "  (none)"
echo

write_section "KEY FILE IMPLEMENTATION STATUS"

dbPath=$(python scripts/paths_resolve_cli.py resolve core.db 2>/dev/null || echo "src/pipeline/db.py")

echo "PH-01: Spec Alignment & Index Mapping"
echo "  ws-ph01-module-stubs (Codex):"
echo "    core DB module: $dbPath"
check_file "$dbPath"
echo
echo "  ws-ph01-docs (Codex):"
archPath=$(resolve_or docs.architecture_main "docs/ARCHITECTURE.md")
echo "    $archPath (updated):"
check_file "$archPath"
echo

echo "PH-02: Data Model & State Machine"
echo "  ws-ph02-db-core (Codex):"
echo "    $dbPath::get_connection():"
check_impl "$dbPath" "get_connection"
echo

echo "PH-03: Tool Profiles & Adapter Layer"
echo "  ws-ph03-docs (Codex):"
phasePlan=$(resolve_or docs.phase_plan "docs/PHASE_PLAN.md")
echo "    $phasePlan (updated):"
check_file "$phasePlan"
echo

write_section "SUMMARY"
totalBranches=$(git branch -a | grep -c 'workstream/' || true)
totalWorktrees=$(git worktree list | grep -c 'ws-ph' || true)
echo "  Total workstream branches: $totalBranches / 17"
echo "  Active worktrees: $totalWorktrees"
