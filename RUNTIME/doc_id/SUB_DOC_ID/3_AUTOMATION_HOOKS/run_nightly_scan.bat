REM TRIGGER_ID: TRIGGER-RUNNER-RUN-NIGHTLY-SCAN-005
@echo off
REM DOC-ID Nightly Scan - Current Architecture
REM Updated: 2026-01-04 - Fixed obsolete migration_v3 path

cd /d "%~dp0.."
python 1_CORE_OPERATIONS\doc_id_scanner.py scan
python 5_REGISTRY_DATA\sync_registries.py check
