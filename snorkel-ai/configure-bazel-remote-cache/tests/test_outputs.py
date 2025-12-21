from pathlib import Path
import json


def test_cache_verification_file_exists():
    """Test that cache_verification.json file exists."""
    cache_file = Path("/app/cache_verification.json")
    assert cache_file.exists(), f"File {cache_file} does not exist"


def test_cache_verification_json_valid():
    """Test that cache_verification.json contains valid JSON with required fields."""
    cache_file = Path("/app/cache_verification.json")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)
    
    required_fields = [
        "cache_hit_percentage",
        "compile_actions_executed",
        "total_actions",
        "cache_hit_actions",
        "build_successful"
    ]
    
    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from cache_verification.json"
    
    # Verify types
    assert isinstance(data["cache_hit_percentage"], (int, float)), \
        "cache_hit_percentage must be a number"
    assert isinstance(data["compile_actions_executed"], int), \
        "compile_actions_executed must be an integer"
    assert isinstance(data["total_actions"], int), \
        "total_actions must be an integer"
    assert isinstance(data["cache_hit_actions"], int), \
        "cache_hit_actions must be an integer"
    assert isinstance(data["build_successful"], bool), \
        "build_successful must be a boolean"


def test_cache_hit_percentage_above_threshold():
    """Test that cache hit percentage is >95%."""
    cache_file = Path("/app/cache_verification.json")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)
    
    cache_hit_percentage = data["cache_hit_percentage"]
    assert cache_hit_percentage > 95.0, (
        f"Cache hit percentage {cache_hit_percentage}% is not above 95%. "
        f"Expected >95%, got {cache_hit_percentage}%"
    )


def test_no_compile_actions_executed():
    """Test that no compile actions were executed in the second build."""
    cache_file = Path("/app/cache_verification.json")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)
    
    compile_actions_executed = data["compile_actions_executed"]
    assert compile_actions_executed == 0, (
        f"Expected 0 compile actions executed, but got {compile_actions_executed}. "
        f"All compilation should have been served from cache."
    )


def test_build_successful():
    """Test that the second build completed successfully."""
    cache_file = Path("/app/cache_verification.json")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)
    
    assert data["build_successful"] is True, \
        "Second build must have completed successfully"


def test_bazelrc_cache_configuration():
    """Test that .bazelrc file exists and contains remote cache configuration."""
    bazelrc_file = Path("/app/.bazelrc")
    
    assert bazelrc_file.exists(), f"File {bazelrc_file} does not exist"
    
    with open(bazelrc_file, 'r') as f:
        content = f.read()
    
    # Verify remote cache configuration is present
    assert "remote_cache" in content, \
        ".bazelrc must contain remote_cache configuration"
    assert "localhost:8080" in content or "http://localhost:8080" in content, \
        ".bazelrc must configure remote cache to use localhost:8080"


def test_cache_statistics_consistent():
    """Test that cache statistics are internally consistent."""
    cache_file = Path("/app/cache_verification.json")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)
    
    total_actions = data["total_actions"]
    cache_hit_actions = data["cache_hit_actions"]
    cache_hit_percentage = data["cache_hit_percentage"]
    
    # Verify cache hit percentage matches calculated value
    if total_actions > 0:
        calculated_percentage = (cache_hit_actions / total_actions) * 100
        # Allow small floating point differences
        assert abs(cache_hit_percentage - calculated_percentage) < 0.01, (
            f"Cache hit percentage {cache_hit_percentage}% does not match "
            f"calculated value {calculated_percentage}% "
            f"(cache_hit_actions={cache_hit_actions}, total_actions={total_actions})"
        )
    
    # Verify cache hits don't exceed total actions
    assert cache_hit_actions <= total_actions, (
        f"cache_hit_actions ({cache_hit_actions}) cannot exceed "
        f"total_actions ({total_actions})"
    )
