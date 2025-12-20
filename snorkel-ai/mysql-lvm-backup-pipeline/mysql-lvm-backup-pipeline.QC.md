# Quality Control — mysql-lvm-backup-pipeline

## Manual Review Readiness

- [x] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent)
  - Solution creates proper backup script with MySQL locking, LVM snapshots, rsync, retention, cron, and verification script

- [x] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md)
  - All 10 requirements are clearly numbered and testable
  - Constraints explicitly stated
  - Files and outputs sections list all paths

- [x] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions)
  - Dockerfile installs MySQL, LVM, rsync, cron
  - Init script sets up LVM and MySQL data
  - Environment matches task requirements

- [x] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content)
  - Tags: mysql, lvm, backup, snapshot, cron, shell-scripting, filesystem
  - Difficulty: hard (appropriate for multi-step systems administration task)
  - Category: systems-administration (correct)

---

## CI / Evaluation Checks

- [x] behavior_in_task_description  
  (EVERY behavior checked by tests is explicitly described in instruction.md)
  - Test: backup script exists → Requirement 1-10 (script creation)
  - Test: backup script runs → Requirements 1-9 (all backup operations)
  - Test: backup directory created → Requirement 4 (backup to /backups/mysql)
  - Test: backup contains MySQL data → Requirement 4 (rsync data)
  - Test: log file exists → Requirement 9 (detailed logging)
  - Test: retention policy → Requirement 7 (keep last 7 backups)
  - Test: cron job configured → Requirement 8 (automate with cron)
  - Test: verification script → Requirement 10 (verify restoration)
  - Test: timestamp format → Requirement 4 (backup_YYYYMMDD_HHMMSS)

- [x] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests)
  - Requirement 1 (quiesce MySQL) → test_backup_script_runs_successfully, test_mysql_lock_mechanism
  - Requirement 2 (create LVM snapshot) → test_backup_script_runs_successfully
  - Requirement 3 (mount snapshot) → test_backup_script_runs_successfully
  - Requirement 4 (rsync data) → test_backup_contains_mysql_data
  - Requirement 5 (unmount/remove snapshot) → test_backup_script_runs_successfully
  - Requirement 6 (release MySQL lock) → test_backup_script_runs_successfully
  - Requirement 7 (retention policy) → test_retention_policy_enforced
  - Requirement 8 (cron automation) → test_cron_job_configured
  - Requirement 9 (detailed logging) → test_backup_log_file_exists
  - Requirement 10 (verify restoration) → test_verification_script_exists, test_verification_script_runs

- [x] informative_test_docstrings  
  (Each test clearly states what behavior it validates)
  - All tests have clear docstrings explaining what they validate

- [x] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions)
  - Tests verify actual backup operations (not just file existence)
  - Tests verify backup content (MySQL data files)
  - Tests verify retention policy by running multiple backups
  - Tests verify cron configuration
  - Solution directory not in Docker image

- [x] structured_data_schema (if applicable)  
  (Exact schema is documented in task.yaml or an explicitly referenced file)
  - N/A - no structured data schema required

- [x] pinned_dependencies  
  (All non-apt dependencies are version pinned)
  - Base image: debian:bookworm-slim (pinned)
  - System packages from apt (no version pinning needed per Harbor docs)
  - Test dependencies: pytest==8.4.1, pytest-json-ctrf==0.3.5 (pinned in test.sh)

- [x] typos  
  (No typos in filenames, variables, paths, or instructions)
  - All paths verified: /app/backup_mysql.sh, /backups/mysql, /var/log/mysql_backup.log, etc.
  - All variable names consistent
  - Instruction text reviewed

- [x] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image)
  - Dockerfile only copies app/ directory
  - No COPY solution/ or COPY tests/ commands
  - Verified with grep

- [x] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time)
  - pytest and dependencies installed in test.sh at runtime
  - Not in Dockerfile

- [x] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers)
  - Solution creates backup script that performs actual operations
  - Solution creates verification script that checks backups
  - No hardcoded outputs

- [x] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions)
  - /app/backup_mysql.sh → mentioned in Files section
  - /app/verify_restore.sh → mentioned in Requirements and Files section
  - /backups/mysql/ → mentioned in Requirements and Files section
  - /var/log/mysql_backup.log → mentioned in Requirements and Files section
  - /etc/cron.d/mysql-backup → mentioned in Files section

- [x] check_canary  
  (Required canary string exists at top of all required files)
  - solution/solve.sh contains # CANARY_STRING_PLACEHOLDER at line 2

- [x] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files)
  - Dockerfile only references app/ and environment/init-lvm.sh
  - No solution/ or tests/ references
  - Verified with grep

- [x] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope)
  - test.sh uses uvx with pytest (correct pattern)
  - Python 3.13 specified

- [x] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones)
  - All paths in instruction.md are absolute: /app/, /backups/mysql/, /var/log/, etc.
  - No relative paths found

- [x] check_test_file_references  
  (Files referenced in tests are declared in task.yaml)
  - task.toml doesn't have explicit file declarations (Harbor 2.0 may not require this)
  - All files are mentioned in instruction.md Files section

- [x] check_files  
  (No extraneous files exist outside the task directory)
  - Only expected files present: instruction.md, task.toml, app/, environment/, solution/, tests/, NOTES.md
  - Control files (STATE, DONE, QC) will be removed before ZIP

- [x] check_privileged_containers  
  (No privileged containers are used)
  - Dockerfile doesn't use privileged mode
  - Note: LVM operations may require SYS_ADMIN capability (documented in NOTES.md)

- [x] check_task_sizes  
  (All files are under 1MB)
  - All files are small shell scripts, config files, and test files
  - No large binary files

- [x] validate_task_fields  
  (All required task.yaml fields are present and valid)
  - version: "1.0" ✓
  - metadata.author_name: "anonymous" ✓
  - metadata.author_email: "anonymous" ✓
  - metadata.difficulty: "hard" ✓ (valid: easy/medium/hard)
  - metadata.category: "systems-administration" ✓
  - metadata.tags: array with 7 tags ✓
  - metadata.expert_time_estimate_min: 120 ✓
  - metadata.junior_time_estimate_min: 240 ✓
  - verifier.timeout_sec: 1800.0 ✓
  - agent.timeout_sec: 1800.0 ✓
  - environment.build_timeout_sec: 900.0 ✓
  - environment.cpus: 2 ✓
  - environment.memory_mb: 4096 ✓
  - environment.storage_mb: 20480 ✓

---

## Result

ALL CHECKS PASSED




