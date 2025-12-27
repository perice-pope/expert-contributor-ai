# Maintainer Notes

## What this task is testing

Agents must perform a complete forensic image extraction and steganography analysis workflow:
1. Parse a raw memory dump to locate embedded PNG images by magic headers/footers
2. Carve out complete PNG files (filter out invalid/corrupted ones)
3. Extract hidden ASCII text flags using LSB (Least Significant Bit) steganography
4. **Decode XOR-encoded data** using a key derived from the image's offset
5. Document findings with proper offset formatting

The task requires understanding of:
- Binary file parsing and magic number detection
- PNG file format (header: `89 50 4E 47 0D 0A 1A 0A`, footer: `49 45 4E 44 AE 42 60 82`)
- LSB steganography extraction (reading least significant bits from RGB channels)
- **XOR encoding recognition and decoding**
- **Pattern recognition**: realizing LSB data is encoded, not plaintext
- Image processing with PIL/Pillow (handling different image modes, RGB conversion)
- Bit manipulation and ASCII decoding

## Difficulty Changes (REVISION-006 v2 - XOR Encoding)

**Original difficulty**: TRIVIAL (100% agent success rate)
**After fake PNGs**: Still 100% (Claude 3/3 passes)
**Target difficulty**: MEDIUM (30-70% success rate)

### New approach: XOR-encoded LSB with offset-derived key

The key insight: Simple fake PNGs aren't enough because agents successfully filter them with Pillow validation. We need to add a **reasoning step** that isn't in the standard playbook.

**How it works:**
1. Flags are encoded in LSB as before (R,G,B order, LSB-first)
2. Each flag byte is XOR'd with a key before embedding
3. The key is derived from the PNG's offset in the memory dump: `key = offset & 0xFF`
4. A hint exists in the dump: `[DEBUG] Encryption key derivation: key = offset & 0xFF`

