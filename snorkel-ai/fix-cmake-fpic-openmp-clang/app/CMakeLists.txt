cmake_minimum_required(VERSION 3.15)
project(OpenMPExample VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Intentionally missing: set(CMAKE_POSITION_INDEPENDENT_CODE ON)
# This will cause -fPIC errors when building shared libraries

# Find OpenMP
find_package(OpenMP REQUIRED COMPONENTS CXX)

# Create a shared library (this will fail without -fPIC on some linkers)
add_library(math_utils SHARED
    src/math_utils.cpp
    src/math_utils.h
)

# Intentionally broken: Try to use OpenMP flags directly instead of the imported target
# This approach may not work correctly with Clang's OpenMP runtime
target_compile_options(math_utils PRIVATE ${OpenMP_CXX_FLAGS})
# Missing: target_link_libraries with OpenMP::OpenMP_CXX
# This will cause unresolved symbols when linking

# Create executable that uses the shared library
add_executable(calculator
    src/main.cpp
)

target_link_libraries(calculator PRIVATE math_utils)

# Add tests
enable_testing()
add_test(NAME calculator_test COMMAND calculator)
