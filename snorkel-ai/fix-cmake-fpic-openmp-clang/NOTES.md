# Maintainer Notes - fix-cmake-fpic-openmp-clang

## Task Overview

This task requires fixing a CMake-based C++ project that fails to build due to:
1. Missing `-fPIC` flag for shared library compilation (though modern CMake may enable this by default)
2. Unresolved OpenMP symbols when linking (the main failure mode)

## Intended Agent Failure Modes

### Shallow Fixes That Should Fail

1. **Only adding -fPIC flag manually**: Adding `-fPIC` to compile flags without fixing OpenMP linking will still fail
2. **Only linking OpenMP to executable**: The shared library needs OpenMP, not just the executable
3. **Using wrong OpenMP target**: Must use `OpenMP::OpenMP_CXX` imported target, not raw flags
4. **Missing PUBLIC linkage**: OpenMP must be linked PUBLICLY from the shared library so executables get it transitively

### Expected Agent Mistakes

- Trying to fix source code instead of CMakeLists.txt
- Not understanding that shared libraries need OpenMP linked PUBLICLY
- Adding OpenMP flags manually instead of using the imported target
- Not enabling `CMAKE_POSITION_INDEPENDENT_CODE` (though this may not be strictly necessary on all systems)

## Test Design Rationale

The tests verify:
1. **Build success**: CMake configuration and compilation must complete without errors
2. **Artifact creation**: Both shared library and executable must be created
3. **Runtime correctness**: Executable must run and produce correct numerical results
4. **Test framework**: ctest must report all tests passing

Tests are behavioral only - they check outputs and file existence, not source code inspection.

## Determinism and Reproducibility

- All package versions are pinned in Dockerfile
- CMake version: 3.25.1-1
- Clang version: 1:14.0-55.7~deb12u1
- OpenMP version: 1:14.0-55.7~deb12u1
- Build process is deterministic (no randomness)
- No network access required during build or execution

## Why Tests Are Structured This Way

- **test_cmake_build_succeeds**: Ensures the core build process works
- **test_shared_library_exists**: Verifies the shared library artifact is created
- **test_executable_exists**: Verifies the executable artifact is created
- **test_executable_runs_successfully**: Ensures runtime execution works (catches linking issues)
- **test_executable_produces_correct_calculations**: Validates correctness (catches logic errors)
- **test_ctest_passes**: Uses CMake's built-in testing framework for additional validation

Each test is independent and can fail for different reasons, making debugging easier.

## Known Issues and Edge Cases

- On some systems, `-fPIC` may be enabled by default for shared libraries, so the main failure mode is OpenMP linking
- The broken CMakeLists.txt uses `target_compile_options` with OpenMP flags but doesn't link the OpenMP library, causing undefined symbol errors
- The solution must use `OpenMP::OpenMP_CXX` imported target for proper Clang/OpenMP integration

