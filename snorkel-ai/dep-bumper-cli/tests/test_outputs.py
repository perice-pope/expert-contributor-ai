"""Tests for the dependency bumper CLI tool."""
import json
import os
import re
import stat
import subprocess
from pathlib import Path

APP_DIR = Path("/app")
SCRIPT_PATH = APP_DIR / "dep_bumper.py"

PACKAGE_JSON_CONTENT = """{
  "name": "sample-project",
  "version": "1.0.0",
  "description": "Sample project for dependency bumping",
  "dependencies": {
    "chalk": "4.1.2",
    "express": "^4.18.0",
    "lodash": "~4.17.21"
  },
  "devDependencies": {
    "eslint": ">=8.0.0",
    "jest": "^29.0.0",
    "typescript": "~5.2.0"
  }
}
"""

REQUIREMENTS_CONTENT = """# Core dependencies
requests==2.31.0  # core http client
flask>=3.0.0
uvicorn[standard]~=0.23.0; python_version >= "3.11"

# Development dependencies
pytest==7.4.0
black==23.0.0
"""

NPM_OUTDATED = {
    "express": {"current": "4.18.0", "wanted": "4.18.2", "latest": "4.19.0"},
    "chalk": {"current": "4.1.2", "wanted": "4.1.2", "latest": "5.0.0"},
    "typescript": {"current": "5.2.0", "wanted": "5.2.2", "latest": "5.3.0"},
    "lodash": {"current": "4.17.21", "wanted": "4.17.22", "latest": "4.17.23"}
}

