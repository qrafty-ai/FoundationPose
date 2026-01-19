# FoundationPose Extensions Build Guide

This directory contains custom C++ and CUDA extensions for FoundationPose.

## Extensions

1. **mycpp**: C++ extension built with CMake and pybind11
2. **bundlesdf/mycuda**: CUDA extension with two modules (common and gridencoder)

## Building

### Automatic Build (Recommended)

Run the master build script from this directory:

```bash
./build_extensions.sh
```

This will build both mycpp and mycuda extensions.

### Manual Build

#### 1. Build mycpp

```bash
cd mycpp
./build.sh
cd ..
```

#### 2. Build mycuda

```bash
cd bundlesdf/mycuda
uv pip install --no-build-isolation -e .
cd ../..
```

## Integration with uv

The mycuda extension is configured as an editable path dependency in the main `pyproject.toml`:

```toml
[dependency-groups]
foundationpose = [
    "foundationpose",
    "foundationpose-mycuda",
]

[tool.uv.sources]
foundationpose-mycuda = { path = "FoundationPose/bundlesdf/mycuda", editable = true }

[tool.uv.extra-build-dependencies]
foundationpose-mycuda = ["torch>=2.8.0,<2.9.0", "setuptools", "wheel", "numpy>=2.0"]
```

## Requirements

- CMake >= 3.15
- C++ compiler with C++17 support
- CUDA toolkit
- PyTorch with CUDA support
- pybind11
- Eigen3
- Boost (system, program_options)
- OpenMP

## Notes

- The mycpp extension creates a `mycpp.so` file in `mycpp/build/`
- The mycuda extension creates `common` and `gridencoder` modules
- Both extensions need to be rebuilt when PyTorch is updated
- The build uses the same PyTorch version as specified in the main project dependencies
