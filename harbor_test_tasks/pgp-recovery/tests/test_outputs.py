"""Tests for the OpenPGP key recovery task."""
from pathlib import Path
import subprocess


def test_memory_dump_not_modified():
    """Anti-cheating: Verify original memory dump was not modified."""
    dump_path = Path("/app/memory.dump")
    assert dump_path.exists(), "Memory dump file missing"
    
    # Check file hasn't been tampered with by checking it's still multi-region format
    content = dump_path.read_text(errors="ignore")
    assert "MEMDUMP" in content or "MEMORY_DUMP" in content, "Memory dump header missing - file may be modified"
    assert "gpg keyring buffer" in content, "Key buffer regions missing - file may be modified"
    assert content.count("[Region") >= 5, "Too few memory regions - dump appears modified"


def test_decrypted_file_exists():
    """Verify the decrypted output file was created."""
    decrypted_path = Path("/output/decrypted.txt")
    assert decrypted_path.exists(), f"Decrypted file {decrypted_path} does not exist"
    assert decrypted_path.is_file(), f"{decrypted_path} exists but is not a file"


def test_decrypted_file_not_empty():
    """Verify the decrypted file contains content."""
    decrypted_path = Path("/output/decrypted.txt")
    content = decrypted_path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "Decrypted file is empty"


def test_decrypted_content_matches_expected():
    """Verify the decrypted plaintext matches the expected secret message."""
    decrypted_path = Path("/output/decrypted.txt")
    decrypted_content = decrypted_path.read_text(encoding="utf-8").strip()
    
    # The expected message contains a specific marker and content
    assert "SECRET_MESSAGE_42" in decrypted_content, (
        f"Expected 'SECRET_MESSAGE_42' marker in decrypted content, got: {decrypted_content[:100]}"
    )
    assert "The quick brown fox jumps over the lazy dog" in decrypted_content, (
        "Expected test phrase not found in decrypted content"
    )
    assert "Recovery successful" in decrypted_content, (
        "Expected 'Recovery successful' marker not found in decrypted content"
    )


def test_decrypted_content_complete():
    """Verify the decrypted content is the complete expected message."""
    decrypted_path = Path("/output/decrypted.txt")
    decrypted_content = decrypted_path.read_text(encoding="utf-8").strip()
    
    # The full expected message
    expected_message = "SECRET_MESSAGE_42: The quick brown fox jumps over the lazy dog. Recovery successful!"
    
    # Allow for minor whitespace differences but content must match
    assert expected_message in decrypted_content or decrypted_content == expected_message, (
        f"Decrypted content does not match expected message.\n"
        f"Expected (contains): {expected_message}\n"
        f"Got: {decrypted_content}"
    )


def test_key_was_imported():
    """Verify that a private key was successfully imported into GPG."""
    gpg_home = Path("/root/.gnupg")
    assert gpg_home.exists(), "GPG home directory does not exist"
    
    # Check for keyring files (GPG 2.x uses pubring.kbx, older versions use secring.gpg or pubring.gpg)
    has_keyring = (
        (gpg_home / "pubring.kbx").exists() or
        (gpg_home / "secring.gpg").exists() or
        (gpg_home / "pubring.gpg").exists()
    )
    assert has_keyring, "No GPG keyring files found - key may not have been imported"
    
    # Anti-cheating: Verify a key was actually imported by checking GPG can list it
    result = subprocess.run(
        ["gpg", "--list-secret-keys", "--with-colons"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "GPG list-secret-keys failed"
    assert "fpr:" in result.stdout or "sec:" in result.stdout, \
        "No secret keys found in keyring - import may have failed"


def test_fragmented_key_recovered():
    """Anti-cheating: Verify key was recovered from fragmented regions, not simple extraction."""
    dump_path = Path("/app/memory.dump")
    dump_content = dump_path.read_text(errors="ignore")
    
    # The new dump has key split across 3 regions
    # Simple string extraction won't work - must assemble fragments
    assert dump_content.count("gpg keyring buffer") >= 3, \
        "Memory dump doesn't have fragmented structure - using wrong dump?"
    
    # Verify the key is split across multiple regions (not contiguous)
    # Check that memory regions exist between key fragments
    lines = dump_content.splitlines()
    key_buffer_indices = [i for i, line in enumerate(lines) if "gpg keyring buffer" in line]
    assert len(key_buffer_indices) >= 3, "Not enough key buffer regions"
    
    # Verify regions aren't contiguous (there's other memory in between)
    gap1 = key_buffer_indices[1] - key_buffer_indices[0]
    gap2 = key_buffer_indices[2] - key_buffer_indices[1]
    assert gap1 > 20, f"Fragments 1 and 2 too close together (gap={gap1})"
    assert gap2 > 20, f"Fragments 2 and 3 too close together (gap={gap2})"
    
    # Check for red herring fake keys
    assert dump_content.count("BEGIN PGP") >= 3, \
        "Memory dump should contain multiple key-like structures (including fake ones)"
