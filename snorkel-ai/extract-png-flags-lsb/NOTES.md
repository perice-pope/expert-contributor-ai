# Maintainer Notes

## What this task is testing

Agents must perform a complete forensic image extraction and steganography analysis workflow:
1. Parse a raw memory dump to locate embedded PNG images by magic headers/footers
2. Carve out complete PNG files (header to footer)
3. Extract hidden ASCII text flags using LSB (Least Significant Bit) steganography
4. Document findings with proper offset formatting

The task requires understanding of:
- Binary file parsing and magic number detection
- PNG file format (header: `89 50 4E 47 0D 0A 1A 0A`, footer: `49 45 4E 44 AE 42 60 82`)
- LSB steganography extraction (reading least significant bits from RGB channels)
- Image processing with PIL/Pillow (handling different image modes, RGB conversion)
- Bit manipulation and ASCII decoding

## Intended failure modes

### 1. Incomplete PNG carving
- **Shallow fix**: Only finding the first PNG image, not continuing search after first match
- **Pattern**: Using `find()` once and breaking, not looping through entire dump
- **Why it fails**: Multiple PNGs are embedded; missing images means missing flags
- **Test catches**: `test_at_least_three_flags_extracted` fails if < 3 flags found

### 2. Incorrect footer handling
- **Shallow fix**: Assuming PNG ends at a fixed offset or not searching for footer
- **Pattern**: Extracting data between header and arbitrary offset, missing actual footer
- **Why it fails**: PNGs have variable sizes; wrong boundaries create invalid images
- **Test catches**: `test_carved_images_are_valid_pngs` fails if images are malformed

### 3. Wrong image mode handling
- **Shallow fix**: Not converting image to RGB mode before pixel access
- **Pattern**: Accessing pixels directly without `img.convert('RGB')`, assuming RGB mode
- **Why it fails**: PIL may open images in RGBA, P, or other modes; direct pixel access fails or returns wrong data
- **Test catches**: `test_carved_images_are_valid_pngs` may pass, but LSB extraction fails silently

### 4. Incorrect LSB extraction
- **Shallow fix**: Reading MSB instead of LSB, wrong channel order, or incorrect bit-to-byte conversion
- **Pattern**: Using `(pixel >> 7) & 1` instead of `pixel & 1`, or wrong bit ordering in byte assembly
- **Why it fails**: LSB steganography requires exact bit extraction; wrong bits produce garbage text
- **Test catches**: `test_all_expected_flags_present` fails if flags are incorrect

### 5. Bit-to-byte conversion errors
- **Shallow fix**: Wrong bit ordering when assembling bytes (LSB vs MSB first)
- **Pattern**: Using `bits[i] << (7-j)` instead of `bits[i+j] << j` for LSB-first encoding
- **Why it fails**: Flags are encoded LSB-first; wrong order produces incorrect ASCII
- **Test catches**: `test_all_expected_flags_present` fails, `test_flags_are_ascii_text` may fail

### 6. Null terminator handling
- **Shallow fix**: Not stopping at null byte, extracting beyond flag end
- **Pattern**: Continuing to extract bits after flag ends, including padding/noise
- **Why it fails**: Extracts garbage after flag, may cause decoding errors or wrong flags
- **Test catches**: `test_flags_are_ascii_text` may fail if non-printable chars included

### 7. Output format errors
- **Shallow fix**: Writing offsets in decimal or wrong format, missing `0x` prefix
- **Pattern**: Writing `1024: FLAG{...}` instead of `0x400: FLAG{...}`
- **Why it fails**: Tests expect hexadecimal format with `0x` prefix
- **Test catches**: `test_flags_file_format` and `test_flag_offsets_are_valid_hex` fail

### 8. Directory creation failures
- **Shallow fix**: Not creating `/app/images/` directory before writing files
- **Pattern**: Writing to non-existent directory, causing file write errors
- **Why it fails**: File operations fail if directory doesn't exist
- **Test catches**: `test_images_directory_exists` and `test_png_images_were_carved` fail

### 9. Silent error handling
- **Shallow fix**: Catching exceptions but not logging or handling them properly
- **Pattern**: `except: pass` or returning None without indication of what failed
- **Why it fails**: Agent can't diagnose why extraction failed, may miss flags
- **Test catches**: Indirectly - missing flags cause `test_all_expected_flags_present` to fail

## Why tests are designed this way

### Behavioral validation over implementation checking
- Tests verify the **outputs** (`/app/images/*.png`, `/app/flags.txt`) contain expected content
- Tests don't check if specific Python functions were used (allows multiple valid approaches)
- Tests verify image validity by actually opening them with PIL (not just file extension)

### Content matching with flexibility
- Tests check for **expected flag strings** (must contain specific flags)
- Allows any number of additional flags (flexible on extras, strict on required)
- Verifies format but not exact offset values (offsets may vary based on implementation)

### Edge case coverage
- Empty file checks prevent false positives from empty outputs
- PNG validation ensures carved images are actually valid (not just binary blobs)
- ASCII validation prevents extraction of binary garbage
- Format validation ensures proper offset notation for forensic documentation

