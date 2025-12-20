"""Tests for the OpenPGP key recovery task."""
from pathlib import Path


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
