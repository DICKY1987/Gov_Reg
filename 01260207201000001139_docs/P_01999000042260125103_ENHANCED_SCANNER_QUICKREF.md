# Enhanced Scanner Quick Reference

**FILE_ID:** 01999000042260125103  
**PURPOSE:** Quick reference for using the enhanced scanner service

## Command Usage

### Basic Scan (Backward Compatible)
```bash
python scanner_service.py --root . --root-id 01260207201000001169 --report
```

### Enhanced Scan - Summary
```bash
python scanner_service.py --root . --root-id 01260207201000001169 \
  --enhanced --format summary
```

### Enhanced Scan - Full Report
```bash
python scanner_service.py --root . --root-id 01260207201000001169 \
  --enhanced --format full --historical
```

### Enhanced Scan - Prometheus Metrics
```bash
python scanner_service.py --root . --root-id 01260207201000001169 \
  --enhanced --format prometheus
```

### Enhanced Scan with Fix
```bash
python scanner_service.py --root . --root-id 01260207201000001169 \
  --enhanced --fix --format full
```

### Save Report to File
```bash
python scanner_service.py --root . --root-id 01260207201000001169 \
  --enhanced --format full --output scan_report.json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No violations, system compliant |
| 1 | Violations found (or not all repaired in --fix mode) |
| 2 | Regression detected (compliance decreased >1%) |

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--root PATH` | Project root directory (default: current directory) |
| `--root-id ID` | Project root ID (required) |
| `--report` | Report-only mode, no fixes (default) |
| `--fix` | Repair mode, automatically fix violations |
| `--enhanced` | Use enhanced scan with comprehensive metrics |
| `--format FORMAT` | Output format: `basic`, `full`, `summary`, `prometheus` |
| `--historical` | Include historical comparison with previous scan |
| `--no-evidence` | Skip storing evidence (for testing only) |
| `--output FILE` | Save report to JSON file |

## Output Formats

### Summary Format
Concise one-screen summary with:
- Overall compliance score
- Violation count
- Scan duration
- Trend indicator (if --historical)

### Full Format
Comprehensive multi-section report with:
- Directory metrics
- File metrics
- Compliance coverage
- Zone distribution
- Depth analysis
- Registry sync status
- Duplicate detection
- Historical comparison
- Performance metrics
- Recommended actions

### Prometheus Format
Machine-readable metrics for monitoring:
- `governance_compliance_score`
- `governance_violations_total`
- `governance_directories_scanned`
- `governance_scan_duration_seconds`
- `governance_files_scanned`
- `governance_duplicates_total`

## Metrics Explained

### Compliance Score (0-100%)
Weighted average of directory and file compliance:
- 60% weight: Directory compliance (% governed dirs with valid .dir_id)
- 40% weight: File compliance (% files with correct ID format)

### Zone Compliance
Per-zone compliance percentages:
- **Governed** - Must have .dir_id files
- **Staging** - Transitioning to governance
- **Excluded** - Not subject to governance

### Registry Sync
Coherence between .dir_id files and registry:
- **In sync** - .dir_id matches registry entry
- **Missing from registry** - .dir_id exists but not in registry
- **Missing from filesystem** - Registry entry but no .dir_id
- **Path mismatch** - ID exists but paths don't match

### Violation Codes

| Code | Severity | Description |
|------|----------|-------------|
| DIR-IDENTITY-004 | ERROR | Missing .dir_id in governed directory |
| DIR-IDENTITY-005 | ERROR | Invalid .dir_id format (corrupt file) |
| DIR-IDENTITY-006 | ERROR | Invalid .dir_id content (validation failed) |

## Evidence Storage

Enhanced scans store evidence in:
```
.state/evidence/scans/{scan_id}/
├── report.json          # Full report
├── violations.jsonl     # Streaming violations (one per line)
├── metrics.json         # All metrics
├── registry_sync.json   # Registry sync details
├── duplicates.json      # Duplicate ID groups
└── sha256.txt           # Integrity hash
```

