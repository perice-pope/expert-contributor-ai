# CANARY_STRING_PLACEHOLDER

#!/bin/bash
set -euo pipefail

# Fix the broken dep_bumper.py implementation
# This script applies all necessary fixes to make the CLI work correctly

cd /app

# Create a fixed version of dep_bumper.py
cat > dep_bumper.py << 'ENDPYTHON'
#!/usr/bin/env python3
"""
Dependency Bumper CLI - Fixed implementation
"""

import json
import re
import subprocess
import sys
from pathlib import Path

def read_package_json():
    """Read package.json and extract dependencies and devDependencies."""
    pkg_path = Path("/app/package.json")
    if not pkg_path.exists():
        return {}, {}
    
    try:
        with open(pkg_path) as f:
            data = json.load(f)
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        return deps, dev_deps
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading package.json: {e}", file=sys.stderr)
        return {}, {}


def read_requirements_txt():
    """Read requirements.txt and extract packages with version constraints."""
    req_path = Path("/app/requirements.txt")
    if not req_path.exists():
        return []
    
    packages = []
    try:
        with open(req_path) as f:
            for line in f:
                original_line = line
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    packages.append({"name": None, "version": None, "original": original_line, "is_comment": True})
                    continue
                
                # Parse package name and version constraint
                # Handle formats: package==1.2.3, package>=1.2.3, package~=1.2.3, etc.
                match = re.match(r'^([a-zA-Z0-9_-]+[a-zA-Z0-9_.-]*)\s*(.*)$', line)
                if match:
                    name = match.group(1)
                    version_constraint = match.group(2).strip() if match.group(2) else ""
                    packages.append({
                        "name": name,
                        "version": version_constraint,
                        "original": original_line,
                        "is_comment": False
                    })
    except IOError as e:
        print(f"Error reading requirements.txt: {e}", file=sys.stderr)
    
    return packages


def get_npm_outdated():
    """Get outdated npm packages."""
    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            capture_output=True,
            text=True,
            cwd="/app",
            timeout=60
        )
        
        # npm outdated returns non-zero exit code when packages are outdated
        # This is expected, so we check stdout instead
        if result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {}
        return {}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error checking npm outdated: {e}", file=sys.stderr)
        return {}


def get_pypi_outdated():
    """Get outdated PyPI packages."""
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                outdated_list = json.loads(result.stdout)
                # Convert to dict for easier lookup
                outdated_dict = {item["name"].lower(): item for item in outdated_list}
                return outdated_dict
            except json.JSONDecodeError:
                return {}
        return {}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error checking pip outdated: {e}", file=sys.stderr)
        return {}


def parse_version_constraint(constraint):
    """Extract current version from constraint string."""
    if not constraint:
        return None
    # Try to extract version number from various formats
    match = re.search(r'([0-9]+\.[0-9]+(?:\.[0-9]+)?)', constraint)
    if match:
        return match.group(1)
    return None


def interactive_select(outdated_npm, outdated_pypi, pypi_packages):
    """Interactive selection of packages to update."""
    all_packages = []
    
    # Format npm packages
    idx = 1
    for pkg_name, info in outdated_npm.items():
        current = info.get("current", "?")
        latest = info.get("latest", "?")
        print(f"{idx}. {pkg_name}: {current} -> {latest} (npm)")
        all_packages.append(("npm", pkg_name, info))
        idx += 1
    
    # Format PyPI packages
    outdated_dict = get_pypi_outdated()
    for pkg in pypi_packages:
        if pkg["is_comment"] or not pkg["name"]:
            continue
        pkg_lower = pkg["name"].lower()
        if pkg_lower in outdated_dict:
            outdated_info = outdated_dict[pkg_lower]
            current = outdated_info.get("version", "?")
            latest = outdated_info.get("latest_version", outdated_info.get("latest", {}).get("version", "?"))
            print(f"{idx}. {pkg['name']}: {current} -> {latest} (pypi)")
            all_packages.append(("pypi", pkg["name"], {
                "current": current,
                "latest": latest,
                "original": pkg
            }))
            idx += 1
    
    if not all_packages:
        return []
    
    # Get user input with validation
    while True:
        selection = input("Select packages (comma-separated indices, 'all', or 'skip'): ").strip()
        
        if selection.lower() == "skip" or not selection:
            return []
        
        if selection.lower() == "all":
            return all_packages
        
        # Parse comma-separated indices and ranges
        try:
            indices = []
            for part in selection.split(","):
                part = part.strip()
                if "-" in part:
                    # Handle range like "1-3"
                    start, end = map(int, part.split("-"))
                    indices.extend(range(start, end + 1))
                else:
                    indices.append(int(part))
            
            # Validate indices
            selected = []
            for i in indices:
                if 1 <= i <= len(all_packages):
                    selected.append(all_packages[i - 1])
                else:
                    print(f"Warning: Index {i} is out of range, skipping", file=sys.stderr)
            
            return selected
        except ValueError:
            print("Invalid input. Please enter comma-separated numbers, ranges (e.g., 1-3), 'all', or 'skip'.", file=sys.stderr)
            continue


