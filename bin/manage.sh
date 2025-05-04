#!/bin/bash
# Wrapper script for running Django management commands

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set environment variables
export IGLO_DB_PORT=15432
export CELERY_TASK_ALWAYS_EAGER=True
export ENABLE_PROFILING=False
export FAST_IGOR=True
export IGOR_MAX_STEPS=120  # Maximum steps for IGOR calculations

# Run the Django management command using the virtual environment's Python
"$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/iglo/manage.py" "$@"