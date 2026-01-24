#!/usr/bin/env python3
"""
Windows Artifact Timeline Correlation Tool

Ingests MFT records, EVTX logs, and Prefetch files to create a unified timeline.
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def parse_mft_records(mft_file: Path) -> List[Dict[str, Any]]:
    """Parse MFT records file and extract file creation events."""
    events = []
    
    # Bug: Not handling file not found properly, and timestamp parsing is wrong
    try:
        with open(mft_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Format: "C:\Windows\System32\notepad.exe|2024-01-15 14:30:25 EST"
                parts = line.split('|')
                if len(parts) != 2:
                    continue
                
                file_path = parts[0]
                timestamp_str = parts[1]
                
                # Bug: Not converting EST to UTC, just stripping timezone
                # Also not handling the format correctly
                try:
                    # Bug: Wrong format string - missing timezone handling
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S EST")
                    # Bug: Not converting to UTC, just using as-is
                    events.append({
                        'timestamp': dt,
                        'event_type': 'file_creation',
                        'source': 'MFT',
                        'details': file_path,
                        'raw_timestamp': timestamp_str
                    })
                except ValueError:
                    # Bug: Silently skipping invalid timestamps
                    pass
    except FileNotFoundError:
        # Bug: Should raise or handle properly
        pass
    
    return events


def parse_evtx_events(evtx_file: Path) -> List[Dict[str, Any]]:
    """Parse EVTX event log file and extract process/service events."""
    events = []
    
    try:
        with open(evtx_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Format: "EventID:4688|Time:2024-01-15T19:30:25.123Z|Process:C:\Windows\System32\cmd.exe|Signed:true"
                # Format: "EventID:7045|Time:2024-01-15T19:35:10.456Z|Service:WindowsUpdate|Action:start"
                # Format: "EventID:4657|Time:2024-01-15T19:40:00.789Z|Key:HKEY_LOCAL_MACHINE\...\Run|Value:malware.exe"
                
                if 'EventID:4688' in line:
                    # Process execution event
                    # Bug: Regex might not capture all cases
                    process_match = re.search(r'Process:([^|]+)', line)
                    time_match = re.search(r'Time:([^|]+)', line)
                    signed_match = re.search(r'Signed:([^|]+)', line)
                    
                    if process_match and time_match:
                        process_path = process_match.group(1)
                        time_str = time_match.group(1)
                        is_signed = signed_match.group(1).lower() == 'true' if signed_match else None
                        
                        try:
                            # Bug: Assuming time_str is already UTC, but might need parsing
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
                            pass
                
                elif 'EventID:7045' in line:
                    # Service start event
                    service_match = re.search(r'Service:([^|]+)', line)
                    time_match = re.search(r'Time:([^|]+)', line)
                    action_match = re.search(r'Action:([^|]+)', line)
                    
                    if not action_match or action_match.group(1).strip().lower() != 'start':
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
                            pass
                
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
                            pass
    except FileNotFoundError:
        pass
    
    return events


def parse_prefetch(prefetch_file: Path) -> List[Dict[str, Any]]:
    """Parse Prefetch file and extract process execution events."""
    events = []
    
    try:
        with open(prefetch_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Format: "C:\Windows\System32\powershell.exe|1705350625"
                parts = line.split('|')
                if len(parts) != 2:
                    continue
                
                process_path = parts[0]
                epoch_str = parts[1]
                
                try:
                    # Bug: Converting epoch to datetime but not setting timezone to UTC
                    epoch = int(epoch_str)
                    dt = datetime.fromtimestamp(epoch)
                    # Bug: Missing UTC timezone info
                    events.append({
                        'timestamp': dt,
                        'event_type': 'process_execution',
                        'source': 'Prefetch',
                        'details': process_path,
                        'raw_timestamp': epoch_str
                    })
                except (ValueError, OSError):
                    pass
    except FileNotFoundError:
        pass
    
    return events


def detect_anomalies(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect and flag anomalous events."""
    anomalous = []
    
    for event in events:
        anomaly_flag = False
        anomaly_reason = ""
        
        # Bug: Anomaly detection logic is incomplete
        # Check for unsigned binary executions
        if event.get('event_type') == 'process_execution':
            # Bug: Only checking EVTX events, missing Prefetch events
            if event.get('source') == 'EVTX' and event.get('is_signed') is False:
                anomaly_flag = True
                anomaly_reason = "Unsigned binary execution"
        
        # Check for registry Run key modifications
        if event.get('event_type') == 'registry_modification':
            details = event.get('details', '')
            # Bug: Case-sensitive check, might miss variations
            if 'Run' in details:
                anomaly_flag = True
                anomaly_reason = "Registry Run key modification"
        
        event['anomaly_flag'] = anomaly_flag
        event['anomaly_reason'] = anomaly_reason
        
        if anomaly_flag:
            anomalous.append(event)
    
    return anomalous


def normalize_timestamps(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize all timestamps to UTC ISO 8601 format."""
    # Bug: This function doesn't actually normalize - timestamps are already wrong
    # It should convert EST to UTC and ensure all are UTC
    normalized = []
    
    for event in events:
        dt = event['timestamp']
        # Bug: Not actually converting timezones, just formatting
        # Should convert EST to UTC (EST is UTC-5, EDT is UTC-4)
        if isinstance(dt, datetime):
            # Bug: Assuming naive datetime is UTC, but it's not
            if dt.tzinfo is None:
                # Treat as UTC (wrong if it's EST)
                event['timestamp_utc'] = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                event['timestamp_utc'] = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            event['timestamp_utc'] = str(dt)
        
        normalized.append(event)
    
    return normalized


def correlate_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Correlate all events into a single chronological timeline."""
    # Bug: Not actually sorting by timestamp
    # Should sort by timestamp_utc after normalization
    # Currently just returns events in order they were parsed
    return events


def write_csv_timeline(events: List[Dict[str, Any]], output_file: Path):
    """Write timeline to CSV file."""
    # Bug: Using wrong field names and not handling missing fields
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'event_type', 'source', 'details', 'anomaly_flag', 'anomaly_reason'])
        
        for event in events:
            # Bug: Using timestamp instead of timestamp_utc
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
        # Bug: Using wrong field structure
        summary.append({
            'timestamp': event.get('timestamp_utc', ''),
            'event_type': event.get('event_type', ''),
            'source': event.get('source', ''),
            'details': event.get('details', ''),
            'anomaly_type': event.get('anomaly_reason', ''),  # Bug: Should be anomaly_type
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
    
    # Bug: Normalization happens but doesn't actually fix timezones
    normalized_events = normalize_timestamps(all_events)
    
    # Bug: Correlation doesn't actually sort
    timeline = correlate_timeline(normalized_events)
    
    # Detect anomalies
    anomalous = detect_anomalies(timeline)
    
    # Write outputs
    write_csv_timeline(timeline, output_dir / 'timeline.csv')
    write_json_summary(anomalous, output_dir / 'suspicious_events.json')
    
    print(f"Processed {len(timeline)} events, flagged {len(anomalous)} suspicious events")


if __name__ == '__main__':
    main()
