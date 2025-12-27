"""Tests for the PNG carving and LSB steganography extraction task.

These tests verify:
1. PNG images were correctly carved from the memory dump
2. Images are valid PNG files
3. Flags were extracted using LSB steganography
4. Output format is correct (hex offsets)
5. Anti-cheating: offsets correspond to actual PNG positions in dump
6. Anti-cheating: images match data at dump offsets
"""
from pathlib import Path
import re
import hashlib
from PIL import Image

# PNG signatures for validation
PNG_HEADER = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
PNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'


def test_images_directory_exists():
    """Verify the images output directory was created."""
    images_dir = Path("/app/images")
    assert images_dir.exists(), f"Images directory {images_dir} does not exist"
    assert images_dir.is_dir(), f"{images_dir} exists but is not a directory"


def test_png_images_were_carved():
    """Verify that at least one PNG image was carved from the memory dump."""
    images_dir = Path("/app/images")
    png_files = list(images_dir.glob("image_*.png"))
    assert len(png_files) > 0, "No PNG images were carved from the memory dump"


def test_carved_images_are_valid_pngs():
    """Verify that all carved images are valid PNG files."""
    images_dir = Path("/app/images")
    png_files = list(images_dir.glob("image_*.png"))
    
    for png_file in png_files:
        try:
            img = Image.open(png_file)
            img.verify()  # Verify it's a valid image
            assert img.format == 'PNG', f"{png_file} is not a valid PNG image"
        except Exception as e:
            assert False, f"{png_file} is not a valid PNG image: {e}"


def test_flags_file_exists():
    """Verify the flags output file was created."""
    flags_path = Path("/app/flags.txt")
    assert flags_path.exists(), f"Flags file {flags_path} does not exist"
    assert flags_path.is_file(), f"{flags_path} exists but is not a file"


def test_flags_file_not_empty():
    """Verify the flags file contains content."""
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "Flags file is empty"


def test_flags_file_format():
    """Verify flags file has correct format: 0x<hex>: <flag_text>."""
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    
    assert len(lines) > 0, "Flags file has no valid lines"
    
    # Format: 0x<hex>: <flag>
    pattern = re.compile(r'^0x[0-9a-fA-F]+:\s+.+$')
    for line in lines:
        assert pattern.match(line), (
            f"Flag line does not match expected format '0x<hex>: <flag>': {line}"
        )


def test_all_expected_flags_present():
    """Verify all expected flags are present in the output."""
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    
    # Expected flags (must be present) - XOR-encoded LSB extraction
    expected_flags = [
        "FLAG{xor_reveals_the_truth}",
        "FLAG{offset_is_the_key}",
        "FLAG{forensics_master}"
    ]
    
    found_flags = []
    for line in content.strip().split('\n'):
        if ':' in line:
            flag_text = line.split(':', 1)[1].strip()
            found_flags.append(flag_text)
    
    for expected_flag in expected_flags:
        assert expected_flag in found_flags, (
            f"Expected flag '{expected_flag}' not found in flags file. "
            f"Found flags: {found_flags}"
        )


def test_flag_offsets_are_valid_hex():
    """Verify flag offsets are valid hexadecimal numbers."""
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    
    for line in content.strip().split('\n'):
        if not line.strip():
            continue
        # Extract offset part (before the colon)
        if ':' in line:
            offset_part = line.split(':', 1)[0].strip()
            assert offset_part.startswith('0x'), (
                f"Offset does not start with '0x': {offset_part}"
            )
            hex_value = offset_part[2:]
            try:
                int(hex_value, 16)  # Validate it's valid hex
            except ValueError:
                assert False, f"Invalid hexadecimal offset: {offset_part}"


def test_at_least_three_flags_extracted():
    """Verify at least three flags were extracted (one per PNG image)."""
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.strip().split('\n') if line.strip() and ':' in line]
    
    assert len(lines) >= 3, (
        f"Expected at least 3 flags, but found {len(lines)}. "
        f"Content: {content[:200]}"
    )


def test_flags_are_ascii_text():
    """Verify extracted flags contain only ASCII printable characters."""
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    
    for line in content.strip().split('\n'):
        if ':' in line:
            flag_text = line.split(':', 1)[1].strip()
            # Check all characters are printable ASCII
            assert all(32 <= ord(c) <= 126 for c in flag_text), (
                f"Flag contains non-ASCII or non-printable characters: {flag_text[:50]}"
            )


