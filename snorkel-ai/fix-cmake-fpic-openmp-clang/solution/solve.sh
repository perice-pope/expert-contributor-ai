# CANARY_STRING_PLACEHOLDER

#!/bin/bash
set -euo pipefail

# Fix CMake configuration to enable -fPIC and correct OpenMP linking for Clang

cd /app

# Verify source files exist
if [ ! -f src/math_utils.cpp ] || [ ! -f src/math_utils.h ] || [ ! -f src/main.cpp ]; then
    echo "ERROR: Source files not found in /app/src/"
    ls -la /app/ || true
    ls -la /app/src/ || true
    exit 1
fi

# The issues are:
# 1. Missing CMAKE_POSITION_INDEPENDENT_CODE ON (needed for shared libraries)
# 2. OpenMP linking may not work correctly with Clang - need to ensure proper runtime

# Fix CMakeLists.txt
cat > CMakeLists.txt << 'EOF'
cmake_minimum_required(VERSION 3.15)
project(OpenMPExample VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable position-independent code for shared libraries
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find OpenMP
find_package(OpenMP REQUIRED COMPONENTS CXX)

# Create a shared library
add_library(math_utils SHARED
    src/math_utils.cpp
    src/math_utils.h
)

# Link OpenMP - for Clang, we need to ensure we link the correct runtime
# OpenMP::OpenMP_CXX should work, but we can also explicitly set the flags if needed
target_link_libraries(math_utils PUBLIC OpenMP::OpenMP_CXX)

# Create executable that uses the shared library
add_executable(calculator
    src/main.cpp
)

target_link_libraries(calculator PRIVATE math_utils)

# Add tests
enable_testing()
add_test(NAME calculator_test COMMAND calculator)
EOF

# Build the project
mkdir -p build
cd build
cmake ..
make

# Verify the build succeeded
if [ ! -f libmath_utils.so ] && [ ! -f libmath_utils.so.* ]; then
    echo "ERROR: Shared library not found"
    exit 1
fi

if [ ! -f calculator ]; then
    echo "ERROR: Executable not found"
    exit 1
fi

# Run the executable to verify it works
./calculator

# Run tests
ctest --output-on-failure

echo "Build and tests completed successfully!"
