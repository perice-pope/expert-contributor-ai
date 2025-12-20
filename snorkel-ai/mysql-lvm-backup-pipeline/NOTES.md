# Maintainer Notes

## What this task is testing

Agents must implement a complete MySQL database backup pipeline using LVM snapshots. This requires:

1. **MySQL quiescing**: Properly acquire and maintain a read lock on MySQL tables during the snapshot operation to ensure data consistency
2. **LVM snapshot management**: Create, mount, and remove LVM snapshots correctly with proper size specifications
3. **Filesystem operations**: Mount ext4 filesystems, handle mount points, and unmount cleanly
4. **Backup operations**: Use rsync correctly to copy data from the snapshot (not the original volume)
5. **Retention policy**: Implement logic to keep only the last 7 backups, deleting older ones
6. **Automation**: Configure cron jobs with proper scheduling and logging
7. **Logging**: Generate detailed logs for all operations with timestamps and status messages
8. **Verification**: Create a script that validates backup integrity and can verify restoration

The task requires understanding of:
- MySQL administration (FLUSH TABLES WITH READ LOCK, maintaining locks)
- LVM operations (lvcreate, lvremove, snapshot creation)
- Linux filesystem operations (mount, umount, ext4)
- Shell scripting (error handling, background processes, cleanup)
- Cron job configuration
- Backup retention logic (sorting, counting, deletion)

## Intended failure modes

### 1. Missing or incorrect MySQL lock
- **Shallow fix**: Not acquiring lock, or acquiring but not maintaining it during snapshot
- **Pattern**: Forgetting `FLUSH TABLES WITH READ LOCK`, or not keeping connection alive
- **Why it fails**: Without proper locking, MySQL may write during snapshot, causing inconsistent backup
- **Test catches**: Backup may succeed but data integrity tests fail, or MySQL operations fail during backup

### 2. Wrong snapshot source for rsync
- **Shallow fix**: Backing up from `/var/lib/mysql/` instead of mounted snapshot
- **Pattern**: Using original volume path in rsync command
- **Why it fails**: Backs up live data that may change during backup, defeating purpose of snapshot
- **Test catches**: Tests verify backup contains data, but may not catch this subtle bug immediately

### 3. Missing snapshot size specification
- **Shallow fix**: Creating snapshot without `-L` size parameter
- **Pattern**: `lvcreate -s -n mysql_snapshot /dev/vg_mysql/lv_mysql_data` (missing size)
- **Why it fails**: LVM requires size for snapshot creation; command fails
- **Test catches**: `test_backup_script_runs_successfully` fails immediately

### 4. Incorrect retention policy
- **Shallow fix**: Not implementing retention, or keeping wrong number of backups
- **Pattern**: No cleanup logic, or keeping all backups instead of 7
- **Why it fails**: Disk fills up, or doesn't meet requirement of keeping exactly 7
- **Test catches**: `test_retention_policy_enforced` fails if more than 7 backups exist

### 5. Missing error handling and cleanup
- **Shallow fix**: Not cleaning up snapshots or releasing locks on failure
- **Pattern**: No error handling, snapshots left mounted, locks not released
- **Why it fails**: Subsequent backup runs fail due to existing snapshots or locked tables
- **Test catches**: Second backup run fails, or MySQL becomes unusable

### 6. Wrong mount/unmount order
- **Shallow fix**: Unmounting before releasing MySQL lock, or removing snapshot before unmounting
- **Pattern**: Incorrect sequence of operations
- **Why it fails**: May cause data corruption or leave system in inconsistent state
- **Test catches**: Backup may appear to work but verification fails

### 7. Missing cron configuration
- **Shallow fix**: Not creating cron job file, or wrong schedule
- **Pattern**: Forgetting to create `/etc/cron.d/mysql-backup` or wrong cron syntax
- **Why it fails**: Backup doesn't run automatically as required
- **Test catches**: `test_cron_job_configured` fails

### 8. Incomplete logging
- **Shallow fix**: Not logging all operations, or logging to wrong file
- **Pattern**: Missing log statements, or not using `/var/log/mysql_backup.log`
- **Why it fails**: Can't troubleshoot issues, doesn't meet requirement
- **Test catches**: `test_backup_log_file_exists` and log content checks fail

### 9. Missing verification script
- **Shallow fix**: Not creating `verify_restore.sh`, or script doesn't validate backups
- **Pattern**: Forgetting to create script, or script doesn't check backup integrity
- **Why it fails**: Can't verify that backups are restorable
- **Test catches**: `test_verification_script_exists` and `test_verification_script_runs` fail

