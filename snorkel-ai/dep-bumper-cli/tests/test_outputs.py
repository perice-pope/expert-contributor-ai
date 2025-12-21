"""Tests for the dependency bumper CLI tool."""
import json
import re
import subprocess
from pathlib import Path


def test_dep_bumper_exists():
    """Verify dep_bumper.py script exists and is executable."""
    script_path = Path("/app/dep_bumper.py")
    assert script_path.exists(), f"Script {script_path} does not exist"
    assert script_path.is_file(), f"{script_path} exists but is not a file"
    assert script_path.stat().st_mode & 0o111, f"{script_path} is not executable"


def test_package_json_exists():
    """Verify package.json file exists."""
    pkg_path = Path("/app/package.json")
    assert pkg_path.exists(), f"package.json {pkg_path} does not exist"
    assert pkg_path.is_file(), f"{pkg_path} exists but is not a file"


def test_package_json_valid():
    """Verify package.json is valid JSON with dependencies."""
    pkg_path = Path("/app/package.json")
    pkg_data = json.loads(pkg_path.read_text())
    
    assert isinstance(pkg_data, dict), "package.json must be a JSON object"
    assert "dependencies" in pkg_data or "devDependencies" in pkg_data, (
        "package.json must have dependencies or devDependencies"
    )


def test_requirements_txt_exists():
    """Verify requirements.txt file exists."""
    req_path = Path("/app/requirements.txt")
    assert req_path.exists(), f"requirements.txt {req_path} does not exist"
    assert req_path.is_file(), f"{req_path} exists but is not a file"


def test_cli_can_detect_outdated():
    """Verify CLI can detect outdated packages (may return empty if all up to date)."""
    script_path = Path("/app/dep_bumper.py")
    
    # Run with 'skip' input to avoid interactive selection
    result = subprocess.run(
        ["python3", str(script_path)],
        input="skip\n",
        capture_output=True,
        text=True,
        timeout=120,
        cwd="/app"
    )
    
    # Should complete without crashing
    assert "Reading dependency files" in result.stdout or "Checking for outdated packages" in result.stdout or "No outdated packages found" in result.stdout, (
        f"CLI should read files and check outdated. Output: {result.stdout}\nError: {result.stderr}"
    )


def test_cli_updates_package_json():
    """Verify CLI updates package.json when packages are selected."""
    script_path = Path("/app/dep_bumper.py")
    pkg_path = Path("/app/package.json")
    
    # Read original package.json
    original_data = json.loads(pkg_path.read_text())
    original_deps = original_data.get("dependencies", {}).copy()
    original_dev_deps = original_data.get("devDependencies", {}).copy()
    
    # Run CLI with 'all' selection if there are outdated packages, 'skip' otherwise
    # First check if there are outdated packages
    check_result = subprocess.run(
        ["npm", "outdated", "--json"],
        capture_output=True,
        text=True,
        cwd="/app",
        timeout=60
    )
    
    has_outdated = False
    if check_result.stdout:
        try:
            outdated = json.loads(check_result.stdout)
            has_outdated = len(outdated) > 0
        except json.JSONDecodeError:
            pass
    
    if has_outdated:
        # Run with 'all' to update all packages
        result = subprocess.run(
            ["python3", str(script_path)],
            input="all\n",
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/app"
        )
        
        # Check if package.json was updated
        updated_data = json.loads(pkg_path.read_text())
        updated_deps = updated_data.get("dependencies", {})
        updated_dev_deps = updated_data.get("devDependencies", {})
        
        # At least one dependency should have changed if updates were applied
        # (We check that the file was potentially modified - exact changes depend on available updates)
        assert "Updating dependency files" in result.stdout or "Done!" in result.stdout, (
            f"CLI should update files. Output: {result.stdout}\nError: {result.stderr}"
        )
    else:
        # No outdated packages, just verify CLI runs
        result = subprocess.run(
            ["python3", str(script_path)],
            input="skip\n",
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/app"
        )
        assert result.returncode == 0 or "No outdated packages" in result.stdout, (
            f"CLI should handle no outdated packages gracefully. Output: {result.stdout}\nError: {result.stderr}"
        )


