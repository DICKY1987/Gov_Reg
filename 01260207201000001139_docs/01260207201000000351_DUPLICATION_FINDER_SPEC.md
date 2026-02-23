# Multi-Faceted Duplication Finder Specification

## Purpose
Define a single, clear specification for a script that detects duplicates across multiple facets (content, structure, IDs, and paths). The script is read-only and produces reports suitable for follow-on cleanup or remediation work.

## Goals
- Detect exact duplicates by content hash.
- Detect near-duplicates via normalization (whitespace, line endings, case).
- Detect structured duplicates across JSON and YAML (canonicalized data).
- Detect ID-level duplicates (same file_id, bundle_id, or registry key).
- Provide a consistent grouping and confidence model across facets.
- Emit machine-readable reports with enough context to choose a canonical file.

## Non-Goals
- Automatically delete, move, or rewrite files.
- Replace governance validation or registry reconciliation logic.
- Perform semantic similarity via external APIs or network calls.

## Inputs
- One or more scan roots (files or directories).
- Include and exclude patterns (glob-like).
- Optional registry sources (JSON or YAML) for ID-based duplication checks.
- Optional facet toggles to enable or disable detectors.

## Facets and Detection Rules

### 1) Exact Content Hash (Binary-Safe)
- Hash algorithm: SHA256 (streamed in chunks).
- Grouping key: `content_hash`.
- Confidence: 1.0.
- Purpose: exact duplicates, regardless of file name or location.

### 2) Normalized Text Hash
- Normalization: convert CRLF to LF, trim trailing whitespace, collapse multiple blank lines, optional case-fold.
- Grouping key: `normalized_text_hash`.
- Confidence: 0.7 to 0.9 based on normalization profile.
- Purpose: duplicates with cosmetic differences.

### 3) Structured Data Canonicalization (JSON/YAML)
- Parse data, sort keys, remove volatile fields (configurable list), then serialize to canonical JSON.
- Grouping key: `structured_hash`.
- Confidence: 0.9.
- Purpose: logically identical structured files that differ in formatting or field order.

### 4) Registry ID Duplicates
- Input: registry JSON/YAML with known ID fields (file_id, bundle_id, record_id, doc_id).
- Grouping key: `id:<id_value>`.
- Confidence: 1.0 if exact match in same registry namespace.
- Purpose: ID collisions and duplicates across registry entries.

### 5) Path and Name Similarity
- Signals: same file name, same stem, or same relative path across roots.
- Optional edit-distance threshold for near matches (configurable).
- Confidence: 0.4 to 0.7 depending on match type.
- Purpose: duplicates with identical naming patterns.

### 6) Optional Fuzzy Content Similarity
- Technique: shingling + rolling hash or a local fuzzy hash (no network).
- Grouping key: `fuzzy:<cluster_id>`.
- Confidence: 0.5 to 0.8 based on similarity score.
- Purpose: near-duplicates where normalization is insufficient.

## Grouping and Confidence
- Each facet produces candidate groups with a facet-specific confidence score.
- A merged group is formed when two or more facets point to the same set of files.
- Final confidence is the max of contributing facet scores, with a boost when multiple facets agree.

## Canonical Selection
Canonical choice is deterministic and configurable. Default priority order:
1. Location tier (preferred directories).
2. Newest mtime (or oldest, configurable).
3. Shallowest path depth.
4. Largest file (if structured).
5. Stable tie-breaker: lexicographic path.

## Output

### Report Schema (JSON)
Top-level fields:
- `scan_summary`: counts, timing, exclusions, errors.
- `facet_summary`: per-facet counts and settings.
- `duplicate_groups`: array of groups.

Each `duplicate_group` includes:
- `group_id`, `facet`, `confidence`
- `canonical` (path)
- `members`: list of files with path, size, mtime, and signals.
- `notes`: optional list of warnings or exclusions.

### Human-Readable Summary (MD or TXT)
- Total groups and total duplicates.
- Top N groups by size and by confidence.
- A short list of recommended canonical paths.

## CLI Outline
- `--scan-paths <path...>`
- `--include <glob...>`
- `--exclude <glob...>`
- `--min-size-bytes <int>`
- `--registry <path...>` (optional)
- `--facet <name...>` (subset of facets)
- `--report <path>` and `--report-format json|md|txt`
- `--fail-on-duplicate` (exit code 1 if any duplicates found)

## Config Outline (YAML)
Key sections:
- `global`: scan paths, include/exclude, min size, timeouts
- `facets`: per-facet enable/disable and thresholds
- `canonical`: selection rules and location tiers
- `output`: report path, format, and top-N limits

## Safety and Operational Constraints
- Read-only: no file modifications.
- Skip or log unreadable files; never stop a scan on a single error.
- Default exclusions: `.git\`, `__pycache__\`, `node_modules\`, and backup folders.
- Support large files via streaming to avoid memory spikes.

## Test Plan
- Unit tests for hashing, normalization, and canonicalization.
- Structured duplicates across JSON and YAML samples.
- ID-level duplicates using a fixture registry file.
- Performance test on a directory with 10k+ files.

## Open Questions
- Which ID fields are authoritative for duplicate grouping in this repo?
- Should normalized text hashing be enabled by default for code files?
- Which directories should be highest priority in the canonical location tier list?
