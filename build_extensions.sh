#!/bin/bash
set -e

PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Building FoundationPose extensions in: $PROJ_ROOT"

# Activate virtual environment if it exists
if [ -f "$PROJ_ROOT/../.venv/bin/activate" ]; then
    source "$PROJ_ROOT/../.venv/bin/activate"
fi

# 1. Build mycpp extension
echo "==== Building mycpp extension ===="
cd "$PROJ_ROOT/mycpp"
./build.sh
cd "$PROJ_ROOT"

# 2. Build mycuda extension
echo "==== Building mycuda extension ===="
cd "$PROJ_ROOT/bundlesdf/mycuda"
uv pip install --no-build-isolation -e .
cd "$PROJ_ROOT"

echo "==== All FoundationPose extensions built successfully ===="