def update_package_json(updates, deps, dev_deps):
    """Update package.json with new versions, preserving prefixes."""
    pkg_path = Path("/app/package.json")
    with open(pkg_path) as f:
        data = json.load(f)
    
    for ecosystem, pkg_name, info in updates:
        if ecosystem == "npm":
            latest = info.get("latest", "")
            # Preserve existing version prefix (^, ~, etc.)
            if pkg_name in deps:
                old_version = deps[pkg_name]
                prefix = ""
                if old_version.startswith("^"):
                    prefix = "^"
                elif old_version.startswith("~"):
                    prefix = "~"
                elif old_version.startswith(">="):
                    prefix = ">="
                data["dependencies"][pkg_name] = f"{prefix}{latest}"
            elif pkg_name in dev_deps:
                old_version = dev_deps[pkg_name]
                prefix = ""
                if old_version.startswith("^"):
                    prefix = "^"
                elif old_version.startswith("~"):
                    prefix = "~"
                elif old_version.startswith(">="):
                    prefix = ">="
                if "devDependencies" not in data:
                    data["devDependencies"] = {}
                data["devDependencies"][pkg_name] = f"{prefix}{latest}"
    
    with open(pkg_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def update_requirements_txt(updates, original_packages):
    """Update requirements.txt with new versions, preserving comments and formatting."""
    req_path = Path("/app/requirements.txt")
    
    # Create a mapping of package names to new versions
    update_map = {}
    for ecosystem, pkg_name, info in updates:
        if ecosystem == "pypi":
            latest = info.get("latest", "")
            update_map[pkg_name.lower()] = latest
    
    # Rebuild file preserving structure
    lines = []
    for pkg in original_packages:
        if pkg["is_comment"] or not pkg["name"]:
            # Preserve comments and empty lines
            lines.append(pkg["original"].rstrip())
        else:
            pkg_lower = pkg["name"].lower()
            if pkg_lower in update_map:
                # Update version
                new_version = update_map[pkg_lower]
                lines.append(f"{pkg['name']}=={new_version}")
            else:
                # Preserve original line
                lines.append(pkg["original"].rstrip())
    
    with open(req_path, "w") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")


def regenerate_lockfiles():
    """Regenerate npm and pip lockfiles."""
    # Use npm install (not npm ci) to update lockfile
    try:
        subprocess.run(
            ["npm", "install"],
            cwd="/app",
            check=True,
            timeout=300,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Warning: npm install failed: {e}", file=sys.stderr)
    
    # Use pip-compile to regenerate Python lockfile
    try:
        subprocess.run(
            ["pip-compile", "requirements.txt"],
            cwd="/app",
            check=True,
            timeout=300,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Warning: pip-compile failed (may not be installed): {e}", file=sys.stderr)


def generate_commit_summary(updates):
    """Generate conventional commit summary with proper formatting."""
    npm_updates = []
    pypi_updates = []
    
    for ecosystem, pkg_name, info in updates:
        current = info.get("current", "?")
        latest = info.get("latest", "?")
        if ecosystem == "npm":
            npm_updates.append(f"- {pkg_name}: {current} -> {latest}")
        elif ecosystem == "pypi":
            pypi_updates.append(f"- {pkg_name}: {current} -> {latest}")
    
    summary = "chore(deps): bump npm and PyPI dependencies\n\n"
    
    if npm_updates:
        summary += "npm:\n"
        summary += "\n".join(npm_updates)
        summary += "\n"
    
    if pypi_updates:
        if npm_updates:
            summary += "\n"
        summary += "pypi:\n"
        summary += "\n".join(pypi_updates)
        summary += "\n"
    
    # Write to correct path
    output_path = Path("/app/commit-summary.txt")
    with open(output_path, "w") as f:
        f.write(summary)


def main():
    """Main entry point."""
    print("Reading dependency files...")
    deps, dev_deps = read_package_json()
    pypi_packages = read_requirements_txt()
    
    print("Checking for outdated packages...")
    outdated_npm = get_npm_outdated()
    outdated_pypi_dict = get_pypi_outdated()
    
    # Filter pypi_packages to only those that are outdated
    outdated_pypi = [pkg for pkg in pypi_packages 
                     if not pkg["is_comment"] and pkg["name"] 
                     and pkg["name"].lower() in outdated_pypi_dict]
    
    if not outdated_npm and not outdated_pypi:
        print("No outdated packages found.")
        return
    
    print("\nOutdated packages:")
    updates = interactive_select(outdated_npm, outdated_pypi, pypi_packages)
    
    if not updates:
        print("No packages selected. Exiting.")
        return
    
    print("\nUpdating dependency files...")
    update_package_json(updates, deps, dev_deps)
    update_requirements_txt(updates, pypi_packages)
    
    print("Regenerating lockfiles...")
    regenerate_lockfiles()
    
    print("Generating commit summary...")
    generate_commit_summary(updates)
    
    print("Done!")

if __name__ == "__main__":
    main()
ENDPYTHON

chmod +x dep_bumper.py

echo "Fixed dep_bumper.py with all necessary corrections"
