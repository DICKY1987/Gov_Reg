#!/bin/bash
set -euo pipefail

# Phase B Test Harness
# Generated: 2026-02-17T13:22:11.259336+00:00

echo 'Testing TASK-CLI-1...'
python -m pytest tests/test_cli.py

echo 'Testing TASK-CLI-2...'
python -m pytest tests/test_routing.py

echo 'Testing TASK-DOC-1...'
test -f README.md

echo 'All tests passed'