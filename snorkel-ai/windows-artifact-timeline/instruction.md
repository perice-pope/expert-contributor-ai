# Windows Artifact Timeline Correlation

You've been given a set of Windows forensic artifacts from an incident investigation: NTFS MFT records, EVTX event logs, and Prefetch files. Your task is to build a Python tool that ingests these artifacts, extracts file creation events, process executions, and service starts, normalizes all timestamps to UTC, correlates them into a unified chronological timeline, and flags suspicious activities.

## Requirements

1. **Parse MFT Records**: Extract file creation timestamps from the MFT records file (`/app/data/mft_records.txt`). Each line contains a file path and a timestamp in local Windows time format.
2. **Parse EVTX Events**: Extract process execution and service start events from the EVTX log file (`/app/data/events.evtx.txt`). Timestamps are in Windows event log format.
3. **Parse Prefetch Files**: Extract process execution timestamps from the Prefetch artifacts file (`/app/data/prefetch.txt`). Timestamps are in Unix epoch format.
4. **Normalize Timestamps**: Convert all timestamps to UTC and ensure consistent formatting (ISO 8601: `YYYY-MM-DDTHH:MM:SSZ`).
5. **Correlate Events**: Merge all events into a single chronological timeline sorted by timestamp.
6. **Anomaly Detection**: Flag and annotate the following suspicious events:
   - Unsigned binary executions (binaries without valid digital signatures)
   - Registry Run key modifications (events indicating changes to autorun registry keys)
7. **Output CSV Timeline**: Write the complete timeline to `/output/timeline.csv` with columns: `timestamp`, `event_type`, `source`, `details`, `anomaly_flag`, `anomaly_reason`.
8. **Output JSON Summary**: Write a summary of suspicious events to `/output/suspicious_events.json` containing an array of objects with fields: `timestamp`, `event_type`, `source`, `details`, `anomaly_type`, `reason`.

## Constraints

- **No external network calls**. All processing must be done offline.
- **Do not modify the input data files**. Read them as-is.
- **Handle timezone conversion correctly**. Windows local time must be converted to UTC (assume EST/EDT timezone for Windows timestamps).
- **All timestamps must be in UTC** in the output, regardless of source format.
- **The CSV must have a header row** and use comma delimiters.
- **The JSON must be valid JSON** with proper escaping.

## Files

- Starter project: `/app`
- Main tool script: `/app/timeline_tool.py`
- Input data files:
  - `/app/data/mft_records.txt` (MFT file creation records)
  - `/app/data/events.evtx.txt` (EVTX event log entries)
  - `/app/data/prefetch.txt` (Prefetch execution records)
- Output directory: `/output/`
- Output files:
  - `/output/timeline.csv` (complete chronological timeline)
  - `/output/suspicious_events.json` (summary of flagged events)

## Outputs

- `/output/timeline.csv`: CSV file with columns `timestamp`, `event_type`, `source`, `details`, `anomaly_flag`, `anomaly_reason`. All timestamps in UTC ISO 8601 format. When `anomaly_flag` is `true`, the `anomaly_reason` column must contain a descriptive text explanation of why the event is flagged as anomalous.
- `/output/suspicious_events.json`: JSON file with array of suspicious event objects, each containing `timestamp`, `event_type`, `source`, `details`, `anomaly_type`, `reason`.
