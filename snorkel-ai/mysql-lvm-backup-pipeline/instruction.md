# Implement MySQL LVM Backup Pipeline

A production MySQL database is running on an ext4 filesystem within an LVM logical volume. You need to implement a consistent backup pipeline that creates point-in-time snapshots, backs up the data, and maintains retention policies. The existing backup script at `/app/backup_mysql.sh` is incomplete and contains bugs that prevent it from working correctly.

## Requirements

1. **Quiesce MySQL database**: Before creating a snapshot, flush all tables and lock the database to ensure consistency. Use `FLUSH TABLES WITH READ LOCK` and maintain the lock during the snapshot operation.

2. **Create LVM snapshot**: Create a snapshot of the logical volume containing the MySQL data directory. The volume group is `vg_mysql`, the logical volume is `lv_mysql_data`, and the snapshot should be named `mysql_snapshot` with a size of 1GB.

3. **Mount snapshot**: Mount the snapshot to `/mnt/mysql_snapshot` as an ext4 filesystem. Create the mount point if it doesn't exist.

4. **Backup data via rsync**: Use rsync to copy the MySQL data directory from the mounted snapshot to `/backups/mysql/backup_YYYYMMDD_HHMMSS` (timestamp format: `YYYYMMDD_HHMMSS`). Preserve permissions, ownership, and timestamps. Create the `/backups/mysql` directory if it doesn't exist.

5. **Unmount and remove snapshot**: After the backup completes, unmount the snapshot and remove the LVM snapshot logical volume.

6. **Release MySQL lock**: Release the MySQL table lock after the snapshot is removed.

7. **Implement retention policy**: Keep only the last 7 backups. Delete older backups automatically, maintaining exactly 7 most recent backups sorted by timestamp.

8. **Automate with cron**: Configure a cron job to run the backup script daily at 2:00 AM. The cron job should log output to `/var/log/mysql_backup.log`.

9. **Detailed logging**: The backup script must produce detailed logs including:
   - Start timestamp
   - Each operation step (quiesce, snapshot creation, mount, rsync, unmount, cleanup)
   - Success/failure status for each step
   - End timestamp
   - Error messages if any step fails

10. **Verify restoration**: Create a verification script at `/app/verify_restore.sh` that:
    - Mounts the most recent backup as a read-only filesystem
    - Verifies that a sample database can be recovered from the backup
    - Reports success or failure

## Constraints

- **Do not modify MySQL configuration files**. Work with the existing MySQL setup.
- **Do not change the logical volume structure**. Use the existing `vg_mysql` volume group and `lv_mysql_data` logical volume.
- **All operations must be deterministic**. No network calls, no random data generation.
- **The backup script must be idempotent**. Running it multiple times should not cause errors.
- **Use shell scripts only**. No Python or other languages unless absolutely necessary for MySQL operations.
- **Backup directory structure**: Each backup must be in its own timestamped subdirectory under `/backups/mysql/`.
- **Log file location**: All backup logs must be written to `/var/log/mysql_backup.log` with append mode.

## Files

- Starter backup script: `/app/backup_mysql.sh` (incomplete, contains bugs)
- MySQL data directory: `/var/lib/mysql` (on LVM logical volume `vg_mysql/lv_mysql_data`)
- Backup destination: `/backups/mysql/` (create if needed)
- Log file: `/var/log/mysql_backup.log`
- Verification script: `/app/verify_restore.sh` (create this)
- Cron configuration: `/etc/cron.d/mysql-backup` (create this)

## Outputs

- `/backups/mysql/backup_YYYYMMDD_HHMMSS/` (timestamped backup directories, exactly 7 most recent)
- `/var/log/mysql_backup.log` (detailed backup operation logs)
- `/app/backup_mysql.sh` (fixed and complete backup script)
- `/app/verify_restore.sh` (restoration verification script)
- `/etc/cron.d/mysql-backup` (cron job configuration)
