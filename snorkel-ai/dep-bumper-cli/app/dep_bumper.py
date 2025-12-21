#!/usr/bin/env python3
"""
Dependency Bumper CLI - Broken starter implementation
This script has multiple bugs that need to be fixed.
"""

import json
import subprocess
import sys
from pathlib import Path

# BUG: Missing imports for parsing requirements.txt
# BUG: Missing error handling

def read_package_json():
    """Read package.json and extract dependencies."""
    pkg_path = Path("/app/package.json")
    if not pkg_path.exists():
        return {}
    
    with open(pkg_path) as f:
        data = json.load(f)
    
    # BUG: Only reads dependencies, misses devDependencies
    deps = data.get("dependencies", {})
    return deps

def read_requirements_txt():
    """Read requirements.txt and extract packages."""
    req_path = Path("/app/requirements.txt")
    if not req_path.exists():
        return []
    
    # BUG: Doesn't handle comments or version constraints properly
    packages = []
    with open(req_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # BUG: Simple split doesn't handle all constraint formats
                parts = line.split("==")
                if len(parts) == 2:
                    packages.append({"name": parts[0], "version": parts[1]})
    
    return packages

def get_npm_outdated():
    """Get outdated npm packages."""
    # BUG: Doesn't handle errors or missing npm
    result = subprocess.run(
        ["npm", "outdated", "--json"],
        capture_output=True,
        text=True,
        cwd="/app"
    )
    
    # BUG: Doesn't check return code
    if result.stdout:
        return json.loads(result.stdout)
    return {}

def get_pypi_outdated():
    """Get outdated PyPI packages."""
    # BUG: Wrong command - pip index versions doesn't work the way we need
    # BUG: Should use pip list --outdated --format=json instead
    outdated = []
    packages = read_requirements_txt()
    
    for pkg in packages:
        # BUG: This command doesn't exist or work correctly
        result = subprocess.run(
            ["pip", "index", "versions", pkg["name"]],
            capture_output=True,
            text=True
        )
        # BUG: Doesn't parse output correctly
        outdated.append(pkg)
    
    return outdated

def interactive_select(outdated_npm, outdated_pypi):
    """Interactive selection of packages to update."""
    all_packages = []
    
    # BUG: Doesn't format output correctly
    idx = 1
    for pkg_name, info in outdated_npm.items():
        print(f"{idx}. {pkg_name}: {info.get('current')} -> {info.get('latest')} (npm)")
        all_packages.append(("npm", pkg_name, info))
        idx += 1
    
    for pkg in outdated_pypi:
        # BUG: Doesn't have version info from get_pypi_outdated
        print(f"{idx}. {pkg['name']}: ? -> ? (pypi)")
        all_packages.append(("pypi", pkg["name"], pkg))
        idx += 1
    
    # BUG: Doesn't handle input validation or ranges
    selection = input("Select packages (comma-separated indices, 'all', or 'skip'): ").strip()
    
    if selection.lower() == "skip" or not selection:
        return []
    
    if selection.lower() == "all":
        return all_packages
    
    # BUG: Doesn't handle comma-separated or ranges
    indices = [int(x) for x in selection.split(",")]
    return [all_packages[i - 1] for i in indices]

def update_package_json(updates):
    """Update package.json with new versions."""
    pkg_path = Path("/app/package.json")
    with open(pkg_path) as f:
        data = json.load(f)
    
    # BUG: Only updates dependencies, not devDependencies
    for ecosystem, pkg_name, info in updates:
        if ecosystem == "npm":
            # BUG: Doesn't preserve existing version prefix (^, ~, etc.)
            data["dependencies"][pkg_name] = f"^{info['latest']}"
    
    with open(pkg_path, "w") as f:
        json.dump(data, f, indent=2)

def update_requirements_txt(updates):
    """Update requirements.txt with new versions."""
    req_path = Path("/app/requirements.txt")
    
    # BUG: Doesn't preserve comments or formatting
    lines = []
    for ecosystem, pkg_name, info in updates:
        if ecosystem == "pypi":
            # BUG: Doesn't have version info, hardcodes ==
            lines.append(f"{pkg_name}==2.0.0")
    
    with open(req_path, "w") as f:
        f.write("\n".join(lines))

def regenerate_lockfiles():
    """Regenerate npm and pip lockfiles."""
    # BUG: Uses npm ci instead of npm install
    subprocess.run(["npm", "ci"], cwd="/app", check=True)
    
    # BUG: Wrong command - should be pip-compile
    subprocess.run(["pip", "compile", "requirements.txt"], cwd="/app", check=True)

def generate_commit_summary(updates):
    """Generate conventional commit summary."""
    # BUG: Doesn't separate npm and pypi sections
    # BUG: Doesn't have proper version information
    summary = "chore(deps): bump dependencies\n\n"
    
    for ecosystem, pkg_name, info in updates:
        summary += f"- {pkg_name}: ? -> ? ({ecosystem})\n"
    
    # BUG: Doesn't write to correct path
    with open("/app/commit.txt", "w") as f:
        f.write(summary)

def main():
    """Main entry point."""
    print("Reading dependency files...")
    npm_deps = read_package_json()
    pypi_deps = read_requirements_txt()
    
    print("Checking for outdated packages...")
    outdated_npm = get_npm_outdated()
    outdated_pypi = get_pypi_outdated()
    
    if not outdated_npm and not outdated_pypi:
        print("No outdated packages found.")
        return
    
    print("\nOutdated packages:")
    updates = interactive_select(outdated_npm, outdated_pypi)
    
    if not updates:
        print("No packages selected. Exiting.")
        return
    
    print("\nUpdating dependency files...")
    update_package_json(updates)
    update_requirements_txt(updates)
    
    print("Regenerating lockfiles...")
    regenerate_lockfiles()
    
    print("Generating commit summary...")
    generate_commit_summary(updates)
    
    print("Done!")

if __name__ == "__main__":
    main()

