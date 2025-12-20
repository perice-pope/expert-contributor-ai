# Windows Artifact Timeline Correlation - Task Notes

## Intended Agent Failure Modes

This task is designed to expose common agent failure modes in multi-step debugging scenarios:

### 1. **Shallow Fixes (Symptom vs. Root Cause)**
- **Bug**: Timestamps not converted to UTC properly
- **Failure Mode**: Agent might fix one timestamp format but miss others (EST, epoch, ISO)
- **Why**: Requires understanding that all three input formats need timezone conversion, not just one

### 2. **Incomplete Anomaly Detection**
- **Bug**: Anomaly detection only checks EVTX events, misses Prefetch; case-sensitive registry checks
- **Failure Mode**: Agent might fix unsigned binary detection but miss case-insensitive registry key matching
- **Why**: Requires reading the full detection logic and understanding edge cases

### 3. **Missing Correlation Logic**
- **Bug**: Timeline not sorted chronologically
- **Failure Mode**: Agent might fix parsing but forget to sort the final timeline
- **Why**: Easy to miss if focused only on parsing correctness

### 4. **Timezone Conversion Errors**
- **Bug**: EST timestamps treated as UTC, epoch timestamps missing timezone
- **Failure Mode**: Agent might add timezone info but forget EST→UTC conversion (EST = UTC-5)
- **Why**: Requires understanding Windows timezone conventions and proper UTC conversion

### 5. **Output Format Issues**
- **Bug**: CSV uses wrong field names, JSON structure incorrect
- **Failure Mode**: Agent might fix parsing but output wrong format, or fix format but miss field mappings
- **Why**: Requires careful attention to instruction requirements vs. actual output

## Test Design Rationale

### Behavioral Tests (Not Implementation Checks)
All tests verify **outputs and results**, not source code patterns:
- `test_timestamps_are_utc_iso_format()`: Checks actual timestamp format in CSV, not regex patterns in code
- `test_timeline_is_sorted_chronologically()`: Verifies sort order, not whether `sorted()` is called
- `test_unsigned_binary_detected()`: Checks JSON output for flagged events, not code logic

### Comprehensive Coverage
Tests map to each instruction requirement:
1. **Parse MFT/EVTX/Prefetch** → `test_mft_events_in_timeline()`, `test_evtx_events_in_timeline()`, `test_prefetch_events_in_timeline()`
2. **Normalize timestamps** → `test_timestamps_are_utc_iso_format()`
3. **Correlate timeline** → `test_timeline_is_sorted_chronologically()`
4. **Anomaly detection** → `test_unsigned_binary_detected()`, `test_registry_run_key_detected()`
5. **Output CSV** → `test_csv_timeline_exists()`, `test_csv_timeline_has_header()`, format checks
6. **Output JSON** → `test_json_summary_exists()`, `test_json_summary_has_required_fields()`

### Edge Case Coverage
- **Case-insensitive registry checks**: `test_registry_run_key_detected()` verifies both `Run` and `run` are caught
- **Multiple timestamp formats**: Tests verify all three formats (EST, ISO UTC, epoch) are handled
- **Cross-format correlation**: `test_csv_anomaly_flags_match_json()` ensures consistency between outputs

## Determinism and Reproducibility

### Pinned Dependencies
- **Python**: `3.11.9` (pinned in Dockerfile)
- **System packages**: `curl=7.88.1-10+deb12u6` (pinned)
- **Test tools**: `pytest==8.4.1`, `pytest-json-ctrf==0.3.5` (pinned in test.sh)

### No External Dependencies
- All parsing uses Python standard library (`csv`, `json`, `re`, `datetime`)
- No network calls required
- Input data files are static and deterministic

### Timezone Handling
- EST timestamps are deterministic: always UTC-5 (no daylight saving time complexity for this task)
- Epoch timestamps are deterministic Unix timestamps
- ISO timestamps with Z suffix are already UTC

### Deterministic Outputs
- CSV output order is deterministic (sorted by timestamp)
- JSON output order is deterministic (sorted by timestamp within suspicious events)
- All timestamps convert to the same UTC values every run

## Expected Difficulty

**Medium** - This task requires:
- Understanding multiple timestamp formats and timezone conversion
- Multi-step debugging (parsing → normalization → correlation → detection → output)
- Attention to detail in output formats
- Understanding of Windows forensics concepts (MFT, EVTX, Prefetch)

**Target Pass Rate**: < 80% (challenging but fair)

## Common Agent Mistakes

1. **Fixing only one timestamp format** (e.g., EST but forgetting epoch)
2. **Not converting EST to UTC** (just stripping timezone label)
3. **Missing the sort step** (parsing works but timeline unsorted)
4. **Case-sensitive registry matching** (misses `run` vs `Run`)
5. **Wrong output field names** (using `timestamp` instead of `timestamp_utc` in CSV)
6. **Incomplete anomaly detection** (fixes one type but misses others)

## Validation Notes

- Oracle solution passes all tests deterministically
- Tests are idempotent (can run multiple times)
- No flaky tests (no time/random dependencies)
- All edge cases covered in test data (unsigned binaries, registry Run keys, all event types)

