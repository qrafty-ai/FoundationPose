#!/bin/bash
set -e

PROJ_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Project root: ${PROJ_ROOT}"

# 1. Install system dependencies via pixi
echo "Installing system dependencies via pixi..."
pixi install

# 2. Install Python dependencies via uv
echo "Installing Python dependencies via uv..."
# First sync without git dependencies to get torch and other base libs
# We do this by temporarily masking them or just running a sync that handles them.
# Given the complexities, we'll use the final successful command sequence.

# Create helper script for finding libs (created outside to avoid quote nesting issues)
cat <<EOF > .find_libs.py
import os, site, glob
try:
    site_pkg = site.getsitepackages()[0]
    libs = glob.glob(os.path.join(site_pkg, 'nvidia', '*', 'lib'))
    libs.append(os.path.join(site_pkg, 'torch', 'lib'))
    print(':'.join(libs))
except Exception:
    pass
EOF

pixi run bash -c '
export CUDA_HOME=$CONDA_PREFIX
export CUDA_PATH=$CONDA_PREFIX
export TORCH_CUDA_ARCH_LIST="8.0;8.6;9.0"
export IGNORE_TORCH_VER=1

echo "Syncing python environment..."
# 1. Install build dependencies from PyPI
uv pip install numpy Cython setuptools wheel ninja

# 2. Install PyTorch and related from PyTorch index (using extra-index-url to allow PyPI fallbacks)
uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128

# 3. Setup LD_LIBRARY_PATH for the build process
# We need to include nvidia libs (cudnn, cublas, etc.) and torch libs
export LD_LIBRARY_PATH=$(uv run python .find_libs.py):$LD_LIBRARY_PATH
echo "LD_LIBRARY_PATH set to: $LD_LIBRARY_PATH"

# 4. Sync the rest, using the pre-installed torch for building extensions
uv sync --no-build-isolation --preview-features extra-build-dependencies
source .venv/bin/activate

# Ensure pybind11 is available for CMake
uv pip install pybind11

# 3. Build mycpp extension
echo "Building mycpp extension..."
cd mycpp
rm -rf build && mkdir -p build && cd build
cmake ..     -DCMAKE_PREFIX_PATH=$CONDA_PREFIX     -Dpybind11_DIR=$(uv run python -m pybind11 --cmakedir)     -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
cd ../..

# 4. Build mycuda extension (already handled by uv sync --no-build-isolation if in pyproject.toml as editable, 
# but FoundationPose has it as a separate setup.py usually. In our pyproject.toml we didnt add it yet as editable by default.

echo "Building bundlesdf/mycuda extension..."
cd bundlesdf/mycuda
uv pip install --no-build-isolation -e .
cd ../..
'

echo "Modernized build complete."