### Comprehensive flag validation
- Tests verify all three expected flags are present (not just one)
- Tests verify flag format (ASCII printable, proper structure)
- Tests verify offset format (hexadecimal with `0x` prefix)
- Tests verify image-to-flag count consistency

## Determinism and reproducibility

### Fixed inputs
- Memory dump is pre-generated with embedded PNGs (deterministic content via seeded random)
- PNG images contain fixed flags: `FLAG{hidden_in_plain_sight}`, `FLAG{lsb_steganography_rocks}`, `FLAG{memory_forensics_ftw}`
- LSB encoding uses deterministic algorithm (R, G, B channel order, LSB-first bit encoding)

### No external dependencies
- All operations work offline (no network calls)
- Memory dump is pre-generated and included in Docker image
- No time-dependent behavior (no sleeps, no polling)

### Tool version pinning
- Python version pinned: `python:3.11-slim-bookworm`
- Pillow version pinned: `Pillow==10.0.0`
- Base image pinned: `debian:bookworm-slim`

### Idempotent operations
- PNG carving is idempotent (same dump produces same images)
- LSB extraction is deterministic (same image produces same flag)
- Flag output format is consistent

## Task difficulty knobs

### Easy mode (not used here)
- Single PNG in dump
- Simple LSB extraction (no mode conversion needed)
- Flags in obvious locations

### Medium mode (could be)
- Multiple PNGs but clearly separated
- Standard RGB images
- Simple LSB extraction

### Hard mode (current)
- Multiple PNGs embedded in binary dump with noise
- Requires proper PNG carving (header + footer search)
- Must handle image mode conversion (RGBA → RGB)
- Complete LSB extraction workflow (bit extraction → byte assembly → ASCII decode)
- Proper output formatting (hex offsets, flag documentation)

### Harder variants (future)
- Fragmented PNGs across memory regions
- PNGs with compression or corruption
- Multiple flags per image
- Flags encoded in different channels or bit positions
- Non-ASCII flags (binary data)

## Difficulty Redesign (2025-12-31)

### Problem
Task was rated TRIVIAL with 100% agent pass rate. Needed to increase difficulty without adding brittle tests.

### Solution Implemented
Added signal vs noise distinction: instructions now clarify that not all carved PNGs contain valid flags. Some images may contain noise or decoy data that should be filtered out.

**Changes made:**
1. **Instruction updates**: Added language about signal vs noise, decoy data, and filtering requirements
2. **Test updates**: Replaced `test_all_expected_flags_present` with `test_expected_flags_present_and_valid` that only checks inclusion (not exclusion) to avoid brittleness
3. **Updated test docstrings**: Clarified that more images than flags is expected (due to decoy images)

### Memory Dump Regeneration Required
⚠️ **CRITICAL**: The memory dump (`/app/memdump.raw`) must be regenerated to include 2-3 decoy PNGs:

**Decoy PNG specifications:**
- **Decoy 1**: Valid PNG with all-zero LSBs (no extractable text)
- **Decoy 2**: Valid PNG with random ASCII noise in LSBs (e.g., "NOISE_DATA_12345")
- **Decoy 3**: Valid PNG with near-miss flag format in LSBs:
  - Option A: `FL4G{decoy_not_real}` (digit instead of letter)
  - Option B: `FLAG[decoy_not_real]` (brackets instead of braces)
  - Option C: `FLAG{decoy_not_real` (missing closing brace)

**Total PNGs in dump**: 5-6 (3 real flags + 2-3 decoys)

**Expected difficulty impact**: Should reduce pass rate from 100% to ~50-70% by requiring agents to:
- Extract LSB data from all images
- Validate extracted strings against expected flags
- Filter out noise/decoy data

### Implementation Status
- ✅ Instruction updated with signal vs noise language
- ✅ Tests updated (inclusion-only check, no exclusion)
- ⚠️ Memory dump regeneration pending (must be done before task submission)

## Expected agent behavior

**Good agents will:**
1. Search entire memory dump for all PNG headers (loop, not single find)
2. Match each header with corresponding footer
3. Extract complete PNG data (header to footer)
4. Convert images to RGB mode before pixel access
5. Extract LSBs in correct order (R, G, B per pixel)
6. Assemble bits into bytes correctly (LSB-first)
7. Stop at null terminator
8. Format output with hex offsets (`0x<hex>: <flag>`)
9. Create output directories before writing

**Weak agents will:**
1. Only find first PNG (break after first match)
2. Extract incomplete PNGs (wrong footer or fixed size)
3. Access pixels without mode conversion (fails for RGBA)
4. Read wrong bits (MSB instead of LSB)
5. Wrong bit-to-byte conversion (MSB-first instead of LSB-first)
6. Not stop at null terminator (extract garbage)
7. Wrong output format (decimal offsets, missing `0x`)
8. Forget to create directories
9. Silently fail on errors (no debugging info)

## Known issues and limitations

- Memory dump size is relatively small (~27KB) for realistic forensics, but sufficient for testing
- PNGs are embedded cleanly (not fragmented) - realistic fragmentation would increase difficulty significantly
- Flags are ASCII-only - binary flag extraction would require different validation
- LSB encoding is straightforward (sequential R, G, B) - more complex encoding schemes possible

