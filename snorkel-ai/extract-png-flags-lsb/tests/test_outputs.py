"""Tests for the PNG carving and LSB steganography extraction task."""
from pathlib import Path
import re
from PIL import Image


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
    
    # Expected flags (must be present)
    expected_flags = [
        "FLAG{hidden_in_plain_sight}",
        "FLAG{lsb_steganography_rocks}",
        "FLAG{memory_forensics_ftw}"
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


def test_png_offsets_correspond_to_memdump():
    """Verify that reported PNG offsets actually contain PNG headers in memdump.raw.
    
    This anti-cheating test ensures agents cannot pass by hardcoding flags with fake offsets.
    Each reported offset must correspond to a real PNG header in the memory dump.
    """
    flags_path = Path("/app/flags.txt")
    memdump_path = Path("/app/memdump.raw")
    
    # PNG header magic bytes: \x89PNG\r\n\x1a\n
    PNG_HEADER = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
    
    # Read flags file
    content = flags_path.read_text(encoding="utf-8")
    
    # Read memory dump
    with open(memdump_path, 'rb') as f:
        memdump_data = f.read()
    
    # Parse each flag line and verify offset
    for line in content.strip().split('\n'):
        if not line.strip() or ':' not in line:
            continue
        
        # Extract offset (format: 0x<hex>: <flag>)
        offset_part = line.split(':', 1)[0].strip()
        assert offset_part.startswith('0x'), (
            f"Offset does not start with '0x': {offset_part}"
        )
        
        # Convert hex offset to integer
        try:
            offset = int(offset_part[2:], 16)
        except ValueError:
            assert False, f"Invalid hexadecimal offset: {offset_part}"
        
        # Verify offset is within memdump bounds
        assert offset < len(memdump_data), (
            f"Reported offset 0x{offset:x} is beyond memdump size ({len(memdump_data)} bytes)"
        )
        
        # Verify PNG header exists at this offset
        if offset + len(PNG_HEADER) <= len(memdump_data):
            header_at_offset = memdump_data[offset:offset + len(PNG_HEADER)]
            assert header_at_offset == PNG_HEADER, (
                f"PNG header not found at reported offset 0x{offset:x}. "
                f"Expected {PNG_HEADER.hex()}, found {header_at_offset.hex()}"
            )
        else:
            assert False, (
                f"Reported offset 0x{offset:x} is too close to end of memdump "
                f"({len(memdump_data)} bytes) to contain PNG header"
            )


def test_flags_extractable_from_carved_images():
    """Verify that flags reported in flags.txt can be extracted via LSB from carved images.
    
    This anti-cheating test ensures agents actually perform LSB extraction from image pixel
    data rather than hardcoding known flags. The test verifies that each flag in flags.txt
    can be found in the LSB data of at least one carved image.
    
    Note: This test does NOT enforce a specific extraction algorithm, bit order, traversal
    pattern, or termination method. Any valid LSB extraction method that produces the
    reported flags is acceptable.
    """
    flags_path = Path("/app/flags.txt")
    images_dir = Path("/app/images")
    
    # Read all flags from flags.txt
    flags_content = flags_path.read_text(encoding="utf-8")
    reported_flags = set()
    for line in flags_content.strip().split('\n'):
        if ':' in line:
            flag_text = line.split(':', 1)[1].strip()
            reported_flags.add(flag_text)
    
    assert len(reported_flags) > 0, "No flags found in flags.txt"
    
    # Get all carved images
    png_files = sorted(images_dir.glob("image_*.png"))
    assert len(png_files) > 0, "No carved images found"
    
    # Extract LSB data from all images and collect all possible flag strings
    extracted_flags = set()
    
    for png_file in png_files:
        img = Image.open(png_file)
        img = img.convert('RGB')
        pixels = img.load()
        width, height = img.size
        
        # Extract LSBs from all pixels (method-agnostic: collect all bits)
        bits = []
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                bits.append(r & 1)
                bits.append(g & 1)
                bits.append(b & 1)
        
        # Try extracting strings from various bit positions and lengths
        # This is permissive - we're just checking existence, not exact method
        for start_bit in range(min(100, len(bits) - 8)):  # Try first 100 bit positions
            for byte_len in range(20, min(200, (len(bits) - start_bit) // 8)):  # Try various lengths
                # Extract bytes (LSB-first per pixel, but we try different starting points)
                flag_bytes = []
                for i in range(byte_len):
                    bit_idx = start_bit + (i * 8)
                    if bit_idx + 7 >= len(bits):
                        break
                    byte_val = sum(bits[bit_idx + j] << j for j in range(8))
                    flag_bytes.append(byte_val)
                    if byte_val == 0:  # Stop at null terminator if found
                        break
                
                # Try to decode as ASCII
                try:
                    candidate = bytes(flag_bytes).decode('ascii', errors='ignore').rstrip('\x00').strip()
                    # Check if it looks like a flag (starts with FLAG{)
                    if candidate.startswith('FLAG{') and len(candidate) > 10:
                        extracted_flags.add(candidate)
                except:
                    pass
    
    # Verify all reported flags can be found in extracted data
    missing_flags = reported_flags - extracted_flags
    assert len(missing_flags) == 0, (
        f"Flags reported in flags.txt could not be extracted from carved images via LSB: {missing_flags}. "
        f"This suggests flags may have been hardcoded rather than extracted from image pixel data."
    )
