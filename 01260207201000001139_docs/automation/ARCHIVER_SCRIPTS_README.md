# Archive & Restore Scripts - Quick Reference

## Location
`C:\Users\richg\Gov_Reg`

---

## 1. caps_keyword_archiver.py

**Purpose:** Archive files based on CAPS keywords in filenames

**Keywords:** REPORT, COMPLETE, QUICKSTART, GUIDE, CHECKLIST, PLAN, SUMMARY, FINAL, PHASE, WEEK, STATUS, CHAT, SCRIPT

**Default Archive:** `C:\Users\richg\CENTRAL_ARCHIVE`

### Usage

#### Plan Mode (Preview what will be archived)
```bash
python caps_keyword_archiver.py --mode plan --parent "C:\path\to\directory" --out "./archive_plan"
```

#### Apply Mode (Execute the archive)
```bash
python caps_keyword_archiver.py --mode apply --out ./archive_plan
```

#### Dry Run (Test without moving files)
```bash
python caps_keyword_archiver.py --mode apply --out ./archive_plan --dry-run
```

### Options
- `--parent`: Directory to scan (default: `C:\Users\richg\Gov_Reg`)
- `--archive`: Archive destination (default: `C:\Users\richg\CENTRAL_ARCHIVE`)
- `--out`: Output directory for plans/reports (required)
- `--include-exts`: Filter by extensions (e.g., `--include-exts .md,.txt`)
- `--exclude-dirs`: Additional directories to exclude

### Output Files
- `MOVE_PLAN.md` - Human-readable plan
- `MOVE_MANIFEST.json` - Machine-readable manifest
- `APPLY_REPORT.md` - Execution report
- `APPLY_REPORT.json` - Execution details

---

## 2. restore_python_files.py

**Purpose:** Restore Python (.py) files from archive back to original locations

### Usage

```bash
python restore_python_files.py
```

### What it does:
1. Reads all MOVE_MANIFEST.json files from archive_plan* directories
2. Filters for .py files only
3. Moves them back from archive to original locations
4. Generates PYTHON_RESTORE_REPORT.json

### Output
- Console summary with counts
- `PYTHON_RESTORE_REPORT.json` - Detailed restoration log

---

## Common Workflows

### Archive files from a directory
```bash
# 1. Preview
python caps_keyword_archiver.py --mode plan --parent "C:\path\to\dir" --out "./plan_output"

# 2. Review plan_output/MOVE_PLAN.md

# 3. Execute
python caps_keyword_archiver.py --mode apply --out ./plan_output
```

### Archive multiple directories
```bash
# Run for each directory with different output folders
python caps_keyword_archiver.py --mode plan --parent "C:\dir1" --out "./plan_dir1"
python caps_keyword_archiver.py --mode plan --parent "C:\dir2" --out "./plan_dir2"

# Execute all
python caps_keyword_archiver.py --mode apply --out ./plan_dir1
python caps_keyword_archiver.py --mode apply --out ./plan_dir2
```

### Restore all Python files
```bash
python restore_python_files.py
```

---

## Notes

- **Safety:** Archiver never overwrites files (adds _N suffix for collisions)
- **Reversible:** Manifests preserve original paths for restoration
- **Selective:** Use `--include-exts` to target specific file types
- **Excluded:** Automatically skips .git, node_modules, venv, __pycache__, etc.

---

## History

- **2026-02-16:** Created archiver and restoration scripts
- **Keywords added:** STATUS, CHAT, SCRIPT (Round 2)
- **Total archived:** 1,298 files across 3 directories
- **Python files restored:** 323 files

---

## Customization

To add more keywords, edit `caps_keyword_archiver.py` line 41:

```python
KEYWORDS = {
    "REPORT", "COMPLETE", "QUICKSTART", "GUIDE", "CHECKLIST",
    "PLAN", "SUMMARY", "FINAL", "PHASE", "WEEK",
    "STATUS", "CHAT", "SCRIPT",
    # Add your keywords here:
    # "MYNEWKEYWORD",
}
```
