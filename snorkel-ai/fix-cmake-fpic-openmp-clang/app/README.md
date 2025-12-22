# OpenMP Math Utils

A CMake-based C++ project that uses OpenMP for parallel computation.

## Building

```bash
mkdir build
cd build
cmake ..
make
```

## Running

```bash
./calculator
```

## Issues

The project currently fails to build due to:
1. Missing `-fPIC` flag when building shared libraries
2. Unresolved OpenMP symbols when using Clang