def test_images_match_expected_count():
    """Verify the number of carved images matches the number of flags."""
    images_dir = Path("/app/images")
    png_files = list(images_dir.glob("image_*.png"))
    
    flags_path = Path("/app/flags.txt")
    content = flags_path.read_text(encoding="utf-8")
    flag_count = len([line for line in content.strip().split('\n') 
                     if line.strip() and ':' in line])
    
    # Should have at least as many images as flags (may have more if some failed to extract)
    assert len(png_files) >= flag_count, (
        f"Number of carved images ({len(png_files)}) is less than number of flags ({flag_count})"
    )


def test_memory_dump_not_modified():
    """Verify the original memory dump was not modified."""
    memdump_path = Path("/app/memdump.raw")
    assert memdump_path.exists(), "Memory dump file is missing"
    
    # Read the dump and verify it contains expected PNG structures
    data = memdump_path.read_bytes()
    
    # Must have at least 3 valid PNG headers in the dump
    png_count = 0
    offset = 0
    while True:
        pos = data.find(PNG_HEADER, offset)
        if pos == -1:
            break
        # Check if there's a corresponding footer
        footer_pos = data.find(PNG_FOOTER, pos)
        if footer_pos > pos:
            png_count += 1
        offset = pos + 1
    
    assert png_count >= 3, (
        f"Memory dump should contain at least 3 valid PNG structures, found {png_count}. "
        f"Dump may have been modified."
    )


def test_offsets_correspond_to_png_positions():
    """Anti-cheating: verify reported offsets point to actual PNG headers in dump."""
    flags_path = Path("/app/flags.txt")
    memdump_path = Path("/app/memdump.raw")
    
    content = flags_path.read_text(encoding="utf-8")
    dump_data = memdump_path.read_bytes()
    
    for line in content.strip().split('\n'):
        if not line.strip() or ':' not in line:
            continue
        
        # Extract offset
        offset_str = line.split(':', 1)[0].strip()
        if offset_str.startswith('0x'):
            offset = int(offset_str[2:], 16)
            
            # Verify PNG header exists at this offset
            if offset < len(dump_data):
                header_at_offset = dump_data[offset:offset + len(PNG_HEADER)]
                assert header_at_offset == PNG_HEADER, (
                    f"Offset {offset_str} does not point to a valid PNG header in the memory dump. "
                    f"Found bytes: {header_at_offset.hex()[:32]}..., expected: {PNG_HEADER.hex()}. "
                    f"Offsets must correspond to actual PNG positions in memdump.raw."
                )
            else:
                assert False, (
                    f"Offset {offset_str} ({offset}) is beyond memory dump size ({len(dump_data)})"
                )


def test_carved_images_match_dump_data():
    """Anti-cheating: verify carved images match byte-for-byte with dump data at offsets."""
    flags_path = Path("/app/flags.txt")
    images_dir = Path("/app/images")
    memdump_path = Path("/app/memdump.raw")
    
    content = flags_path.read_text(encoding="utf-8")
    dump_data = memdump_path.read_bytes()
    
    # Build offset -> flag mapping
    offset_map = {}
    for line in content.strip().split('\n'):
        if not line.strip() or ':' not in line:
            continue
        offset_str, flag = line.split(':', 1)
        offset_str = offset_str.strip()
        if offset_str.startswith('0x'):
            offset = int(offset_str[2:], 16)
            offset_map[offset] = flag.strip()
    
    # For each carved image, verify it matches dump data
    png_files = sorted(images_dir.glob("image_*.png"))
    
    for png_file in png_files:
        carved_data = png_file.read_bytes()
        carved_hash = hashlib.md5(carved_data).hexdigest()
        
        # Find this image in the dump
        found_match = False
        offset = 0
        while True:
            pos = dump_data.find(carved_data[:min(100, len(carved_data))], offset)
            if pos == -1:
                break
            
            # Check if full image matches
            dump_slice = dump_data[pos:pos + len(carved_data)]
            if dump_slice == carved_data:
                found_match = True
                break
            offset = pos + 1
        
        assert found_match, (
            f"Carved image {png_file.name} (hash: {carved_hash[:16]}) does not match any "
            f"data in the memory dump. Images must be extracted from memdump.raw, not generated."
        )