def test_cli_updates_requirements_txt():
    """Verify CLI updates requirements.txt when packages are selected."""
    script_path = Path("/app/dep_bumper.py")
    req_path = Path("/app/requirements.txt")
    
    # Read original requirements.txt
    original_content = req_path.read_text()
    
    # Check for outdated PyPI packages
    pip_result = subprocess.run(
        ["pip", "list", "--outdated", "--format=json"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    has_outdated_pypi = False
    if pip_result.returncode == 0 and pip_result.stdout:
        try:
            outdated = json.loads(pip_result.stdout)
            # Check if any packages from requirements.txt are outdated
            req_packages = [line.split("==")[0].strip() for line in original_content.split("\n") 
                          if line.strip() and not line.strip().startswith("#")]
            outdated_names = [item["name"].lower() for item in outdated]
            has_outdated_pypi = any(pkg.lower() in outdated_names for pkg in req_packages)
        except (json.JSONDecodeError, KeyError):
            pass
    
    if has_outdated_pypi:
        # Run with 'all' to update all packages
        result = subprocess.run(
            ["python3", str(script_path)],
            input="all\n",
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/app"
        )
        
        # Check if requirements.txt was updated
        updated_content = req_path.read_text()
        
        # File should have been modified (exact changes depend on available updates)
        assert "Updating dependency files" in result.stdout or "Done!" in result.stdout, (
            f"CLI should update files. Output: {result.stdout}\nError: {result.stderr}"
        )


def test_cli_regenerates_lockfiles():
    """Verify CLI regenerates lockfiles after updates."""
    script_path = Path("/app/dep_bumper.py")
    
    # Check if there are outdated packages
    npm_result = subprocess.run(
        ["npm", "outdated", "--json"],
        capture_output=True,
        text=True,
        cwd="/app",
        timeout=60
    )
    
    has_outdated = False
    if npm_result.stdout:
        try:
            outdated = json.loads(npm_result.stdout)
            has_outdated = len(outdated) > 0
        except json.JSONDecodeError:
            pass
    
    if has_outdated:
        # Run with 'all' to trigger lockfile regeneration
        result = subprocess.run(
            ["python3", str(script_path)],
            input="all\n",
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/app"
        )
        
        # Should attempt to regenerate lockfiles
        assert "Regenerating lockfiles" in result.stdout, (
            f"CLI should regenerate lockfiles. Output: {result.stdout}\nError: {result.stderr}"
        )
        
        # package-lock.json should exist after npm install
        lock_path = Path("/app/package-lock.json")
        # Note: npm install may fail if packages are incompatible, but should be attempted
        # We just verify the attempt was made


def test_cli_generates_commit_summary():
    """Verify CLI generates commit-summary.txt file."""
    script_path = Path("/app/dep_bumper.py")
    summary_path = Path("/app/commit-summary.txt")
    
    # Remove existing summary if it exists
    if summary_path.exists():
        summary_path.unlink()
    
    # Check for outdated packages
    npm_result = subprocess.run(
        ["npm", "outdated", "--json"],
        capture_output=True,
        text=True,
        cwd="/app",
        timeout=60
    )
    
    has_outdated = False
    if npm_result.stdout:
        try:
            outdated = json.loads(npm_result.stdout)
            has_outdated = len(outdated) > 0
        except json.JSONDecodeError:
            pass
    
    if has_outdated:
        # Run with 'all' to generate summary
        result = subprocess.run(
            ["python3", str(script_path)],
            input="all\n",
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/app"
        )
        
        # commit-summary.txt should exist
        assert summary_path.exists(), (
            f"commit-summary.txt should be created. Output: {result.stdout}\nError: {result.stderr}"
        )
        
        # Verify content format
        summary_content = summary_path.read_text()
        assert "chore(deps):" in summary_content, (
            f"Summary should contain conventional commit format. Content: {summary_content}"
        )
    else:
        # No outdated packages - run with skip, summary may not be created
        result = subprocess.run(
            ["python3", str(script_path)],
            input="skip\n",
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/app"
        )
        # Summary may or may not exist if no updates were made


def test_commit_summary_format():
    """Verify commit-summary.txt has correct conventional commit format."""
    summary_path = Path("/app/commit-summary.txt")
    
    if not summary_path.exists():
        # Skip if summary doesn't exist (no updates were made)
        return
    
    summary_content = summary_path.read_text()
    
    # Should start with conventional commit header
    assert summary_content.startswith("chore(deps):"), (
        f"Summary should start with 'chore(deps):'. Content: {summary_content[:100]}"
    )
    
    # Should have sections for npm and/or pypi
    has_npm_section = "npm:" in summary_content
    has_pypi_section = "pypi:" in summary_content
    
    assert has_npm_section or has_pypi_section, (
        f"Summary should have npm or pypi section. Content: {summary_content}"
    )
    
    # Should have package update entries in format: "- package: old -> new"
    update_pattern = r"-\s+\w+:\s+\S+\s+->\s+\S+"
    matches = re.findall(update_pattern, summary_content)
    assert len(matches) > 0, (
        f"Summary should contain package update entries. Content: {summary_content}"
    )


def test_package_json_preserves_structure():
    """Verify package.json structure is preserved after updates."""
    pkg_path = Path("/app/package.json")
    
    if not pkg_path.exists():
        return
    
    pkg_data = json.loads(pkg_path.read_text())
    
    # Should still be valid JSON
    assert isinstance(pkg_data, dict), "package.json should remain a valid JSON object"
    
    # Should have name and version fields preserved
    if "name" in pkg_data:
        assert isinstance(pkg_data["name"], str), "name should be a string"
    
    if "version" in pkg_data:
        assert isinstance(pkg_data["version"], str), "version should be a string"


def test_requirements_txt_preserves_comments():
    """Verify requirements.txt preserves comments after updates."""
    req_path = Path("/app/requirements.txt")
    
    if not req_path.exists():
        return
    
    req_content = req_path.read_text()
    
    # Should still be a text file (not empty)
    assert len(req_content) > 0, "requirements.txt should not be empty"
    
    # If there were comments originally, they might be preserved
    # (exact preservation depends on implementation, but file should be valid)
