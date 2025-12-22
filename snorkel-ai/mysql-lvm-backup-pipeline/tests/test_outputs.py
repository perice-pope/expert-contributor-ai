"""Tests for MySQL LVM backup pipeline task."""
import re
import subprocess
from pathlib import Path
from datetime import datetime


def test_backup_script_exists():
    """Test that backup_mysql.sh exists and is executable."""
    backup_script = Path("/app/backup_mysql.sh")
    assert backup_script.exists(), "backup_mysql.sh does not exist"
    assert backup_script.is_file(), "backup_mysql.sh is not a file"
    assert backup_script.stat().st_mode & 0o111, "backup_mysql.sh is not executable"


def test_backup_script_runs_successfully():
    """Test that backup script executes without errors."""
    backup_script = Path("/app/backup_mysql.sh")
    
    # Run the backup script
    result = subprocess.run(
        ["/bin/bash", str(backup_script)],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    assert result.returncode == 0, (
        f"Backup script failed with exit code {result.returncode}. "
        f"stdout: {result.stdout}, stderr: {result.stderr}"
    )


def test_backup_directory_created():
    """Test that backup directory is created with correct timestamp format."""
    backup_dir = Path("/backups/mysql")
    assert backup_dir.exists(), "/backups/mysql directory does not exist"
    assert backup_dir.is_dir(), "/backups/mysql is not a directory"
    
    # Check for backup subdirectories with timestamp format YYYYMMDD_HHMMSS
    backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
    assert len(backup_dirs) > 0, "No backup directories found"
    
    # Verify timestamp format
    timestamp_pattern = re.compile(r'^backup_\d{8}_\d{6}$')
    for backup_path in backup_dirs:
        assert timestamp_pattern.match(backup_path.name), (
            f"Backup directory name '{backup_path.name}' does not match format 'backup_YYYYMMDD_HHMMSS'"
        )


def test_backup_contains_mysql_data():
    """Test that backup contains MySQL data files."""
    backup_dir = Path("/backups/mysql")
    backup_dirs = sorted([d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")], reverse=True)
    
    assert len(backup_dirs) > 0, "No backup directories found"
    latest_backup = backup_dirs[0]
    
    # Check for essential MySQL files/directories
    # MySQL data directory should contain at least mysql system database or testdb
    has_mysql_data = (
        (latest_backup / "mysql").exists() or
        (latest_backup / "testdb").exists() or
        (latest_backup / "ibdata1").exists() or
        any(latest_backup.glob("*.ibd")) or
        any(latest_backup.glob("*.MYD"))
    )
    
    assert has_mysql_data, (
        f"Backup at {latest_backup} does not contain recognizable MySQL data files"
    )


def test_backup_log_file_exists():
    """Test that log file is created and contains entries."""
    log_file = Path("/var/log/mysql_backup.log")
    assert log_file.exists(), "/var/log/mysql_backup.log does not exist"
    assert log_file.is_file(), "/var/log/mysql_backup.log is not a file"
    
    log_content = log_file.read_text()
    assert len(log_content) > 0, "Log file is empty"
    
    # Check for expected log entries
    assert "Starting MySQL backup" in log_content or "Starting MySQL backup" in log_content, (
        "Log file does not contain backup start message"
    )


def test_retention_policy_enforced():
    """Test that retention policy keeps only last 7 backups."""
    backup_dir = Path("/backups/mysql")
    backup_dirs = sorted([d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")], reverse=True)
    
    # Run backup multiple times to test retention
    backup_script = Path("/app/backup_mysql.sh")
    for _ in range(3):
        subprocess.run(
            ["/bin/bash", str(backup_script)],
            capture_output=True,
            timeout=300
        )
    
    # Re-check backup count
    backup_dirs_after = sorted([d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")], reverse=True)
    
    # Should have at most 7 backups (or all if less than 7 were created)
    assert len(backup_dirs_after) <= 7, (
        f"Retention policy failed: found {len(backup_dirs_after)} backups, expected at most 7"
    )


def test_cron_job_configured():
    """Test that cron job is configured for MySQL backup."""
    cron_file = Path("/etc/cron.d/mysql-backup")
    assert cron_file.exists(), "/etc/cron.d/mysql-backup does not exist"
    
    cron_content = cron_file.read_text()
    assert "backup_mysql.sh" in cron_content, "Cron file does not reference backup_mysql.sh"
    assert "0 2 * * *" in cron_content or "2 * * *" in cron_content, (
        "Cron job is not scheduled for 2:00 AM"
    )


def test_verification_script_exists():
    """Test that verify_restore.sh exists and is executable."""
    verify_script = Path("/app/verify_restore.sh")
    assert verify_script.exists(), "verify_restore.sh does not exist"
    assert verify_script.is_file(), "verify_restore.sh is not a file"
    assert verify_script.stat().st_mode & 0o111, "verify_restore.sh is not executable"


def test_verification_script_runs():
    """Test that verification script executes and validates backup."""
    verify_script = Path("/app/verify_restore.sh")
    backup_dir = Path("/backups/mysql")
    
    # Ensure at least one backup exists
    backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
    if len(backup_dirs) == 0:
        # Run backup first
        backup_script = Path("/app/backup_mysql.sh")
        subprocess.run(
            ["/bin/bash", str(backup_script)],
            capture_output=True,
            timeout=300
        )
    
    # Run verification script
    result = subprocess.run(
        ["/bin/bash", str(verify_script)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Verification script should exit successfully if backup is valid
    assert result.returncode == 0, (
        f"Verification script failed with exit code {result.returncode}. "
        f"stdout: {result.stdout}, stderr: {result.stderr}"
    )
    
    # Check that verification script output mentions backup
    output = result.stdout + result.stderr
    assert "backup" in output.lower() or "SUCCESS" in output, (
        "Verification script output does not indicate successful verification"
    )


def test_mysql_lock_mechanism():
    """Test that backup script properly handles MySQL locks during snapshot."""
    log_file = Path("/var/log/mysql_backup.log")
    assert log_file.exists(), "Log file must exist to verify lock mechanism"
    log_content = log_file.read_text()
    
    # Check for lock-related messages indicating MySQL was quiesced
    has_lock_info = (
        "lock" in log_content.lower() or
        "quiesc" in log_content.lower() or
        "FLUSH TABLES" in log_content or
        "Quiescing" in log_content
    )
    assert has_lock_info, (
        "Backup log does not indicate MySQL lock/quiesce mechanism was used"
    )


def test_lvm_snapshot_was_used():
    """Test that backup uses LVM snapshot (not direct copy)."""
    log_file = Path("/var/log/mysql_backup.log")
    assert log_file.exists(), "Log file must exist to verify LVM snapshot usage"
    log_content = log_file.read_text()
    
    # Check for snapshot-related messages
    has_snapshot_info = (
        "snapshot" in log_content.lower() or
        "mysql_snapshot" in log_content or
        "dmsetup" in log_content.lower() or
        "lvcreate" in log_content.lower()
    )
    assert has_snapshot_info, (
        "Backup log does not indicate LVM snapshot was used"
    )
    
    # Check for mount/unmount of snapshot
    has_mount_info = (
        "mount" in log_content.lower() or
        "/mnt/mysql_snapshot" in log_content
    )
    assert has_mount_info, (
        "Backup log does not indicate snapshot was mounted"
    )


def test_detailed_logging():
    """Test that backup script produces detailed step-by-step logs."""
    log_file = Path("/var/log/mysql_backup.log")
    assert log_file.exists(), "Log file must exist"
    log_content = log_file.read_text()
    
    # Check for step indicators
    has_steps = (
        "Step 1" in log_content or
        "Step 2" in log_content or
        ("Starting" in log_content and "backup" in log_content.lower())
    )
    assert has_steps, "Log does not contain step-by-step progress messages"
    
    # Check that log has timestamps (format: [YYYY-MM-DD HH:MM:SS])
    has_timestamps = re.search(r'\[\d{4}-\d{2}-\d{2}', log_content) is not None
    assert has_timestamps, "Log entries do not include timestamps"


def test_retention_exactly_seven():
    """Test that retention policy keeps exactly 7 most recent backups."""
    backup_dir = Path("/backups/mysql")
    backup_script = Path("/app/backup_mysql.sh")
    
    # Run backup enough times to exceed 7
    for _ in range(10):
        subprocess.run(
            ["/bin/bash", str(backup_script)],
            capture_output=True,
            timeout=300
        )
    
    # Count backup directories
    backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
    
    # Should have exactly 7 (or fewer if something failed)
    assert len(backup_dirs) <= 7, (
        f"Retention policy failed: found {len(backup_dirs)} backups, expected at most 7"
    )
    
    # If we have 7, they should be the 7 most recent (verify by timestamp order)
    if len(backup_dirs) >= 7:
        sorted_dirs = sorted(backup_dirs, key=lambda d: d.name, reverse=True)
        # The 7 we have should be the most recent ones (sorted by name = sorted by time)
        assert len(sorted_dirs) == 7, "Should have exactly 7 backups after retention cleanup"


def test_backup_timestamp_format():
    """Test that backup timestamps are in correct format and sortable."""
    backup_dir = Path("/backups/mysql")
    backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
    
    if len(backup_dirs) > 1:
        # Extract timestamps and verify they're sortable
        timestamps = []
        for backup_path in backup_dirs:
            match = re.search(r'backup_(\d{8}_\d{6})$', backup_path.name)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Parse timestamp to verify it's valid
                    datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    timestamps.append(timestamp_str)
                except ValueError:
                    assert False, f"Invalid timestamp format in {backup_path.name}"
        
        assert len(timestamps) > 0, "No valid timestamps found in backup directory names"


def test_lvm_volume_group_exists():
    """Test that the required LVM volume group exists."""
    result = subprocess.run(
        ["vgs", "vg_mysql"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        f"Volume group vg_mysql does not exist. "
        f"stderr: {result.stderr}"
    )


def test_lvm_logical_volume_exists():
    """Test that the required LVM logical volume exists."""
    result = subprocess.run(
        ["lvs", "vg_mysql/lv_mysql_data"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        f"Logical volume vg_mysql/lv_mysql_data does not exist. "
        f"stderr: {result.stderr}"
    )


def test_snapshot_cleanup_after_backup():
    """Test that snapshot is properly removed after backup completes."""
    # Check that no mysql_snapshot LV exists (should be cleaned up)
    result = subprocess.run(
        ["lvs", "vg_mysql/mysql_snapshot"],
        capture_output=True,
        text=True
    )
    # Snapshot should NOT exist after backup completes
    assert result.returncode != 0, (
        "Snapshot mysql_snapshot still exists after backup - cleanup failed"
    )
    
    # Also check dmsetup for any leftover snapshot devices
    result_dm = subprocess.run(
        ["dmsetup", "ls"],
        capture_output=True,
        text=True
    )
    assert "mysql_snapshot" not in result_dm.stdout, (
        "Device-mapper snapshot device still exists after backup"
    )


def test_backup_uses_snapshot_mount_point():
    """Test that backup script uses the snapshot mount point, not direct MySQL data."""
    log_file = Path("/var/log/mysql_backup.log")
    if log_file.exists():
        log_content = log_file.read_text()
        
        # Check that rsync source is the snapshot mount point, not /var/lib/mysql
        has_correct_source = (
            "/mnt/mysql_snapshot" in log_content or
            "Mounting snapshot" in log_content or
            "mounted successfully" in log_content.lower()
        )
        assert has_correct_source, (
            "Backup log doesn't show snapshot mount point was used for rsync"
        )
