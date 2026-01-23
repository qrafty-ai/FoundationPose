#!/usr/bin/env python
"""
Custom Hatchling build hook for FoundationPose that builds:
1. mycpp extension using CMake
2. mycuda extensions (common and gridencoder) using torch.utils.cpp_extension
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Custom build hook that runs CMake for mycpp and builds CUDA extensions"""

    def initialize(self, version, build_data):
        """Called before the build starts"""
        print("=" * 80)
        print("Running custom build hook for FoundationPose")
        print("=" * 80)

        # Build mycpp with CMake
        self.build_mycpp()

        # Build mycuda with torch.utils.cpp_extension
        self.build_mycuda()

        # Add built artifacts to the wheel
        if "force_include" not in build_data:
            build_data["force_include"] = {}

        # Include mycpp built library
        mycpp_build = Path(self.root) / "mycpp" / "build"
        built_libs = list(mycpp_build.glob("mycpp*.so"))
        if built_libs:
            for lib in built_libs:
                # Add to foundationpose package
                target_path = f"foundationpose/{lib.name}"
                build_data["force_include"][str(lib)] = target_path
                print(f"Will include {lib} as {target_path}")

        # Include mycuda built libraries (they'll be in foundationpose/bundlesdf/mycuda/)
        mycuda_dir = Path(self.root) / "foundationpose" / "bundlesdf" / "mycuda"
        mycuda_libs = list(mycuda_dir.glob("*.so"))
        for lib in mycuda_libs:
            rel_path = str(lib.relative_to(self.root))
            build_data["force_include"][str(lib)] = rel_path
            print(f"Will include {lib} as {rel_path}")

    def build_mycpp(self):
        """Build mycpp extension using CMake"""
        print("=" * 80)
        print("Building mycpp extension with CMake")
        print("=" * 80)

        source_dir = Path(self.root) / "mycpp"
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
            "-DCMAKE_BUILD_TYPE=Release",
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
        except subprocess.CalledProcessError as e:
            print(f"Error building mycpp: {e}")
            sys.exit(1)

    def build_mycuda(self):
        """Build mycuda extensions using torch.utils.cpp_extension"""
        print("=" * 80)
        print("Building mycuda extensions with torch.utils.cpp_extension")
        print("=" * 80)

        from torch.utils.cpp_extension import load

        mycuda_dir = Path(self.root) / "foundationpose" / "bundlesdf" / "mycuda"

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

        # Build common extension
        print("Building bundlesdf.mycuda.common...")
        try:
            load(
                name="common",
                sources=[
                    str(mycuda_dir / "bindings.cpp"),
                    str(mycuda_dir / "common.cu"),
                ],
                extra_cflags=c_flags,
                extra_cuda_cflags=nvcc_flags,
                extra_include_paths=eigen_includes,
                build_directory=str(mycuda_dir),
                verbose=True,
            )
            print("Successfully built bundlesdf.mycuda.common")
        except Exception as e:
            print(f"Error building common extension: {e}")
            sys.exit(1)

        # Build gridencoder extension
        print("Building bundlesdf.mycuda.gridencoder...")
        try:
            load(
                name="gridencoder",
                sources=[
                    str(mycuda_dir / "torch_ngp_grid_encoder" / "gridencoder.cu"),
                    str(mycuda_dir / "torch_ngp_grid_encoder" / "bindings.cpp"),
                ],
                extra_cflags=c_flags,
                extra_cuda_cflags=nvcc_flags,
                extra_include_paths=eigen_includes,
                build_directory=str(mycuda_dir),
                verbose=True,
            )
            print("Successfully built bundlesdf.mycuda.gridencoder")
        except Exception as e:
            print(f"Error building gridencoder extension: {e}")
            sys.exit(1)

    def clean(self, versions):
        """Called during clean operation"""
        print("Cleaning build artifacts...")

        # Clean mycpp build
        mycpp_build = Path(self.root) / "mycpp" / "build"
        if mycpp_build.exists():
            shutil.rmtree(mycpp_build)
            print(f"Removed {mycpp_build}")

        # Clean mycuda .so files
        mycuda_dir = Path(self.root) / "foundationpose" / "bundlesdf" / "mycuda"
        for so_file in mycuda_dir.glob("*.so"):
            so_file.unlink()
            print(f"Removed {so_file}")
