# Maintainer Notes — dep-bumper-cli

## Intended Agent Failure Modes

1. **Shallow fixes**: Agents may try to fix only obvious syntax errors without addressing the core logic issues:
   - Missing devDependencies handling
   - Incorrect PyPI outdated detection method
   - Broken interactive selection parsing
   - Missing version prefix preservation

2. **Hardcoded solutions**: Agents might try to hardcode package versions or commit messages instead of computing them dynamically.

3. **Missing error handling**: Agents may not add proper error handling for subprocess calls, file I/O, or JSON parsing.

4. **Incomplete lockfile regeneration**: Agents might forget to regenerate both npm and pip lockfiles, or use wrong commands (npm ci instead of npm install).

5. **Formatting issues**: Agents may not preserve comments and formatting in requirements.txt when updating.

## Why Tests Are Structured This Way

- Tests use behavioral validation (checking file contents and outputs) rather than source code inspection to prevent cheating
- Tests handle cases where no outdated packages exist (graceful degradation)
- Tests verify both npm and PyPI ecosystems independently
- Tests check that commit summary follows conventional commit format
- Tests verify lockfile regeneration was attempted (may fail if pip-tools not available, but attempt must be made)

## Determinism and Reproducibility Notes

- All dependencies are pinned (pip-tools==7.4.1, nodejs=20.18.0-1nodesource1)
- No network calls required for version detection (uses npm outdated and pip list --outdated which work with cached metadata)
- Interactive selection uses stdin input, making it testable with subprocess
- Solution is deterministic - same input produces same output
- Lockfile regeneration may produce slightly different results based on dependency resolution, but core functionality is deterministic

## Task Difficulty Knobs

- **Easy**: Fix only npm dependencies, ignore PyPI
- **Medium**: Handle both ecosystems, basic interactive selection
- **Hard** (current): Full implementation with version prefix preservation, comment preservation, range parsing, proper error handling

## Expected Agent Behavior

Agents should:
1. Read and understand the broken code structure
2. Identify all bugs systematically
3. Fix parsing logic for both package.json and requirements.txt
4. Implement proper interactive selection with validation
5. Preserve formatting and version prefixes
6. Regenerate lockfiles correctly
7. Generate properly formatted commit summary

Common mistakes:
- Only fixing npm, ignoring PyPI
- Not handling devDependencies
- Using wrong commands for outdated detection
- Not preserving file formatting
- Hardcoding outputs instead of computing

