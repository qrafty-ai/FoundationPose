#!/bin/bash
set -e

# Build mycpp extension
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building mycpp extension..."
rm -rf build && mkdir -p build && cd build

# Get pybind11 cmake directory
PYBIND11_DIR=$(python -m pybind11 --cmakedir)

cmake .. \
    -DCMAKE_PREFIX_PATH="${CONDA_PREFIX:-/usr}" \
    -Dpybind11_DIR="$PYBIND11_DIR" \
    -DCMAKE_BUILD_TYPE=Release

make -j$(nproc)

echo "mycpp extension built successfully"
