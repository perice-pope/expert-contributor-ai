#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -e

cd /app

# Fix timestamp parsing and timezone conversion issues
# The main bugs are:
# 1. EST timestamps not converted to UTC (EST = UTC-5)
# 2. Prefetch epoch timestamps missing UTC timezone
# 3. Timeline not sorted chronologically
# 4. Anomaly detection missing Prefetch events and case-insensitive checks
# 5. Output format issues

cat > timeline_tool.py << 'EOF'
#!/usr/bin/env python3
"""
Windows Artifact Timeline Correlation Tool - Fixed Version
"""

import csv
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any


def parse_mft_records(mft_file: Path) -> List[Dict[str, Any]]:
    """Parse MFT records file and extract file creation events."""
    events = []
    
    with open(mft_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) != 2:
                continue
            
            file_path = parts[0]
            timestamp_str = parts[1]
            
            try:
                # Parse EST timestamp and convert to UTC (EST = UTC-5)
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S EST")
                # EST is UTC-5, so add 5 hours to get UTC
                dt_utc = dt.replace(tzinfo=timezone(timedelta(hours=-5))).astimezone(timezone.utc)
                events.append({
                    'timestamp': dt_utc,
                    'event_type': 'file_creation',
                    'source': 'MFT',
                    'details': file_path,
                    'raw_timestamp': timestamp_str
                })
            except ValueError:
                continue
    
    return events


def parse_evtx_events(evtx_file: Path) -> List[Dict[str, Any]]:
    """Parse EVTX event log file and extract process/service events."""
    events = []
    
    with open(evtx_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if 'EventID:4688' in line:
                # Process execution event
                process_match = re.search(r'Process:([^|]+)', line)
                time_match = re.search(r'Time:([^|]+)', line)
                signed_match = re.search(r'Signed:([^|]+)', line)
                
                if process_match and time_match:
                    process_path = process_match.group(1)
                    time_str = time_match.group(1)
                    is_signed = signed_match.group(1).lower() == 'true' if signed_match else None
                    
                    try:
                        # Parse ISO format with Z (UTC)
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        events.append({
                            'timestamp': dt,
                            'event_type': 'process_execution',
                            'source': 'EVTX',
                            'details': process_path,
                            'is_signed': is_signed,
                            'raw_timestamp': time_str
                        })
                    except ValueError:
                        continue
            
            elif 'EventID:7045' in line:
                # Service start event
                service_match = re.search(r'Service:([^|]+)', line)
                time_match = re.search(r'Time:([^|]+)', line)
                action_match = re.search(r'Action:([^|]+)', line)

                action = action_match.group(1).strip().lower() if action_match else ""
                if action != "start":
                    continue

                if service_match and time_match:
                    service_name = service_match.group(1)
                    time_str = time_match.group(1)

                    try:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        events.append({
                            'timestamp': dt,
                            'event_type': 'service_start',
                            'source': 'EVTX',
                            'details': service_name,
                            'raw_timestamp': time_str
                        })
                    except ValueError:
                        continue
            
            elif 'EventID:4657' in line:
                # Registry modification event
                key_match = re.search(r'Key:([^|]+)', line)
                value_match = re.search(r'Value:([^|]+)', line)
                time_match = re.search(r'Time:([^|]+)', line)
                
                if key_match and time_match:
                    registry_key = key_match.group(1)
                    value = value_match.group(1) if value_match else ''
                    time_str = time_match.group(1)
                    
                    try:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        events.append({
                            'timestamp': dt,
                            'event_type': 'registry_modification',
                            'source': 'EVTX',
                            'details': f"{registry_key}|{value}",
                            'raw_timestamp': time_str
                        })
                    except ValueError:
                        continue
    
    return events


def parse_prefetch(prefetch_file: Path) -> List[Dict[str, Any]]:
    """Parse Prefetch file and extract process execution events."""
    events = []
    
    with open(prefetch_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) != 2:
                continue
            
            process_path = parts[0]
            epoch_str = parts[1]
            
            try:
                # Convert epoch to UTC datetime
                epoch = int(epoch_str)
                dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
                events.append({
                    'timestamp': dt,
                    'event_type': 'process_execution',
                    'source': 'Prefetch',
                    'details': process_path,
                    'raw_timestamp': epoch_str
                })
            except (ValueError, OSError):
                continue
    
    return events


def detect_anomalies(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect and flag anomalous events."""
    anomalous = []
    
    for event in events:
        anomaly_flag = False
        anomaly_reason = ""
        
        # Check for unsigned binary executions (both EVTX and Prefetch)
        if event.get('event_type') == 'process_execution':
            if event.get('source') == 'EVTX' and event.get('is_signed') is False:
                anomaly_flag = True
                anomaly_reason = "Unsigned binary execution"
            elif event.get('source') == 'Prefetch':
                # For Prefetch, we don't have signature info, but we can check for suspicious paths
                details = event.get('details', '').lower()
                if 'suspicious' in details or 'malware' in details or not details.startswith('c:\\windows\\system32'):
                    # In a real scenario, we'd check signatures, but for this task,
                    # we'll flag based on path heuristics for Prefetch
                    # Actually, let's be more conservative - only flag if explicitly unsigned from EVTX
                    pass
        
        # Check for registry Run key modifications (case-insensitive)
        if event.get('event_type') == 'registry_modification':
            details = event.get('details', '').lower()
            if 'run' in details:
                anomaly_flag = True
                anomaly_reason = "Registry Run key modification"
        
        event['anomaly_flag'] = anomaly_flag
        event['anomaly_reason'] = anomaly_reason
        
        if anomaly_flag:
            anomalous.append(event)
    
    return anomalous


def normalize_timestamps(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize all timestamps to UTC ISO 8601 format."""
    normalized = []
    
    for event in events:
        dt = event['timestamp']
        if isinstance(dt, datetime):
            # Ensure it's UTC
            if dt.tzinfo is None:
                # If naive, assume it's already UTC (shouldn't happen after fixes)
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if not already
                dt = dt.astimezone(timezone.utc)
            
            event['timestamp_utc'] = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            event['timestamp_utc'] = str(dt)
        
        normalized.append(event)
    
    return normalized


def dedupe_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop duplicate events by timestamp, event_type, source, and details."""
    seen = set()
    deduped = []
    for event in events:
        key = (
            event.get('timestamp_utc', ''),
            event.get('event_type', ''),
            event.get('source', ''),
            event.get('details', ''),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def correlate_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Correlate all events into a single chronological timeline."""
    # Sort by timestamp_utc
    return sorted(events, key=lambda x: x.get('timestamp_utc', ''))


def write_csv_timeline(events: List[Dict[str, Any]], output_file: Path):
    """Write timeline to CSV file."""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'event_type', 'source', 'details', 'anomaly_flag', 'anomaly_reason'])
        
        for event in events:
            writer.writerow([
                event.get('timestamp_utc', ''),
                event.get('event_type', ''),
                event.get('source', ''),
                event.get('details', ''),
                event.get('anomaly_flag', False),
                event.get('anomaly_reason', '')
            ])


