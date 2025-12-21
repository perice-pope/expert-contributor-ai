# Maintainer Notes — create-github-actions-ci-workflow

## Task Overview

This task requires agents to create a complete GitHub Actions CI/CD workflow file that implements:
- Matrix builds across multiple OS and language versions
- Dependency caching
- Linting and testing
- Coverage upload
- Conditional publishing on semver tags

## Intended Agent Failure Modes

1. **Incomplete matrix configuration**: Agents may only include some OS or version combinations, missing required values
2. **Missing caching**: Agents may forget to implement caching for pip or npm dependencies
3. **Platform-specific issues**: Agents may not handle Windows vs Ubuntu differences in cache paths or commands
4. **Incorrect conditional logic**: Agents may not properly implement the semver tag detection for publishing
5. **Missing secrets**: Agents may hardcode tokens or forget to use `secrets.PYPI_API_TOKEN` and `secrets.NPM_TOKEN`
6. **YAML syntax errors**: Agents may create invalid YAML that fails validation
7. **Missing steps**: Agents may skip linting, testing, or coverage upload steps
8. **Wrong action versions**: Agents may use outdated or incorrect GitHub Actions versions

## Test Design Rationale

Tests validate:
- **File existence**: Basic requirement - workflow file must exist
- **YAML validity**: Ensures the file can be parsed by GitHub Actions
- **Matrix completeness**: Verifies all required OS (Ubuntu, Windows) and versions (Python 3.8-3.10, Node.js 14/16) are included
- **Caching implementation**: Checks for both pip and npm caching using actions/cache
- **Linting steps**: Validates Python and Node.js linting are present
- **Testing steps**: Validates Python and Node.js testing are present
- **Coverage upload**: Ensures coverage reporting is implemented
- **Conditional publishing**: Validates semver tag detection and secret usage for PyPI and npm publishing
- **Triggers**: Ensures appropriate workflow triggers (push, pull_request, tags)

Tests use YAML parsing to validate structure rather than simple string matching, making them more robust against formatting variations.

## Determinism and Reproducibility

- **No network calls**: Tests validate file structure and content only
- **Pinned dependencies**: Dockerfile uses pinned Python and Node.js versions
- **Static validation**: Tests parse YAML and check for required elements
- **No randomness**: All test checks are deterministic

## Difficulty Knobs

- **Easy**: Simple workflow with basic matrix, no caching
- **Medium (current)**: Full matrix with caching, linting, testing, coverage, conditional publishing
- **Hard**: Add additional complexity like build artifacts, multiple jobs with dependencies, custom actions

## Edge Cases Covered

- Windows vs Ubuntu path differences in caching
- Multiple Python and Node.js versions in matrix
- Conditional publishing only on semver tags (not on every push)
- Secret usage for publishing (not hardcoded tokens)
- Coverage upload for both Python and Node.js

## Why Tests Are Structured This Way

1. **Behavioral validation**: Tests check what the workflow does, not how it's formatted
2. **YAML parsing**: Uses PyYAML to validate structure, catching syntax errors
3. **Comprehensive checks**: Each requirement maps to a specific test
4. **No source grepping**: Tests parse the YAML structure rather than using regex on raw text
5. **Clear failure messages**: Each test has a descriptive assertion message

