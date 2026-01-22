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

APP_DIR = Path("/app")
PACKAGE_JSON_PATH = APP_DIR / "package.json"
REQUIREMENTS_PATH = APP_DIR / "requirements.txt"

REQ_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)"
    r"(?P<extras>\[[^\]]+\])?"
    r"\s*(?P<op>==|>=|<=|~=|!=|>|<)\s*"
    r"(?P<version>[^\s]+)$"
)
COMMENT_RE = re.compile(r"^(?P<content>.*?)(?P<comment>\s+#.*)?$")
MARKER_RE = re.compile(r"^(?P<req>.*?)(?P<marker>\s*;.*)?$")


def read_package_json():
    """Read package.json and extract dependencies and devDependencies."""
    if not PACKAGE_JSON_PATH.exists():
        return {}, {}

    try:
        data = json.loads(PACKAGE_JSON_PATH.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error reading package.json: {exc}", file=sys.stderr)
        return {}, {}

    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    return deps, dev_deps


def _parse_requirement_line(line):
    """Parse a single requirements.txt line into structured parts."""
    leading = line[: len(line) - len(line.lstrip())]
    content = line.lstrip()

    comment_match = COMMENT_RE.match(content)
    if not comment_match:
        return None

    content = comment_match.group("content")
    comment = comment_match.group("comment") or ""

    marker_match = MARKER_RE.match(content)
    if not marker_match:
        return None

    req_part = marker_match.group("req").rstrip()
    marker = marker_match.group("marker") or ""

    if not req_part:
        return None

    req_match = REQ_RE.match(req_part.strip())
    if not req_match:
        return None

    name = req_match.group("name")
    extras = req_match.group("extras") or ""
    op = req_match.group("op")
    version = req_match.group("version")

    return {
        "kind": "requirement",
        "leading": leading,
        "name": name,
        "extras": extras,
        "display": f"{name}{extras}",
        "op": op,
        "version": version,
        "marker": marker,
        "comment": comment,
        "raw": line,
    }


def read_requirements_txt():
    """Read requirements.txt and extract packages with version constraints."""
    if not REQUIREMENTS_PATH.exists():
        return []

    entries = []
    for line in REQUIREMENTS_PATH.read_text().splitlines():
        if not line.strip():
            entries.append({"kind": "blank", "raw": line})
            continue
        if line.lstrip().startswith("#"):
            entries.append({"kind": "comment", "raw": line})
            continue

        parsed = _parse_requirement_line(line)
        if parsed:
            entries.append(parsed)
        else:
            entries.append({"kind": "other", "raw": line})

    return entries


def get_npm_outdated():
    """Get outdated npm packages."""
    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            capture_output=True,
            text=True,
            cwd=str(APP_DIR),
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"Error checking npm outdated: {exc}", file=sys.stderr)
        return {}

    if result.stdout:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}
    return {}


def get_pypi_outdated():
    """Get outdated PyPI packages."""
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"Error checking pip outdated: {exc}", file=sys.stderr)
        return {}

    if result.returncode != 0 or not result.stdout:
        return {}

    try:
        items = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    outdated = {}
    for item in items:
        name = item.get("name")
        if not name:
            continue
        current = item.get("version", "?")
        latest = item.get("latest_version") or item.get("latest") or "?"
        outdated[name.lower()] = {"current": current, "latest": latest}

    return outdated


def _extract_npm_prefix(version_value):
    for prefix in (">=", "<=", "^", "~", ">", "<"):
        if version_value.startswith(prefix):
            return prefix
    return ""


def _parse_selection(selection, max_index):
    if not selection:
        raise ValueError("empty selection")

    indices = []
    for part in selection.split(","):
        part = part.strip()
        if not part:
            raise ValueError("empty segment")
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            if start > end:
                raise ValueError("invalid range")
            indices.extend(range(start, end + 1))
        else:
            indices.append(int(part))

    seen = set()
    unique = []
    for idx in indices:
        if idx not in seen:
            unique.append(idx)
            seen.add(idx)

    if not unique:
        raise ValueError("no indices")

    for idx in unique:
        if idx < 1 or idx > max_index:
            raise ValueError("out of range")

    return unique


def interactive_select(outdated_npm, outdated_pypi, requirements_entries):
    """Interactive selection of packages to update."""
    all_packages = []
    idx = 1

    for pkg_name in sorted(outdated_npm, key=str.lower):
        info = outdated_npm[pkg_name]
        current = info.get("current", "?")
        latest = info.get("latest", "?")
        print(f"{idx}. {pkg_name}: {current} -> {latest} (npm)")
        all_packages.append(
            {
                "ecosystem": "npm",
                "name": pkg_name,
                "current": current,
                "latest": latest,
            }
        )
        idx += 1

    pypi_entries = [
        entry
        for entry in requirements_entries
        if entry.get("kind") == "requirement"
        and entry.get("name", "").lower() in outdated_pypi
    ]

    for entry in sorted(pypi_entries, key=lambda item: item["display"].lower()):
        info = outdated_pypi[entry["name"].lower()]
        current = info.get("current", "?")
        latest = info.get("latest", "?")
        display = entry["display"]
        print(f"{idx}. {display}: {current} -> {latest} (pypi)")
        all_packages.append(
            {
                "ecosystem": "pypi",
                "name": display,
                "base_name": entry["name"],
                "current": current,
                "latest": latest,
            }
        )
        idx += 1

    if not all_packages:
        return []

    while True:
        selection = input(
            "Select packages (comma-separated indices, 'all', or 'skip'): "
        ).strip()

        if selection.lower() == "skip" or not selection:
            return []
        if selection.lower() == "all":
            return all_packages

        try:
            indices = _parse_selection(selection, len(all_packages))
        except ValueError:
            print(
                "Invalid input. Please enter comma-separated numbers, ranges (e.g., 1-3), 'all', or 'skip'.",
                file=sys.stderr,
            )
            continue

        return [all_packages[i - 1] for i in indices]


