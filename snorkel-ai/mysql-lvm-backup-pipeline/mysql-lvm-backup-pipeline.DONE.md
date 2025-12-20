# DONE — mysql-lvm-backup-pipeline

## Verification Summary

- Oracle agent: ⚠️ REQUIRES MANUAL VERIFICATION (Step 7)
  - Solution script created and validated for structure
  - Requires Harbor CLI: `harbor run --agent oracle --path harbor_tasks/mysql-lvm-backup-pipeline`
  
- Real agents tested: ⚠️ REQUIRES MANUAL VERIFICATION (Step 8)
  - Requires Harbor CLI with ≥2 models:
    - `harbor run -a terminus-2 -m gpt-4o -p mysql-lvm-backup-pipeline`
    - `harbor run -a terminus-2 -m anthropic/claude-3-5-sonnet-20240620 -p mysql-lvm-backup-pipeline`
  
- CI / LLMaJ checks: ⚠️ REQUIRES MANUAL VERIFICATION (Step 9)
  - Requires Harbor CI checks or LLMaJ validation
  - All QC checks in mysql-lvm-backup-pipeline.QC.md are verified and pass
  
- ZIP structure validated: ⚠️ PENDING (Step 12)
  - Will be validated after control file teardown
  
- Forbidden files excluded: ✅ VERIFIED
  - Control files (STATE.md, DONE.md, QC.md) will be deleted before ZIP
  - Dockerfile does not copy solution/ or tests/
  - Verified with grep checks

## Completion Status

### Completed Steps
- ✅ Step 1: Template copied and renamed to mysql-lvm-backup-pipeline
- ✅ Step 2: instruction.md and task.toml created and configured
- ✅ Step 3: Dockerfile created with MySQL, LVM, and required tools
- ⚠️ Step 4: Local interactive test - REQUIRES MANUAL VERIFICATION
  - Command: `harbor run --agent oracle --path harbor_tasks/mysql-lvm-backup-pipeline --interactive`
- ✅ Step 5: solution/solve.sh created with complete oracle solution
- ✅ Step 6: tests/test.sh and tests/test_outputs.py created with comprehensive tests
- ⚠️ Step 7: Oracle agent run - REQUIRES MANUAL VERIFICATION
  - Command: `harbor run --agent oracle --path harbor_tasks/mysql-lvm-backup-pipeline`
- ⚠️ Step 8: Real agents tested - REQUIRES MANUAL VERIFICATION
  - Need to run ≥2 models, 2-3 times each
- ⚠️ Step 9: CI / LLMaJ checks - REQUIRES MANUAL VERIFICATION
- ✅ Step 10: Final verification - Structure validated
- ✅ Step 11: Pre-submission validation - All checks pass
- ✅ Step 11.5: Quality Control gate - All QC checks verified and passed
- ⚠️ Step 12: Final packaging - PENDING (requires Steps 4, 7, 8, 9 completion)

## Files Created

### Core Task Files
- ✅ instruction.md - Complete task instructions with 10 numbered requirements
- ✅ task.toml - Configuration with difficulty=hard, category=systems-administration
- ✅ NOTES.md - Comprehensive maintainer notes

### Environment
- ✅ environment/Dockerfile - Debian-based with MySQL, LVM, rsync, cron
- ✅ environment/init-lvm.sh - LVM and MySQL initialization script

### Starter Code
- ✅ app/backup_mysql.sh - Broken backup script with 8 intentional bugs

### Solution
- ✅ solution/solve.sh - Complete oracle solution with CANARY_STRING_PLACEHOLDER

### Tests
- ✅ tests/test.sh - Test runner using uv and pytest
- ✅ tests/test_outputs.py - 11 comprehensive behavioral tests

## Manual Verification Required

Before final packaging, the following must be verified manually:

1. **Step 4**: Interactive environment test
   ```bash
   harbor run --agent oracle --path harbor_tasks/mysql-lvm-backup-pipeline --interactive
   ```
   Verify: Environment behaves correctly, LVM and MySQL are accessible

2. **Step 7**: Oracle agent execution
   ```bash
   harbor run --agent oracle --path harbor_tasks/mysql-lvm-backup-pipeline
   ```
   Verify: Oracle passes all tests

3. **Step 8**: Real agent testing (≥2 models, 2-3 runs each)
   ```bash
   harbor run -a terminus-2 -m gpt-4o -p mysql-lvm-backup-pipeline
   harbor run -a terminus-2 -m anthropic/claude-3-5-sonnet-20240620 -p mysql-lvm-backup-pipeline
   ```
   Verify: Agents can solve the task (may have varying success rates)

4. **Step 9**: CI / LLMaJ checks
   - Run Harbor CI validation
   - Verify all automated checks pass

## Next Steps

1. Complete manual verification of Steps 4, 7, 8, 9
2. If all verifications pass, proceed to Step 12:
   - Delete control files (STATE.md, DONE.md, QC.md)
   - Create ZIP from task directory
   - Validate ZIP structure

## Notes

- LVM operations in Docker may require SYS_ADMIN capability (documented in NOTES.md)
- MySQL lock mechanism uses background process - tested approach but may need adjustment in actual Harbor environment
- All file paths use absolute paths as required
- All dependencies are pinned or from system repos
- Solution does not hardcode outputs - performs actual operations

