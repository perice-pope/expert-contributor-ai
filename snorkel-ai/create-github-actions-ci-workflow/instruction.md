# Create GitHub Actions CI/CD Workflow

A Python/Node.js project needs a complete CI/CD pipeline using GitHub Actions. The workflow file is missing or incomplete. You must create a `.github/workflows/ci.yml` file that runs a matrix build across multiple operating systems and language versions, implements dependency caching, runs linting and testing, uploads coverage reports, and automatically publishes to PyPI and npm when semver git tags are pushed.

## Requirements

1. **Create workflow file**: Create the file `/app/.github/workflows/ci.yml` with a complete GitHub Actions workflow configuration.

2. **Matrix build configuration**: Configure a matrix strategy that runs jobs on:
   - Operating systems: `ubuntu-latest` and `windows-latest`
   - Python versions: `3.8`, `3.9`, `3.10`
   - Node.js versions: `14`, `16`
   - The matrix should include all combinations of these values

3. **Dependency caching**: Implement caching for both Python and Node.js dependencies:
   - Cache pip dependencies using the `actions/cache@v3` action with a cache key based on `requirements.txt` or `pyproject.toml` hash
   - Cache npm dependencies using `actions/cache@v3` with a cache key based on `package-lock.json` or `package.json` hash
   - Use appropriate cache paths for each platform (pip cache on Ubuntu/Windows, npm cache on Ubuntu/Windows)

4. **Install dependencies**: Add steps to install dependencies:
   - Install Python dependencies using pip (with `--cache-dir` pointing to cached directory if available)
   - Install Node.js dependencies using npm (with `--cache` pointing to cached directory if available)
   - Handle both Ubuntu and Windows platforms appropriately

5. **Linting**: Add linting steps for both Python and Node.js:
   - Run Python linter (e.g., `pylint`, `flake8`, or `ruff`) on Python source files
   - Run Node.js linter (e.g., `eslint`) on JavaScript/TypeScript source files
   - Linting failures should fail the job

6. **Testing**: Add testing steps:
   - Run Python tests (e.g., using `pytest`)
   - Run Node.js tests (e.g., using `npm test` or `jest`)
   - Test failures should fail the job

7. **Coverage upload**: Upload test coverage reports:
   - Generate coverage reports for both Python and Node.js tests
   - Upload coverage to a coverage service (e.g., `codecov` or `coveralls`) or as workflow artifacts
   - Coverage upload should occur for all matrix combinations

8. **Conditional publishing on semver tags**: Add a conditional job that runs only on semver git tags (e.g., `v1.0.0`, `v2.1.3`):
   - Detect semver tags using GitHub Actions conditions (e.g., `startsWith(github.ref, 'refs/tags/v')`)
   - Publish Python package to PyPI using `pypa/gh-action-pypi-publish@release/v1` or equivalent
   - Publish Node.js package to npm using `actions/setup-node@v3` with `registry-url` and `publish-npm` or equivalent
   - Use encrypted secrets: `PYPI_API_TOKEN` for PyPI and `NPM_TOKEN` for npm
   - Publishing should only occur after all matrix build jobs succeed

9. **Workflow structure**: Ensure the workflow follows GitHub Actions best practices:
   - Use appropriate action versions (e.g., `actions/checkout@v3`, `actions/setup-python@v4`, `actions/setup-node@v3`)
   - Use `on: push` and `on: pull_request` triggers (at minimum)
   - Use `on: push: tags` with pattern matching for semver tags
   - Jobs should have descriptive names
   - Steps should have descriptive names

## Constraints

- **Do not modify** any source code files (Python, JavaScript, TypeScript, etc.)
- **Do not modify** `package.json`, `requirements.txt`, `pyproject.toml`, or other dependency files
- **Do not modify** existing test files or test configuration
- **Workflow file must be valid YAML** and follow GitHub Actions syntax
- **Use GitHub Actions marketplace actions** where appropriate (do not create custom actions)
- **Secrets must be referenced** using `${{ secrets.SECRET_NAME }}` syntax
- **Matrix strategy must include all specified combinations** (OS × Python × Node.js)
- **Caching must be implemented** for both pip and npm dependencies
- **Publishing must be conditional** on semver tags only (not on every push)

## Files

- Project root: `/app/` (contains Python and Node.js project files)
- Workflow file location: `/app/.github/workflows/ci.yml` (must be created)
- Python project files: `/app/` (may contain `setup.py`, `pyproject.toml`, `requirements.txt`, Python source files)
- Node.js project files: `/app/` (contains `package.json`, may contain `package-lock.json`, JavaScript/TypeScript source files)

## Outputs

- **Workflow file**: `/app/.github/workflows/ci.yml`
  - Must be valid YAML
  - Must contain matrix build configuration
  - Must contain dependency caching
  - Must contain linting steps
  - Must contain testing steps
  - Must contain coverage upload
  - Must contain conditional publishing on semver tags
