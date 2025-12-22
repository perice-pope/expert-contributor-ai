# Quality Control — fix-cmake-fpic-openmp-clang

## Manual Review Readiness

- [x] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent - verified: reward 1.0)

- [x] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md - Requirements 1-5 cover all test behaviors)

- [x] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions - verified: Docker build succeeds, Clang/OpenMP available)

- [x] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content - tags: cmake, cpp, openmp, build-system, clang, shared-libraries)

---

## CI / Evaluation Checks

- [x] behavior_in_task_description  
  (EVERY behavior checked by tests is explicitly described in instruction.md - Requirements 4-5 cover build success, executable creation, runtime correctness, and test passing)

- [x] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests - 6 tests cover all requirements: build, library, executable, runtime, calculations, ctest)

- [x] informative_test_docstrings  
  (Each test clearly states what behavior it validates - All 6 tests have clear docstrings)

- [x] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions - Tests verify actual build artifacts and runtime behavior, not source code)

- [ ] structured_data_schema (if applicable)  
  (Exact schema is documented in task.yaml or an explicitly referenced file)

- [x] pinned_dependencies  
  (All non-apt dependencies are version pinned - Dockerfile pins: build-essential=12.9, cmake=3.25.1-1, clang=1:14.0-55.7~deb12u1, libomp-dev=1:14.0-55.7~deb12u1)

- [x] typos  
  (No typos in filenames, variables, paths, or instructions - Verified: all paths and names correct)

- [x] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image - Verified: Dockerfile only copies app/, no solution/ or tests/)

- [x] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time - Verified: test.sh installs uv and pytest at runtime)

- [x] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers - Solution fixes CMakeLists.txt and builds project)

- [x] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions - /app/build/libmath_utils.so, /app/build/calculator mentioned in Outputs section)

- [x] check_canary  
  (Required canary string exists at top of all required files - Verified: # CANARY_STRING_PLACEHOLDER in solution/solve.sh)

- [x] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files - Verified: only copies app/, no solution/ or tests/)

- [x] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope - Verified: test.sh uses uvx with pytest)

- [x] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones - Verified: all paths use /app/ prefix)

- [x] check_test_file_references  
  (Files referenced in tests are declared in task.yaml - N/A: using task.toml, files mentioned in instruction.md Files section)

- [x] check_files  
  (No extraneous files exist outside the task directory - Verified: only required files present)

- [x] check_privileged_containers  
  (No privileged containers are used - Verified: docker-compose.yaml has no privileged: true)

- [x] check_task_sizes  
  (All files are under 1MB - Verified: source files are small, largest is CMake build artifacts which are excluded from submission)

- [x] validate_task_fields  
  (All required task.toml fields are present and valid - Verified: version, metadata, verifier, agent, environment sections present)

---

## Result

### Code Quality Checks: ✅ ALL PASSED
<!-- Change to ✅ ALL PASSED only when every box above is checked -->

⚠️ **SCOPE NOTICE:** QC checks validate code quality and structure.
They do NOT replace verification steps (4, 7, 8, 9) which require actual execution proof.

See `fix-cmake-fpic-openmp-clang.STATE.md` VERIFICATION GATE for execution status.

