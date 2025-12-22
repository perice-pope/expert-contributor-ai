# Fix CMake Shared Library Build with OpenMP

## Scenario

A CMake-based C++ project fails to build shared libraries due to missing position-independent code flags and unresolved OpenMP symbols when using Clang. The project uses OpenMP for parallel computation but cannot compile or run tests successfully.

## Requirements

1. **Diagnose the build errors**: Identify why the shared library build fails and why OpenMP symbols are unresolved.

2. **Enable position-independent code**: Update the CMake configuration to enable the `-fPIC` flag for shared library compilation.

3. **Fix OpenMP linking**: Ensure the correct OpenMP runtime is linked when using Clang compiler.

4. **Verify successful build**: The project must compile without errors, producing both the shared library (`libmath_utils.so`) and the executable (`calculator`).

5. **Verify tests pass**: The `calculator` executable must run successfully and pass all assertions.

## Constraints

- **DO NOT** modify the source code files (`src/*.cpp`, `src/*.h`)
- **DO NOT** change the project structure or file locations
- **DO NOT** modify the `README.md` file
- **ONLY** modify `/app/CMakeLists.txt` to fix the build issues
- The solution must work with Clang compiler
- The solution must be deterministic (no random behavior)

## Files

The project is located at `/app/` with the following structure:

- `/app/CMakeLists.txt` - CMake configuration file (modify this)
- `/app/src/main.cpp` - Main executable source
- `/app/src/math_utils.h` - Header file for math utilities
- `/app/src/math_utils.cpp` - Implementation of math utilities using OpenMP
- `/app/README.md` - Project documentation (do not modify)

## Outputs

After fixing the CMake configuration:

1. The project must build successfully:
   - Shared library: `/app/build/libmath_utils.so` (or similar path depending on build directory)
   - Executable: `/app/build/calculator`

2. The executable must run and produce output:
   - Prints sum and dot product calculations
   - Prints "All tests passed!"
   - Exits with code 0

3. CMake tests must pass:
   - Running `ctest` in the build directory should report all tests passing

## Build Instructions

The project should be built using:

```bash
cd /app
mkdir -p build
cd build
cmake ..
make
```

Then run:

```bash
./calculator
ctest
```
