# Duplicate ID Prevention System

## Summary
The system prevents duplicate IDs through **4 defense layers**:

### 1. **Atomic Counter (SSOT)**
**File:** `ID\1_runtime\allocators\P_01999000042260124031_unified_id_allocator.py`
- Uses `COUNTER_STORE.json` as single source of truth
- **File locking** (`atomic_json_write`) prevents race conditions
- Atomically increments counter: `counter += 1`
- Format: `01260207201XXXXXXXXX` (11-digit prefix + 9-digit counter)
- Max: 999,999,999 IDs before exhaustion

**Lock Mechanism:** `P_01999000042260124030_shared_utils.py`
- Windows: `msvcrt.locking()` on file handle
- Unix: `fcntl.flock()` exclusive lock
- Temp file write + atomic rename prevents partial writes
- Default timeout: 10 seconds

### 2. **Reservation Ledger**
**File:** `ID\1_runtime\allocators\P_01999000042260124032_reservation_ledger.py`
- Batch reserves ID ranges for multi-file operations
- Tracks state: RESERVED → COMMITTED → CANCELLED
- Prevents ID reuse during planning phase
- Per-plan ledger: `RES-{plan_id}.json`

### 3. **Pre-Commit Hook**
**File:** `ID\2_cli_tools\hooks\P_01999000042260125106_pre_commit_dir_id_check.py`
- Runs on `git commit` (blocks commit if violations found)
- **Checks:**
  - `check_no_duplicate_dir_ids()` - Scans all `.dir_id` files
  - `check_modified_dir_id_files_are_valid()` - Validates format (20 digits)
  - `check_new_governed_directories_have_dir_id()` - Enforces coverage
- Returns exit code 1 to block commit on duplicates

### 4. **Registry Reconciliation**
**File:** `ID\7_automation\P_01999000042260125106_registry_filesystem_reconciler.py`
- Post-scan validation
- **Checks:**
  - `_check_duplicate_file_ids()` - Registry has unique file_ids
  - `_check_duplicate_paths()` - Registry has unique paths
  - Severity: ERROR (cannot auto-fix, requires manual resolution)

### 5. **Health Check (Monitoring)**
**File:** `ID\2_cli_tools\maintenance\P_01999000042260125113_healthcheck.py`
- Periodic health monitoring
- `_check_duplicate_dir_ids()` - Scans all `.dir_id` files
- Severity: CRITICAL if duplicates found
- Reports coverage statistics

## Prevention Flow

1. **Allocation Time** → Atomic counter increment with file lock
2. **Batch Planning** → Reservation ledger tracks reserved ranges
3. **Commit Time** → Pre-commit hook blocks duplicate IDs
4. **Post-Scan** → Reconciler detects registry inconsistencies
5. **Monitoring** → Health check finds filesystem duplicates

## Key Files
- `COUNTER_STORE.json` - Monotonic counter (SSOT)
- `COUNTER_STORE.json.lock` - Cross-process mutex
- `RES-{plan_id}.json` - Reservation ledgers
- `.dir_id` files - Directory identity anchors
- `01999000042260124008_governance_registry.json` - Registry with file_id→path mapping

**No duplicates are possible** if all scripts use the unified allocator.
