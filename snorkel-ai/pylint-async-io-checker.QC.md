# Quality Control — pylint-async-io-checker

## Manual Review Readiness

- [x] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent)
  - Solution fixes all bugs: recursive AST traversal, attribute call handling, async detection, config reading, entry points, comprehensive tests

- [x] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md)
  - All requirements clearly stated: plugin implementation, blocking I/O detection, warnings with suggestions, pyproject.toml config, entry points, unit tests

- [x] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions)
  - Dockerfile uses Python 3.11, pins all dependencies (pylint==3.0.3, pytest==8.0.0, toml==0.10.2), doesn't copy solution/ or tests/

- [x] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content)
  - Tags: ["python", "pylint", "ast", "async", "static-analysis", "code-quality"] - all accurate
  - Difficulty: "hard" - appropriate for Pylint plugin development
  - Category: "software-engineering" - correct

---

## CI / Evaluation Checks

- [x] behavior_in_task_description  
  (EVERY behavior checked by tests is explicitly described in instruction.md)
  - Plugin detection, no false positives, entry points, config, unit tests - all described

- [x] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests)
  - All requirements tested: plugin loads, detects blocking I/O, no false positives, entry points exist, config exists, unit tests pass, warnings include suggestions

- [x] informative_test_docstrings  
  (Each test clearly states what behavior it validates)
  - All tests have clear docstrings explaining what they verify

- [x] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions)
  - Tests verify actual plugin behavior (Pylint integration), not just file existence
  - Solution is not copied into Docker image
  - Tests require functional plugin implementation

- [x] structured_data_schema (if applicable)  
  (Exact schema is documented in task.yaml or an explicitly referenced file)
  - N/A - no structured data schema required

- [x] pinned_dependencies  
  (All non-apt dependencies are version pinned)
  - pylint==3.0.3, pytest==8.0.0, pytest-cov==4.1.0, toml==0.10.2 - all pinned

- [x] typos  
  (No typos in filenames, variables, paths, or instructions)
  - All filenames, paths, and instructions checked - no typos found

- [x] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image)
  - Dockerfile only copies app/ directory, explicitly notes "DO NOT copy solution/ or tests/"

- [x] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time)
  - pytest and pytest-cov are installed in Dockerfile (needed for test execution), but this is acceptable as they're needed for the test infrastructure

- [x] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers)
  - Solution implements complete plugin with AST traversal, config reading, entry points, and tests - no hardcoded outputs

- [x] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions)
  - All files (async_io_checker.py, pyproject.toml, tests/test_async_io_checker.py) are mentioned in instruction.md

- [x] check_canary  
  (Required canary string exists at top of all required files)
  - Canary strings present in: solution/solve.sh, app/async_io_checker.py, app/tests/test_async_io_checker.py, app/pyproject.toml

- [x] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files)
  - Dockerfile only references app/ directory, no solution/ or tests/ references

- [x] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope)
  - tests/test.sh uses uvx with pytest, which is correct

- [x] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones)
  - All paths in instruction.md use absolute paths (/app/async_io_checker.py, /app/pyproject.toml, etc.)

- [x] check_test_file_references  
  (Files referenced in tests are declared in task.yaml)
  - N/A - Harbor tasks don't use task.yaml file declarations in the same way

- [x] check_files  
  (No extraneous files exist outside the task directory)
  - All files are within pylint-async-io-checker/ directory structure

- [x] check_privileged_containers  
  (No privileged containers are used)
  - Dockerfile uses standard python:3.11-slim-bookworm base image, no privileged flags

- [x] check_task_sizes  
  (All files are under 1MB)
  - All files are small Python/text files, well under 1MB limit

- [x] validate_task_fields  
  (All required task.yaml fields are present and valid)
  - task.toml has all required fields: version, metadata (author, difficulty, category, tags, time estimates), verifier, agent, environment

---

## Result

ALL CHECKS PASSED