PIP_OUTDATED = [
    {"name": "requests", "version": "2.31.0", "latest_version": "2.32.0"},
    {"name": "flask", "version": "3.0.0", "latest_version": "3.0.2"},
    {"name": "uvicorn", "version": "0.23.0", "latest_version": "0.24.0"},
    {"name": "pytest", "version": "7.4.0", "latest_version": "7.4.2"},
    {"name": "black", "version": "23.0.0", "latest_version": "23.12.0"}
]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _make_stub_env(tmp_path: Path) -> dict:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    npm_json = json.dumps(NPM_OUTDATED)
    pip_json = json.dumps(PIP_OUTDATED)

    _write_executable(
        bin_dir / "npm",
        """#!/bin/sh
set -e
if [ "$1" = "outdated" ]; then
  for arg in "$@"; do
    if [ "$arg" = "--json" ]; then
      cat <<'JSON'
""" + npm_json + """
JSON
      exit 1
    fi
  done
fi
if [ "$1" = "install" ]; then
  echo '{"lockfileVersion": 2}' > /app/package-lock.json
  exit 0
fi
echo "unsupported npm command" >&2
exit 1
""",
    )

    _write_executable(
        bin_dir / "pip",
        """#!/bin/sh
set -e
if [ "$1" = "list" ]; then
  has_outdated=0
  has_format=0
  for arg in "$@"; do
    if [ "$arg" = "--outdated" ]; then
      has_outdated=1
    fi
    if [ "$arg" = "--format=json" ]; then
      has_format=1
    fi
  done
  if [ "$has_outdated" -eq 1 ] && [ "$has_format" -eq 1 ]; then
    cat <<'JSON'
""" + pip_json + """
JSON
    exit 0
  fi
fi
echo "unsupported pip command" >&2
exit 1
""",
    )

    _write_executable(
        bin_dir / "pip-compile",
        """#!/bin/sh
set -e
echo "# compiled" > /app/requirements.txt.lock
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    return env


def _write_fixture_files() -> None:
    (APP_DIR / "package.json").write_text(PACKAGE_JSON_CONTENT)
    (APP_DIR / "requirements.txt").write_text(REQUIREMENTS_CONTENT)

    for path in [
        APP_DIR / "package-lock.json",
        APP_DIR / "requirements.txt.lock",
        APP_DIR / "commit-summary.txt",
    ]:
        if path.exists():
            path.unlink()


def test_dep_bumper_exists():
    """Verify dep_bumper.py script exists and is executable."""
    assert SCRIPT_PATH.exists(), f"Script {SCRIPT_PATH} does not exist"
    assert SCRIPT_PATH.is_file(), f"{SCRIPT_PATH} exists but is not a file"
    assert SCRIPT_PATH.stat().st_mode & 0o111, f"{SCRIPT_PATH} is not executable"


def test_package_json_exists():
    """Verify package.json file exists."""
    pkg_path = APP_DIR / "package.json"
    assert pkg_path.exists(), f"package.json {pkg_path} does not exist"
    assert pkg_path.is_file(), f"{pkg_path} exists but is not a file"


def test_package_json_valid():
    """Verify package.json is valid JSON with dependencies."""
    pkg_path = APP_DIR / "package.json"
    pkg_data = json.loads(pkg_path.read_text())

    assert isinstance(pkg_data, dict), "package.json must be a JSON object"
    assert "dependencies" in pkg_data or "devDependencies" in pkg_data, (
        "package.json must have dependencies or devDependencies"
    )


def test_requirements_txt_exists():
    """Verify requirements.txt file exists."""
    req_path = APP_DIR / "requirements.txt"
    assert req_path.exists(), f"requirements.txt {req_path} does not exist"
    assert req_path.is_file(), f"{req_path} exists but is not a file"


def test_cli_updates_selected_packages_and_preserves_formatting(tmp_path):
    """Verify selected updates are applied and formatting is preserved."""
    _write_fixture_files()
    env = _make_stub_env(tmp_path)

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH)],
        input="2-3,6,8\n",
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(APP_DIR),
        env=env,
    )

    assert result.returncode == 0, (
        f"CLI should exit cleanly. Output: {result.stdout}\nError: {result.stderr}"
    )

    listed = [
        line.strip()
        for line in result.stdout.splitlines()
        if re.match(r"^\d+\.\s+", line)
    ]
    expected_order = [
        "1. chalk: 4.1.2 -> 5.0.0 (npm)",
        "2. express: 4.18.0 -> 4.19.0 (npm)",
        "3. lodash: 4.17.21 -> 4.17.23 (npm)",
        "4. typescript: 5.2.0 -> 5.3.0 (npm)",
        "5. black: 23.0.0 -> 23.12.0 (pypi)",
        "6. flask: 3.0.0 -> 3.0.2 (pypi)",
        "7. pytest: 7.4.0 -> 7.4.2 (pypi)",
        "8. requests: 2.31.0 -> 2.32.0 (pypi)",
        "9. uvicorn[standard]: 0.23.0 -> 0.24.0 (pypi)",
    ]
    assert listed[: len(expected_order)] == expected_order, (
        "CLI should list outdated packages in deterministic order. "
        f"Got: {listed}"
    )

    pkg_data = json.loads((APP_DIR / "package.json").read_text())
    deps = pkg_data.get("dependencies", {})
    dev_deps = pkg_data.get("devDependencies", {})

    assert deps["express"] == "^4.19.0"
    assert deps["lodash"] == "~4.17.23"
    assert deps["chalk"] == "4.1.2"
    assert dev_deps["typescript"] == "~5.2.0"

    req_lines = (APP_DIR / "requirements.txt").read_text().splitlines()
    assert "requests==2.32.0  # core http client" in req_lines
    assert "flask>=3.0.2" in req_lines
    assert "uvicorn[standard]~=0.23.0; python_version >= \"3.11\"" in req_lines
    assert "pytest==7.4.0" in req_lines
    assert "black==23.0.0" in req_lines


def test_cli_invalid_input_and_generates_summary_and_lockfiles(tmp_path):
    """Verify invalid input is handled and outputs are generated."""
    _write_fixture_files()
    env = _make_stub_env(tmp_path)

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH)],
        input="bad\nall\n",
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(APP_DIR),
        env=env,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "Invalid" in combined_output, (
        "CLI should warn on invalid input and re-prompt. "
        f"Output: {combined_output}"
    )

    summary_path = APP_DIR / "commit-summary.txt"
    assert summary_path.exists(), "commit-summary.txt should be created"

    summary = summary_path.read_text()
    assert summary.startswith("chore(deps):"), "Summary should use conventional commit format"
    assert "npm:" in summary
    assert "pypi:" in summary
    assert "- express: 4.18.0 -> 4.19.0" in summary
    assert "- uvicorn[standard]: 0.23.0 -> 0.24.0" in summary

    assert (APP_DIR / "package-lock.json").exists(), "package-lock.json should be created"
    assert (APP_DIR / "requirements.txt.lock").exists(), "requirements.txt.lock should be created"
