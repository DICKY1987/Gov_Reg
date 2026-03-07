REM TRIGGER_ID: TRIGGER-RUNNER-RUN-DASHBOARD-003
@echo off
REM DOC-ID Dashboard Generation - Current Architecture
REM Updated: 2026-01-04 - Fixed obsolete migration_v3 path

cd /d "%~dp0.."
python 4_REPORTING_MONITORING\generate_dashboard.py
