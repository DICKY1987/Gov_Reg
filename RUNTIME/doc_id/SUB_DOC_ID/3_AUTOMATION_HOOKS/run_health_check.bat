REM TRIGGER_ID: TRIGGER-RUNNER-RUN-HEALTH-CHECK-004
@echo off
REM DOC-ID Health Check - Current Architecture
REM Updated: 2026-01-04 - Fixed obsolete migration_v3 path

cd /d "%~dp0.."
python 2_VALIDATION_FIXING\validate_doc_id_coverage.py --target 90
python 2_VALIDATION_FIXING\validate_doc_id_uniqueness.py
python 2_VALIDATION_FIXING\validate_registry_schema.py
