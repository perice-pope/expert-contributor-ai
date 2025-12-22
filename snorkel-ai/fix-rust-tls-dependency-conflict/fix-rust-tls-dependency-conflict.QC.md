# Quality Control — fix-rust-tls-dependency-conflict

## Manual Review Readiness

- [x] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent)
  - Solution modifies Cargo.toml to use rustls-tls instead of native-tls
  - Solution verified manually: `cargo build` and `cargo test` succeed after fix

- [x] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md)
  - Requirements clearly state: diagnose, fix dependency conflict, ensure build and test success
  - Three solution options provided (rustls-tls, vendored OpenSSL, install libssl-dev)
  - Constraints clearly stated (no logic changes, may modify Cargo.toml)

- [x] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions)
  - Dockerfile uses rust:1.83-slim-bookworm
  - Intentionally does NOT install libssl-dev to create openssl-sys build failure
  - Starter project fails to build (verified: openssl-sys cannot find OpenSSL)

- [x] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content)
  - Tags: ["rust", "dependency-management", "tls", "build-failure", "debugging"]
  - Difficulty: medium
  - Category: software-engineering

---

## CI / Evaluation Checks

- [x] behavior_in_task_description  
  (EVERY behavior checked by tests is explicitly described in instruction.md)
  - Test: cargo build succeeds → Requirement 3: "Ensure successful build"
  - Test: cargo test succeeds → Requirement 4: "Ensure successful tests"
  - Test: Cargo.toml modified → Requirement 2: "Fix the dependency conflict"

- [x] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests)
  - Requirement 1 (diagnose): Not directly tested (diagnosis is agent's work, fix is validated)
  - Requirement 2 (fix): Tested via Cargo.toml modification check
  - Requirement 3 (build): Tested via cargo build execution
  - Requirement 4 (tests): Tested via cargo test execution

- [x] informative_test_docstrings  
  (Each test clearly states what behavior it validates)
  - test_cargo_build_succeeds: "Test that cargo build completes successfully after the fix"
  - test_cargo_test_succeeds: "Test that cargo test completes successfully with all tests passing"
  - test_cargo_toml_modified: "Test that Cargo.toml has been modified to use rustls-tls"
  - test_binary_exists_after_build: "Test that the built binary exists after successful build"

- [x] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions)
  - Tests run actual cargo commands (cannot be faked)
  - Tests verify Cargo.toml modification (cannot just echo success)
  - Tests verify binary exists (requires actual build)
  - Solution directory not in Docker image

- [x] structured_data_schema (if applicable)  
  (Exact schema is documented in task.yaml or an explicitly referenced file)
  - N/A - No structured data output required

- [x] pinned_dependencies  
  (All non-apt dependencies are version pinned)
  - Rust version: 1.83 (pinned in Dockerfile)
  - reqwest: 0.11 (pinned in Cargo.toml)
  - tokio-rustls: 0.24 (pinned in Cargo.toml)
  - tokio: 1 (pinned in Cargo.toml)

- [x] typos  
  (No typos in filenames, variables, paths, or instructions)
  - Verified: All file names, paths, and instructions checked

- [x] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image)
  - Dockerfile only copies app/ directory
  - .dockerignore excludes solution/ and tests/ (though not explicitly needed since COPY only copies app/)

- [x] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time)
  - Test dependencies (pytest, uv) are installed in test.sh, not Dockerfile

- [x] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers)
  - Solution modifies Cargo.toml using sed
  - Solution runs cargo build and cargo test to verify fix
  - No hardcoded outputs

- [x] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions)
  - Tests reference /app/Cargo.toml → Mentioned in instruction.md Files section
  - Tests reference /app/target/debug/tls-client → Implied by build requirement

- [x] check_canary  
  (Required canary string exists at top of all required files)
  - solution/solve.sh: Contains "# CANARY_STRING_PLACEHOLDER" at line 2

- [x] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files)
  - Dockerfile only references app/ directory
  - No references to solution/ or tests/

- [x] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope)
  - tests/test.sh uses uvx (system-wide scope via uvx)

- [x] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones)
  - instruction.md uses /app/Cargo.toml, /app/src/main.rs (absolute paths)

- [x] check_test_file_references  
  (Files referenced in tests are declared in task.yaml)
  - N/A - task.toml doesn't require file declarations for this task type

- [x] check_files  
  (No extraneous files exist outside the task directory)
  - All files are within fix-rust-tls-dependency-conflict/ directory

- [x] check_privileged_containers  
  (No privileged containers are used)
  - Dockerfile uses standard rust:1.83-slim-bookworm base image
  - No privileged flags

- [x] check_task_sizes  
  (All files are under 1MB)
  - All source files are small (Cargo.toml, main.rs, test files, etc.)
  - No large binary files included

- [x] validate_task_fields  
  (All required task.yaml fields are present and valid)
  - task.toml has all required fields: version, metadata (author, difficulty, category, tags), verifier, agent, environment

---

## Result

### Code Quality Checks: ✅ ALL PASSED

⚠️ **SCOPE NOTICE:** QC checks validate code quality and structure.
They do NOT replace verification steps (4, 7, 8, 9) which require actual execution proof.

See `fix-rust-tls-dependency-conflict.STATE.md` VERIFICATION GATE for execution status.