def update_package_json(updates, deps, dev_deps):
    """Update package.json with new versions, preserving prefixes."""
    if not PACKAGE_JSON_PATH.exists():
        return

    try:
        data = json.loads(PACKAGE_JSON_PATH.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error reading package.json: {exc}", file=sys.stderr)
        return

    for update in updates:
        if update.get("ecosystem") != "npm":
            continue
        pkg_name = update["name"]
        latest = update.get("latest", "")

        if pkg_name in deps:
            prefix = _extract_npm_prefix(deps[pkg_name])
            data.setdefault("dependencies", {})[pkg_name] = f"{prefix}{latest}"
        elif pkg_name in dev_deps:
            prefix = _extract_npm_prefix(dev_deps[pkg_name])
            data.setdefault("devDependencies", {})[pkg_name] = f"{prefix}{latest}"

    PACKAGE_JSON_PATH.write_text(json.dumps(data, indent=2) + "\n")


def update_requirements_txt(updates, requirements_entries):
    """Update requirements.txt with new versions, preserving comments and markers."""
    update_map = {
        update.get("base_name", "").lower(): update.get("latest", "")
        for update in updates
        if update.get("ecosystem") == "pypi"
    }

    lines = []
    for entry in requirements_entries:
        if entry.get("kind") != "requirement":
            lines.append(entry.get("raw", ""))
            continue

        name_key = entry.get("name", "").lower()
        version = entry.get("version", "")
        if name_key in update_map:
            version = update_map[name_key]

        line = (
            f"{entry.get('leading', '')}"
            f"{entry.get('name', '')}"
            f"{entry.get('extras', '')}"
            f"{entry.get('op', '')}"
            f"{version}"
            f"{entry.get('marker', '')}"
            f"{entry.get('comment', '')}"
        )
        lines.append(line)

    REQUIREMENTS_PATH.write_text("\n".join(lines) + ("\n" if lines else ""))


def regenerate_lockfiles():
    """Regenerate npm and pip lockfiles."""
    try:
        subprocess.run(
            ["npm", "install"],
            cwd=str(APP_DIR),
            check=True,
            timeout=300,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"Warning: npm install failed: {exc}", file=sys.stderr)

    try:
        subprocess.run(
            ["pip-compile", "requirements.txt"],
            cwd=str(APP_DIR),
            check=True,
            timeout=300,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(
            "Warning: pip-compile failed (may not be installed): "
            f"{exc}",
            file=sys.stderr,
        )


def generate_commit_summary(updates):
    """Generate conventional commit summary with proper formatting."""
    npm_updates = []
    pypi_updates = []

    for update in updates:
        current = update.get("current", "?")
        latest = update.get("latest", "?")
        line = f"- {update.get('name', '?')}: {current} -> {latest}"
        if update.get("ecosystem") == "npm":
            npm_updates.append(line)
        elif update.get("ecosystem") == "pypi":
            pypi_updates.append(line)

    if not npm_updates and not pypi_updates:
        return

    if npm_updates and pypi_updates:
        header = "chore(deps): bump npm and PyPI dependencies"
    elif npm_updates:
        header = "chore(deps): bump npm dependencies"
    else:
        header = "chore(deps): bump PyPI dependencies"

    summary_lines = [header, ""]

    if npm_updates:
        summary_lines.append("npm:")
        summary_lines.extend(npm_updates)
        summary_lines.append("")

    if pypi_updates:
        summary_lines.append("pypi:")
        summary_lines.extend(pypi_updates)
        summary_lines.append("")

    output_path = APP_DIR / "commit-summary.txt"
    output_path.write_text("\n".join(summary_lines).rstrip() + "\n")


def main():
    """Main entry point."""
    print("Reading dependency files...")
    deps, dev_deps = read_package_json()
    requirements_entries = read_requirements_txt()

    print("Checking for outdated packages...")
    outdated_npm = get_npm_outdated()
    outdated_pypi = get_pypi_outdated()

    has_pypi_outdated = any(
        entry.get("kind") == "requirement"
        and entry.get("name", "").lower() in outdated_pypi
        for entry in requirements_entries
    )

    if not outdated_npm and not has_pypi_outdated:
        print("No outdated packages found.")
        return

    print("\nOutdated packages:")
    updates = interactive_select(outdated_npm, outdated_pypi, requirements_entries)

    if not updates:
        print("No packages selected. Exiting.")
        return

    print("\nUpdating dependency files...")
    update_package_json(updates, deps, dev_deps)
    update_requirements_txt(updates, requirements_entries)

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
