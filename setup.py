#!/usr/bin/env python
"""
Custom setup script for FoundationPose that builds:
1. mycpp extension using CMake
2. mycuda extensions (common and gridencoder) using torch.utils.cpp_extension
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext
from torch.utils.cpp_extension import BuildExtension, CUDAExtension


class CMakeBuild(BuildExtension):
    """Custom build extension that runs CMake for mycpp"""

    def run(self):
        # Build mycpp with CMake
        self.build_mycpp()
        # Build mycuda with torch.utils.cpp_extension
        super().run()

    def build_mycpp(self):
        """Build mycpp extension using CMake"""
        print("=" * 80)
        print("Building mycpp extension with CMake")
        print("=" * 80)

        source_dir = Path(__file__).parent / "mycpp"
        build_dir = source_dir / "build"

        # Clean and create build directory
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True)

        # Get pybind11 cmake directory
        try:
            import pybind11

            pybind11_dir = pybind11.get_cmake_dir()
        except Exception as e:
            print(f"Warning: Could not get pybind11 cmake dir: {e}")
            pybind11_dir = None

        # CMake configure
        cmake_args = [
            f"-DCMAKE_BUILD_TYPE=Release",
        ]

        if pybind11_dir:
            cmake_args.append(f"-Dpybind11_DIR={pybind11_dir}")

        # Add CONDA_PREFIX if available
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if conda_prefix:
            cmake_args.append(f"-DCMAKE_PREFIX_PATH={conda_prefix}")

        configure_cmd = ["cmake", str(source_dir)] + cmake_args
        build_cmd = ["make", f"-j{os.cpu_count() or 1}"]

        try:
            subprocess.check_call(configure_cmd, cwd=build_dir)
            subprocess.check_call(build_cmd, cwd=build_dir)
            print(f"Successfully built mycpp extension in {build_dir}")

            # Copy built library to build_lib so it gets included in the wheel
            built_libs = list(build_dir.glob("mycpp*.so"))
            if built_libs:
                built_lib = built_libs[0]
                dest_dir = Path(self.build_lib)
                dest_dir.mkdir(parents=True, exist_ok=True)
                print(f"Copying {built_lib} to {dest_dir}")
                shutil.copy(built_lib, dest_dir)
            else:
                print("Warning: Could not find built mycpp library to copy")

        except subprocess.CalledProcessError as e:
            print(f"Error building mycpp: {e}")
            sys.exit(1)


# Get the directory of this file
here = Path(__file__).parent

# mycuda extension setup
mycuda_dir = here / "bundlesdf" / "mycuda"
code_dir = str(mycuda_dir)

nvcc_flags = [
    "-Xcompiler",
    "-O3",
    "-std=c++17",
    "-U__CUDA_NO_HALF_OPERATORS__",
    "-U__CUDA_NO_HALF_CONVERSIONS__",
    "-U__CUDA_NO_HALF2_OPERATORS__",
]
c_flags = ["-O3", "-std=c++17"]

# Eigen include directories
eigen_includes = [
    "/usr/local/include/eigen3",
    "/usr/include/eigen3",
]

conda_prefix = os.environ.get("CONDA_PREFIX", "")
if conda_prefix:
    eigen_includes.append(os.path.join(conda_prefix, "include", "eigen3"))

# mycuda extensions
ext_modules = [
    CUDAExtension(
        "bundlesdf.mycuda.common",
        [
            "bundlesdf/mycuda/bindings.cpp",
            "bundlesdf/mycuda/common.cu",
        ],
        extra_compile_args={"gcc": c_flags, "nvcc": nvcc_flags},
        include_dirs=eigen_includes,
    ),
    CUDAExtension(
        "bundlesdf.mycuda.gridencoder",
        [
            "bundlesdf/mycuda/torch_ngp_grid_encoder/gridencoder.cu",
            "bundlesdf/mycuda/torch_ngp_grid_encoder/bindings.cpp",
        ],
        extra_compile_args={"gcc": c_flags, "nvcc": nvcc_flags},
        include_dirs=eigen_includes,
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={
        "build_ext": CMakeBuild,
    },
)