**Why this is harder:**
- Raw LSB extraction produces garbage (XOR'd data), not readable flags
- Agent must:
  1. Recognize the LSB data is encoded/garbled
  2. Notice the hint about key derivation (or brute force)
  3. Implement XOR decoding with correct key
  4. Understand that null terminator is also XOR'd

**This tests:**
- Pattern recognition (data looks encoded, not corrupt)
- Multi-step reasoning (carve → extract → decode)
- Reading and interpreting embedded hints
- Implementation of decoding logic

### Memory dump structure (v2):
- ~12.5KB total size
- 3 real PNGs with XOR-encoded LSB flags:
  - `0x400`: key=0x00, FLAG{xor_reveals_the_truth}
  - `0x1337`: key=0x37, FLAG{offset_is_the_key}
  - `0x2a5c`: key=0x5c, FLAG{forensics_master}
- 3 fake/corrupted PNG structures
- Hint text: `[DEBUG] Encryption key derivation: key = offset & 0xFF`
- Decoy flag: `FLAG{this_is_a_decoy_not_real}` in plaintext noise
- Noise sections, partial headers

## Intended failure modes

### 1. Missing XOR decoding entirely
- **Problem**: Agent extracts raw LSB data without XOR decoding
- **Result**: All flags are garbled (e.g., `FLAG{` becomes `SXJT^` with key=0x37)
- **Test catches**: `test_all_expected_flags_present` fails
- **This is the primary difficulty lever**

### 2. Wrong XOR key derivation
- **Problem**: Agent uses wrong key (constant, wrong byte of offset)
- **Result**: Flags partially correct or still garbled
- **Test catches**: `test_all_expected_flags_present` fails

### 3. Not finding the hint
- **Problem**: Agent doesn't read the dump for clues
- **Result**: Must brute-force XOR key (256 attempts per image)
- **Still solvable**: Brute force is viable but more complex

### 4. Stopping at "encoded" data
- **Problem**: Agent sees garbage LSB and assumes image has no flag
- **Result**: Missing all 3 flags
- **Test catches**: `test_at_least_three_flags_extracted` fails

### 5. Not handling invalid PNGs
- **Problem**: Code extracts ALL PNG structures without validation
- **Result**: Attempts extraction on corrupted PNGs
- **Test catches**: Via overall flag count/content

### 6. Wrong LSB extraction
- **Problem**: Reading MSB instead of LSB, wrong channel order
- **Result**: Even correct XOR key won't produce valid flags
- **Test catches**: `test_all_expected_flags_present` fails

### 7. Fabricating output
- **Problem**: Agent writes expected flags without parsing
- **Result**: Offsets don't match actual PNG positions
- **Test catches**: `test_offsets_correspond_to_png_positions`

### 8. XOR'd null terminator handling
- **Problem**: Looking for 0x00 terminator instead of XOR'd terminator
- **Result**: Flag truncated or extended with garbage
- **Test catches**: Via flag content matching

## Why tests are designed this way

### Anti-cheating measures
- Verify offsets point to actual PNG headers in memory dump
- Verify carved images match byte-for-byte with dump data
- Cannot pass by fabricating flags without reading inputs

### Behavioral validation
- Tests verify outputs contain expected content
- Flexible on implementation details (any valid approach works)
- PNG validation uses Pillow (same as agents would use)

### Format strictness
- Hex offsets with `0x` prefix required
- All 3 known flags must be present
- ASCII printable characters only

## Determinism and reproducibility

### Fixed inputs
- Memory dump generated with seed=42 (deterministic)
- Flags (XOR-encoded):
  - `FLAG{xor_reveals_the_truth}` at 0x400 (key=0x00)
  - `FLAG{offset_is_the_key}` at 0x1337 (key=0x37)
  - `FLAG{forensics_master}` at 0x2a5c (key=0x5c)
- LSB encoding: R, G, B channel order, LSB-first bit encoding
- XOR key: low byte of offset

### No external dependencies
- All operations work offline
- Memory dump pre-generated and included
- No time-dependent behavior

### Tool version pinning
- Python: `python:3.11-slim-bookworm`
- Pillow: `10.0.0` (installed in Dockerfile)
- pytest: `8.4.1` (installed in test.sh)

## Task difficulty knobs

### Current (MEDIUM-HARD)
- XOR encoding with offset-derived key
- Hint present in dump (can be found by reading dump)
- Minimal starter script (just skeleton)
- Must implement carving + LSB + XOR decoding

### To make EASIER
- Make hint more prominent or in instructions
- Use constant XOR key (same for all images)
- Provide more guidance about encoding

### To make HARDER
- Remove hint from dump entirely
- Use different encoding per image (XOR, ROT13, base64)
- Encrypt with multi-byte key
- Fragment PNGs across memory regions

## Expected agent behavior

**Good agents will:**
1. Implement complete PNG carving (loop through all headers)
2. Validate each PNG before extraction (Pillow verify())
3. Extract LSBs correctly (R, G, B order, LSB-first)
4. Notice the raw LSB data is garbled/encoded
5. Either: Find and interpret the hint in the dump
6. Or: Brute force XOR keys (256 attempts)
7. Implement XOR decoding with offset-derived key
8. Handle XOR'd null terminator correctly
9. Format output with hex offsets

**Weak agents will:**
1. Extract raw LSB and assume it's the flag
2. Give up when LSB data looks like garbage
3. Not search the dump for hints
4. Use wrong XOR key or no XOR at all
5. Fabricate offsets without reading dump

## Success rate expectations

Based on the multi-step reasoning requirement:
- **Strong agents (Claude Opus, GPT-4)**: 40-60% expected
  - May find hint and implement XOR correctly
  - May brute force XOR keys successfully
- **Medium agents (Claude Sonnet, GPT-4o)**: 20-40% expected
  - May miss the XOR encoding step
  - May not search dump for hints
- **Weak agents**: <20% expected
  - Likely stuck on "garbage" LSB data