### 10. Incorrect timestamp format
- **Shallow fix**: Using wrong date format, or not using timestamp in backup directory name
- **Pattern**: Wrong `date` format string, or not including timestamp
- **Why it fails**: Backup directories don't match expected format, retention logic breaks
- **Test catches**: `test_backup_timestamp_format` and directory name pattern matching fail

## Why tests are designed this way

### Behavioral validation over implementation checking
- Tests verify the **outputs** (backup directories, log files, cron config) contain expected content
- Tests don't check specific shell commands used (allows multiple valid approaches)
- Tests verify backup integrity by checking for MySQL data files (not just directory existence)

### Content matching with flexibility
- Tests check for **expected backup structure** (timestamp format, directory structure)
- Allows variations in implementation details (e.g., different error handling approaches)
- Verifies format but not exact log message text (flexible on wording, strict on presence)

### Edge case coverage
- Empty backup checks prevent false positives from empty directories
- Retention policy tests verify cleanup actually happens (not just counting)
- Timestamp format validation ensures backups are sortable and identifiable
- Multiple backup runs test idempotency and cleanup

### Comprehensive operation validation
- Tests verify all major operations: lock, snapshot, mount, backup, unmount, cleanup
- Tests verify automation (cron) and verification (restore script)
- Tests verify logging at each step
- Tests verify retention policy enforcement

## Determinism and reproducibility

### Fixed inputs
- MySQL database is pre-initialized with test data (testdb database with test_table)
- LVM setup is deterministic (same volume group, logical volume names)
- Backup operations are idempotent (can run multiple times safely)

### No external dependencies
- All operations work offline (no network calls)
- MySQL data is pre-populated in Docker image
- No time-dependent behavior beyond timestamps (no sleeps, no polling)

### Tool version pinning
- Debian version pinned: `debian:bookworm-slim`
- MySQL version from Debian bookworm repos (implicitly pinned)
- LVM tools from Debian repos (implicitly pinned)
- Base image pinned: `debian:bookworm-slim`

### Idempotent operations
- Backup script is idempotent (can run multiple times)
- Retention policy is deterministic (always keeps 7 most recent)
- Snapshot operations clean up after themselves

## Task difficulty knobs

### Easy mode (not used here)
- Single backup operation (no retention policy)
- No MySQL locking required
- Simple file copy instead of LVM snapshots

### Medium mode (could be)
- LVM snapshots but simpler lock mechanism
- Basic retention (keep last 3 backups)
- Minimal logging

### Hard mode (current)
- Full MySQL quiescing with proper lock maintenance
- LVM snapshot lifecycle management
- Complete retention policy (exactly 7 backups)
- Comprehensive logging
- Cron automation
- Verification script
- Error handling and cleanup

### Harder variants (future)
- Multiple databases with different retention policies
- Compression and encryption of backups
- Remote backup locations
- Backup verification with actual MySQL restore
- Incremental backups
- Backup rotation across multiple storage tiers

## Expected agent behavior

**Good agents will:**
1. Acquire MySQL lock using `FLUSH TABLES WITH READ LOCK` and maintain it in background process
2. Create LVM snapshot with proper size specification (`-L 1G`)
3. Mount snapshot to correct mount point
4. Use mounted snapshot path (not original) in rsync command
5. Unmount snapshot before removing it
6. Release MySQL lock after snapshot operations complete
7. Implement retention policy that sorts backups and keeps exactly 7 most recent
8. Create cron job with correct schedule (2:00 AM daily)
9. Log all operations with timestamps
10. Create verification script that checks backup integrity
11. Handle errors and clean up resources on failure

**Weak agents will:**
1. Forget MySQL locking entirely
2. Create snapshot without size (command fails)
3. Back up from original volume instead of snapshot
4. Not implement retention policy
5. Forget to unmount before removing snapshot
6. Not release MySQL lock (leaves database locked)
7. Create cron job with wrong syntax or schedule
8. Missing or incomplete logging
9. Not create verification script
10. Poor error handling (leaves system in bad state)
11. Wrong timestamp format in backup directory names

## Known issues and limitations

- LVM in Docker containers requires specific capabilities (SYS_ADMIN) which may need to be configured in Harbor/docker-compose
- MySQL lock mechanism uses background process with sleep - in production, a more robust mechanism might use a dedicated lock-holding script
- Verification script checks file structure but doesn't perform actual MySQL restore (would require more complex setup)
- Snapshot size (1GB) is fixed - in production, this might need to be calculated based on expected changes
- Retention policy uses simple file counting - in production, might want date-based retention

## Container requirements

This task requires containers with:
- `SYS_ADMIN` capability for LVM operations (loop devices, volume management)
- Sufficient storage for LVM backing file and snapshots
- MySQL service running and accessible

The Dockerfile sets up LVM using a loop device, which requires appropriate capabilities when running the container.

