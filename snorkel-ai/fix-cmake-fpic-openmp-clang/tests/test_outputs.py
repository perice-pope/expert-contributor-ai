from pathlib import Path
import subprocess
import sys


def test_cmake_build_succeeds():
    """Test that the CMake project builds successfully without errors."""
    app_dir = Path("/app")
    build_dir = app_dir / "build"
    
    # Clean and rebuild
    if build_dir.exists():
        subprocess.run(["rm", "-rf", str(build_dir)], check=True)
    
    build_dir.mkdir(exist_ok=True)
    
    # Run cmake
    result = subprocess.run(
        ["cmake", ".."],
        cwd=str(build_dir),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"CMake configuration failed:\n{result.stderr}"
    
    # Run make
    result = subprocess.run(
        ["make"],
        cwd=str(build_dir),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Build failed:\n{result.stderr}"


def test_shared_library_exists():
    """Test that the shared library (libmath_utils.so) is created."""
    build_dir = Path("/app/build")
    
    # Check for libmath_utils.so (exact name or with version suffix)
    lib_files = list(build_dir.glob("libmath_utils.so*"))
    assert len(lib_files) > 0, f"Shared library not found in {build_dir}. Found files: {list(build_dir.iterdir())}"


def test_executable_exists():
    """Test that the calculator executable is created."""
    calculator = Path("/app/build/calculator")
    assert calculator.exists(), f"Executable {calculator} does not exist"


def test_executable_runs_successfully():
    """Test that the calculator executable runs and produces correct output."""
    calculator = Path("/app/build/calculator")
    
    result = subprocess.run(
        [str(calculator)],
        cwd=str(calculator.parent),
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, f"Executable failed with return code {result.returncode}:\n{result.stderr}"
    
    # Check for expected output
    output = result.stdout
    assert "Sum:" in output, f"Expected 'Sum:' in output, got: {output}"
    assert "Dot product:" in output, f"Expected 'Dot product:' in output, got: {output}"
    assert "All tests passed!" in output, f"Expected 'All tests passed!' in output, got: {output}"


def test_executable_produces_correct_calculations():
    """Test that the calculator produces correct numerical results."""
    calculator = Path("/app/build/calculator")
    
    result = subprocess.run(
        [str(calculator)],
        cwd=str(calculator.parent),
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0
    
    output = result.stdout
    
    # Check sum calculation (1+2+3+4+5+6+7+8 = 36)
    assert "Sum: 36" in output or "Sum: 36.0" in output or "Sum: 36." in output, \
        f"Expected sum of 36, output: {output}"
    
    # Check dot product (1*4 + 2*5 + 3*6 = 32)
    assert "Dot product: 32" in output or "Dot product: 32.0" in output or "Dot product: 32." in output, \
        f"Expected dot product of 32, output: {output}"


def test_ctest_passes():
    """Test that ctest reports all tests passing."""
    build_dir = Path("/app/build")
    
    result = subprocess.run(
        ["ctest", "--output-on-failure"],
        cwd=str(build_dir),
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, f"ctest failed:\n{result.stderr}\n{result.stdout}"
    assert "100% tests passed" in result.stdout or "tests passed" in result.stdout.lower(), \
        f"Expected tests to pass, output: {result.stdout}"
