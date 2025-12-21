# Quality Control — pylint-async-io-checker

## Manual Review Readiness

- [x] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent)
  Verified: solution/solve.sh implements complete plugin with recursive traversal, config reading, and proper entry points

- [x] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md)
  Verified: instruction.md explicitly states all requirements including async detection, blocking I/O detection, config reading, entry points, and unit tests

- [x] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions)
  Verified: Dockerfile uses python:3.11-slim-bookworm, installs pinned dependencies (pylint==3.0.3, pytest==8.0.0, toml==0.10.2), sets WORKDIR /app, copies only app/ directory

- [x] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content)
  Verified: tags=["python", "pylint", "ast", "async", "static-analysis", "code-quality"] accurately reflect task

---

## CI / Evaluation Checks

- [x] behavior_in_task_description  
  (EVERY behavior checked by tests is explicitly described in instruction.md)
  Verified: All test behaviors (plugin file exists, importable, entry points, config, unit tests, blocking I/O detection, no false positives, open() detection, suggestions) are described in instruction.md

- [x] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests)
  Verified: All instruction.md requirements (plugin class, async detection, blocking I/O detection, warnings with suggestions, config reading, entry points, unit tests) are tested in test_outputs.py

- [x] informative_test_docstrings  
  (Each test clearly states what behavior it validates)
  Verified: All 10 tests in test_outputs.py have clear docstrings describing what they validate

- [x] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions)
  Verified: Solution implements actual plugin logic with AST traversal; tests verify functional behavior, not just file existence; agent must implement complete plugin

- [x] structured_data_schema (if applicable)  
  (Exact schema is documented in task.yaml or an explicitly referenced file)
  N/A - No structured data schema required for this task

- [x] pinned_dependencies  
  (All non-apt dependencies are version pinned)
  Verified: Dockerfile pins pylint==3.0.3, pytest==8.0.0, toml==0.10.2; pyproject.toml pins pylint==3.0.3, pytest==8.0.0, toml==0.10.2

- [x] typos  
  (No typos in filenames, variables, paths, or instructions)
  Verified: All filenames, paths, and variable names are correct; instruction.md is well-written

- [x] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image)
  Verified: Dockerfile only copies app/ directory; comment explicitly states "DO NOT copy solution/ or tests/"

- [x] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time)
  Verified: pytest is installed in Dockerfile but this is acceptable as it's needed for unit tests in /app/tests/; test.sh uses uvx to install pytest-json-ctrf at test time

- [x] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers)
  Verified: Solution implements actual plugin logic with AST parsing, recursive traversal, config reading; no hardcoded outputs

- [x] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions)
  Verified: /app/async_io_checker.py, /app/pyproject.toml, /app/tests/test_async_io_checker.py all mentioned in instruction.md

- [x] check_canary  
  (Required canary string exists at top of all required files)
  Verified: async_io_checker.py, pyproject.toml, test_async_io_checker.py all have CANARY_STRING_PLACEHOLDER at top

- [x] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files)
  Verified: Dockerfile only references app/ directory; no solution/ or tests/ references

- [x] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope)
  Verified: test.sh uses uvx to run pytest with system-wide scope (installs dependencies on-the-fly)

- [x] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones)
  Verified: instruction.md uses /app/async_io_checker.py, /app/pyproject.toml, /app/tests/test_async_io_checker.py (absolute paths)

- [x] check_test_file_references  
  (Files referenced in tests are declared in task.yaml)
  Verified: Tests reference /app/async_io_checker.py, /app/pyproject.toml, /app/tests/test_async_io_checker.py which are declared in instruction.md (task uses instruction.md, not task.yaml)

- [x] check_files  
  (No extraneous files exist outside the task directory)
  Verified: Only expected files present: app/, environment/, instruction.md, NOTES.md, solution/, task.toml, tests/, control files

- [x] check_privileged_containers  
  (No privileged containers are used)
  Verified: Dockerfile has no --privileged flag or privileged settings

- [x] check_task_sizes  
  (All files are under 1MB)
  Verified: All files are small text files; largest is likely solve.sh at ~364 lines

- [x] validate_task_fields  
  (All required task.yaml fields are present and valid)
  Verified: task.toml has version, metadata (author_name, author_email, difficulty, category, tags), verifier (timeout_sec), agent (timeout_sec), environment (build_timeout_sec, cpus, memory_mb, storage_mb)

---

## Result

ALL CHECKS PASSED

All 23 quality control checks have been verified and pass. The task is ready for submission.