## CI/CD Integration

### Example: Fail on Violations
```bash
#!/bin/bash
python scanner_service.py \
  --root . \
  --root-id $PROJECT_ROOT_ID \
  --enhanced \
  --format summary \
  --output scan_report.json

EXIT_CODE=$?
if [ $EXIT_CODE -eq 1 ]; then
  echo "❌ Governance violations detected"
  exit 1
elif [ $EXIT_CODE -eq 2 ]; then
  echo "❌ Regression detected - compliance decreased"
  exit 1
else
  echo "✅ Governance check passed"
  exit 0
fi
```

### Example: Prometheus Monitoring
```bash
# Export metrics to file
python scanner_service.py \
  --root . \
  --root-id $PROJECT_ROOT_ID \
  --enhanced \
  --format prometheus \
  > metrics.prom

# Push to Pushgateway
cat metrics.prom | curl --data-binary @- \
  http://pushgateway:9091/metrics/job/governance_scan
```

## Historical Tracking

Enable with `--historical` flag:
- Compares with most recent scan in `.state/evidence/scans/`
- Shows violations delta (±count)
- Shows compliance delta (±percentage)
- Lists new violations
- Lists resolved violations
- Detects regression (>1% compliance decrease)

## Performance Tuning

Scanner performance depends on:
- **Directory count** - ~6-10 dirs/sec on typical hardware
- **File count** - ~50-100 files/sec for ID format checking
- **Registry size** - Larger registries increase sync check time

For large repositories (>1000 directories):
- Consider incremental scanning (future feature)
- Use `--no-evidence` during development
- Run full scans in CI/CD only

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError: No module named 'govreg_core'`:
- Run from repository root
- Ensure Python path includes govreg_core parent directory

### Memory Issues
If scanner consumes too much memory:
- Install psutil to track: `pip install psutil`
- Consider breaking into smaller scans
- Check for circular symlinks

### Git Not Available
Change detection requires git:
- Falls back gracefully if git not installed
- `files_modified_dir_id` will always be 0

### Slow Performance
If scans are slow:
- Check for network-mounted directories
- Exclude large directories (.venv, node_modules)
- Use SSD storage for `.state/evidence/`

## Examples

### Check Compliance Before Commit
```bash
python scanner_service.py --root . --root-id ID --enhanced --format summary
# Exit code 0 = safe to commit
```

### Generate Weekly Report
```bash
python scanner_service.py \
  --root . \
  --root-id ID \
  --enhanced \
  --format full \
  --historical \
  --output reports/governance_$(date +%Y%m%d).json
```

### Monitor in Production
```bash
# Cron job: Daily scan with Prometheus export
0 2 * * * cd /app && \
  python scanner_service.py \
    --root . \
    --root-id $ID \
    --enhanced \
    --format prometheus \
  > /var/metrics/governance.prom
```

### Fix All Violations
```bash
python scanner_service.py \
  --root . \
  --root-id ID \
  --fix \
  --enhanced \
  --format full
# Auto-allocates missing .dir_id files
```

## Related Documentation

- [Enhanced Scanner Implementation](P_01999000042260125102_ENHANCED_SCANNER_IMPLEMENTATION.md)
- [Directory Identity Contract](../ID_IDENTITY_CONTRACT.md)
- [Scanner Service Source](../01260207201000001173_govreg_core/P_01260207233100000071_scanner_service.py)
- [Test Suite](../P_01999000042260125101_test_enhanced_scanner_standalone.py)

## Support

For issues or questions:
1. Check test suite: `python P_01999000042260125101_test_enhanced_scanner_standalone.py`
2. Review implementation doc: `P_01999000042260125102_ENHANCED_SCANNER_IMPLEMENTATION.md`
3. Check evidence logs: `.state/evidence/scans/`

---

**Last Updated:** 2026-02-18  
**Version:** 1.0  
**Status:** Production Ready
