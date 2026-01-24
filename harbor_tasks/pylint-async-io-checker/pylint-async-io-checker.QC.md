# Quality Control — pylint-async-io-checker

## Manual Review Readiness

- [x] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent)

- [x] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md)

- [x] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions)

- [x] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content)

---

## CI / Evaluation Checks (ALL 10 REQUIRED)

- [x] behavior_in_instruction  
  (EVERY behavior checked by tests is explicitly described in instruction.md)

- [x] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests)
  ⚠️ Tests must verify EXECUTION, not just string presence!

- [x] informative_test_docstrings  
  (Each test clearly states what behavior it validates)

- [x] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions)
  ⚠️ Verify outputs against actual system state (API calls), not just file contents!

- [x] structured_data_schema (if applicable)  
  (N/A - no structured schema output required)

- [x] pinned_dependencies  
  (All non-apt dependencies are version pinned)

- [x] typos  
  (No typos in filenames, variables, paths, or instructions)

- [x] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image)

- [x] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time)

- [x] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers)

- [x] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions)

- [x] check_canary  
  (Required canary string exists at top of all required files)

- [x] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files)

- [x] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope)

- [x] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones)

- [x] check_test_file_references  
  (Files referenced in tests are declared in task instructions; task.toml is present)

- [x] check_files  
  (No extraneous files exist outside the task directory)

- [x] check_privileged_containers  
  (No privileged containers are used)

- [x] check_task_sizes  
  (All files are under 1MB)

- [x] validate_task_fields  
  (All required task.toml fields are present and valid)

---

## Result

### Code Quality Checks: ✅ ALL PASSED
<!-- Change to ✅ ALL PASSED only when every box above is checked -->

⚠️ **SCOPE NOTICE:** QC checks validate code quality and structure.
They do NOT replace verification steps (4, 7, 8, 9) which require actual execution proof.

See `pylint-async-io-checker.STATE.md` VERIFICATION GATE for execution status.
