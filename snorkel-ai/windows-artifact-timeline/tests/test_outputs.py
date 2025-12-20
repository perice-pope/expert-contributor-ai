"""Tests for the Windows Artifact Timeline Correlation task."""
import csv
import json
from datetime import datetime
from pathlib import Path


def test_csv_timeline_exists():
    """Verify the timeline CSV file was created."""
    timeline_path = Path("/output/timeline.csv")
    assert timeline_path.exists(), "timeline.csv does not exist"


def test_csv_timeline_has_header():
    """Verify the CSV has the correct header row."""
    timeline_path = Path("/output/timeline.csv")
    
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        expected_header = ['timestamp', 'event_type', 'source', 'details', 'anomaly_flag', 'anomaly_reason']
        assert header == expected_header, f"Expected header {expected_header}, got {header}"


def test_csv_timeline_has_events():
    """Verify the CSV contains event rows."""
    timeline_path = Path("/output/timeline.csv")
    
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        rows = list(reader)
        
        assert len(rows) > 0, "CSV should contain at least one event row"


def test_timestamps_are_utc_iso_format():
    """Verify all timestamps are in UTC ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."""
    timeline_path = Path("/output/timeline.csv")
    
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 0:
                timestamp = row[0]
                # Check format: YYYY-MM-DDTHH:MM:SSZ
                assert timestamp.endswith('Z'), f"Timestamp {timestamp} should end with Z (UTC)"
                try:
                    # Try parsing the timestamp
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    assert dt.tzinfo is not None, f"Timestamp {timestamp} should have timezone info"
                except ValueError:
                    assert False, f"Timestamp {timestamp} is not in valid ISO 8601 format"


def test_timeline_is_sorted_chronologically():
    """Verify events are sorted chronologically by timestamp."""
    timeline_path = Path("/output/timeline.csv")
    
    timestamps = []
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 0:
                timestamp = row[0]
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamps.append(dt)
    
    # Check if sorted
    assert timestamps == sorted(timestamps), "Timeline events are not sorted chronologically"


def test_all_event_types_present():
    """Verify all expected event types are present in the timeline."""
    timeline_path = Path("/output/timeline.csv")
    
    event_types = set()
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 1:
                event_types.add(row[1])
    
    expected_types = {'file_creation', 'process_execution', 'service_start', 'registry_modification'}
    assert expected_types.issubset(event_types), f"Missing event types. Expected {expected_types}, got {event_types}"


def test_all_sources_present():
    """Verify all expected sources (MFT, EVTX, Prefetch) are present."""
    timeline_path = Path("/output/timeline.csv")
    
    sources = set()
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 2:
                sources.add(row[2])
    
    expected_sources = {'MFT', 'EVTX', 'Prefetch'}
    assert expected_sources.issubset(sources), f"Missing sources. Expected {expected_sources}, got {sources}"


def test_json_summary_exists():
    """Verify the suspicious events JSON file was created."""
    json_path = Path("/output/suspicious_events.json")
    assert json_path.exists(), "suspicious_events.json does not exist"


def test_json_summary_is_valid():
    """Verify the JSON file is valid JSON."""
    json_path = Path("/output/suspicious_events.json")
    
    with open(json_path, 'r') as f:
        try:
            data = json.load(f)
            assert isinstance(data, list), "JSON should contain an array"
        except json.JSONDecodeError as e:
            assert False, f"Invalid JSON: {e}"


def test_json_summary_has_required_fields():
    """Verify each suspicious event has required fields."""
    json_path = Path("/output/suspicious_events.json")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
        required_fields = {'timestamp', 'event_type', 'source', 'details', 'anomaly_type', 'reason'}
        
        for event in data:
            assert isinstance(event, dict), "Each event should be a dictionary"
            for field in required_fields:
                assert field in event, f"Event missing required field: {field}"


def test_unsigned_binary_detected():
    """Verify unsigned binary executions are flagged in the JSON summary."""
    json_path = Path("/output/suspicious_events.json")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
        # Look for unsigned binary execution events
        unsigned_found = False
        for event in data:
            if event.get('anomaly_type') == 'Unsigned binary execution':
                unsigned_found = True
                assert event.get('event_type') == 'process_execution', "Unsigned binary should be process_execution"
                break
        
        assert unsigned_found, "At least one unsigned binary execution should be flagged"


def test_registry_run_key_detected():
    """Verify registry Run key modifications are flagged."""
    json_path = Path("/output/suspicious_events.json")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
        # Look for registry Run key modifications
        run_key_found = False
        for event in data:
            if event.get('anomaly_type') == 'Registry Run key modification':
                run_key_found = True
                assert event.get('event_type') == 'registry_modification', "Run key should be registry_modification"
                # Check that details contain 'run' (case-insensitive)
                details_lower = event.get('details', '').lower()
                assert 'run' in details_lower, "Details should mention 'run'"
                break
        
        assert run_key_found, "At least one registry Run key modification should be flagged"


def test_csv_anomaly_flags_match_json():
    """Verify anomaly flags in CSV match the events in JSON summary."""
    timeline_path = Path("/output/timeline.csv")
    json_path = Path("/output/suspicious_events.json")
    
    # Collect timestamps of anomalous events from CSV
    csv_anomalous_timestamps = set()
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 4:
                anomaly_flag = row[4].lower()
                if anomaly_flag == 'true':
                    csv_anomalous_timestamps.add(row[0])  # timestamp
    
    # Collect timestamps from JSON
    with open(json_path, 'r') as f:
        json_data = json.load(f)
        json_timestamps = {event['timestamp'] for event in json_data}
    
    # All JSON timestamps should be in CSV anomalous set
    assert json_timestamps.issubset(csv_anomalous_timestamps), \
        "All events in JSON summary should have anomaly_flag=True in CSV"


def test_mft_events_in_timeline():
    """Verify MFT file creation events are present in the timeline."""
    timeline_path = Path("/output/timeline.csv")
    
    mft_events_found = False
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 2 and row[2] == 'MFT' and row[1] == 'file_creation':
                mft_events_found = True
                break
    
    assert mft_events_found, "MFT file creation events should be present in timeline"


def test_evtx_events_in_timeline():
    """Verify EVTX events (process execution, service start, registry) are present."""
    timeline_path = Path("/output/timeline.csv")
    
    evtx_process = False
    evtx_service = False
    evtx_registry = False
    
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 2 and row[2] == 'EVTX':
                if row[1] == 'process_execution':
                    evtx_process = True
                elif row[1] == 'service_start':
                    evtx_service = True
                elif row[1] == 'registry_modification':
                    evtx_registry = True
    
    assert evtx_process, "EVTX process execution events should be present"
    assert evtx_service, "EVTX service start events should be present"
    assert evtx_registry, "EVTX registry modification events should be present"


def test_prefetch_events_in_timeline():
    """Verify Prefetch process execution events are present."""
    timeline_path = Path("/output/timeline.csv")
    
    prefetch_found = False
    with open(timeline_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) > 2 and row[2] == 'Prefetch' and row[1] == 'process_execution':
                prefetch_found = True
                break
    
    assert prefetch_found, "Prefetch process execution events should be present in timeline"