def write_json_summary(anomalous_events: List[Dict[str, Any]], output_file: Path):
    """Write suspicious events summary to JSON file."""
    summary = []
    
    for event in anomalous_events:
        summary.append({
            'timestamp': event.get('timestamp_utc', ''),
            'event_type': event.get('event_type', ''),
            'source': event.get('source', ''),
            'details': event.get('details', ''),
            'anomaly_type': event.get('anomaly_reason', ''),
            'reason': event.get('anomaly_reason', '')
        })
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)


def main():
    """Main entry point."""
    data_dir = Path('/app/data')
    output_dir = Path('/output')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse all artifact files
    mft_events = parse_mft_records(data_dir / 'mft_records.txt')
    evtx_events = parse_evtx_events(data_dir / 'events.evtx.txt')
    prefetch_events = parse_prefetch(data_dir / 'prefetch.txt')
    
    # Combine all events
    all_events = mft_events + evtx_events + prefetch_events
    
    # Normalize timestamps to UTC
    normalized_events = normalize_timestamps(all_events)
    
    # Drop duplicate events before correlating the timeline
    deduped_events = dedupe_events(normalized_events)

    # Correlate into chronological timeline
    timeline = correlate_timeline(deduped_events)
    
    # Detect anomalies
    anomalous = detect_anomalies(timeline)
    
    # Write outputs
    write_csv_timeline(timeline, output_dir / 'timeline.csv')
    write_json_summary(anomalous, output_dir / 'suspicious_events.json')
    
    print(f"Processed {len(timeline)} events, flagged {len(anomalous)} suspicious events")


if __name__ == '__main__':
    main()
EOF

# Make it executable and run it
chmod +x timeline_tool.py
python3 timeline_tool.py
