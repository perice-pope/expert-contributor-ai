# Maintainer Notes

## What this task is testing

Expert-level forensic image extraction with multi-scheme steganography:

1. Parse raw memory dump to locate embedded PNG images
2. Carve complete PNG files (filter invalid/corrupted structures)
3. Extract LSB steganography data from each image
4. **Recognize and decode THREE different encoding schemes**
5. **Combine partial flags in correct order**
6. Document findings with proper formatting

The task requires understanding of:
- Binary file parsing and PNG magic number detection
- PNG file format validation
- LSB steganography extraction (RGB channels, LSB-first bits)
- **Multiple encoding schemes**: Multi-byte XOR, ROT13, Base64
- **Pattern recognition**: Identifying which encoding applies to each image
- **Data combination**: Merging partial results in offset order

## Expert-Level Difficulty Features (v3)

**Original**: TRIVIAL (100% agent success)
**After fake PNGs**: Still 100%
**After single XOR + hint**: Still 100%
**Current (v3)**: Target 30-70%

### All 5 difficulty increases implemented:

1. **NO HINTS** - Zero clues in the dump about encoding schemes
2. **Multi-byte XOR key** - 2-byte key from offset (not just low byte)
3. **Different encoding per image**:
   - Image 1 (0x800): Multi-byte XOR with [offset>>8, offset&0xFF]
   - Image 2 (0x1500): ROT13
   - Image 3 (0x2800): Base64
4. **Split flag** - Must combine parts in correct order:
   - Part 1: `FLAG{expert_`
   - Part 2: `forensics_`
   - Part 3: `challenge}`
   - Combined: `FLAG{expert_forensics_challenge}`
5. **Red herrings**:
   - 3 fake/corrupted PNG structures
   - Decoy plaintext: `flag{this_is_not_the_real_flag}`
   - Decoy base64: `RkxBR3tub3RfdGhlX3JlYWxfZmxhZ30=`
   - Misleading "ENCRYPTED_DATA_BLOCK" text

### Memory dump structure:
- ~12.5KB total size
- 3 real PNGs with different encodings
- 3 fake/corrupted PNG structures
- Multiple decoys and noise sections
- NO hints about encoding

## Intended failure modes

### 1. Not trying multiple decoding schemes
- **Problem**: Agent only tries standard LSB, gets garbage
- **Result**: No readable flag parts
- **This is the primary difficulty lever**

### 2. Wrong XOR key derivation
- **Problem**: Using single-byte key instead of 2-byte offset
- **Result**: Part 1 still garbled

### 3. Not recognizing ROT13
- **Problem**: Agent sees "sberafvpf_" and doesn't recognize ROT13
- **Result**: Missing part 2

### 4. Not recognizing Base64
- **Problem**: Agent sees "Y2hhbGxlbmdlfQ==" and doesn't decode
- **Result**: Missing part 3

### 5. Wrong combination order
- **Problem**: Parts combined in wrong order
- **Result**: Garbled combined flag (e.g., "forensics_FLAG{expert_challenge}")

### 6. Giving up on "garbled" data
- **Problem**: Raw LSB looks like garbage, agent assumes no hidden data
- **Result**: No flags extracted

### 7. Only trying one encoding scheme globally
- **Problem**: Agent applies same decoding to all images
- **Result**: At most 1/3 parts decoded correctly

## Why this is genuinely hard

### Multi-step reasoning required:
1. Carve valid PNGs (filter fakes)
2. Extract raw LSB bytes
3. Recognize data is encoded (not plaintext)
4. Try multiple decoding schemes per image
5. Identify which scheme works for each
6. Combine results in correct (offset) order

### No hints available:
- Dump contains NO indication of encoding schemes
- Must use pattern recognition or brute-force
- ROT13 and Base64 are recognizable patterns
- XOR requires understanding offset relationship

### Pattern recognition challenges:
- ROT13 text looks like scrambled ASCII (sberafvpf_)
- Base64 has characteristic = padding and charset
- XOR produces seemingly random bytes

## Oracle solution approach

The Oracle implements:
1. Standard PNG carving with validation
2. Raw LSB extraction
3. Tries ALL encoding schemes on each image:
   - Multi-byte XOR with 2-byte offset key
   - ROT13
   - Base64
   - Plain ASCII (fallback)
4. Selects results that look like flag parts (FLAG{, _, })
5. Sorts by offset and combines

## Determinism and reproducibility

### Fixed inputs (seed=42):
- Memory dump pre-generated
- Flag parts at fixed offsets:
  - 0x800: "FLAG{expert_" (XOR)
  - 0x1500: "forensics_" (ROT13)
  - 0x2800: "challenge}" (Base64)
- Combined: `FLAG{expert_forensics_challenge}`

### Tool versions:
- Python: 3.11-slim-bookworm
- Pillow: 10.0.0
- pytest: 8.4.1

## Success rate expectations

Based on multi-scheme recognition requirement:
- **Strong agents (Claude Opus, GPT-4)**: 20-40% expected
  - May recognize ROT13/Base64 patterns
  - May figure out multi-byte XOR
- **Medium agents (Claude Sonnet, GPT-4o)**: 10-30% expected
  - Likely to miss at least one encoding scheme
  - May not combine in correct order
- **Weak agents**: <10% expected
  - Stuck on "garbage" LSB data
  - Only try single encoding scheme

## To make easier (if needed)
- Add subtle hints about encodings in dump
- Use single-byte XOR instead of multi-byte
- Use same encoding for all images
- Don't split the flag

## To make harder (if needed)
- Add encryption (AES) requiring key derivation
- Use custom encoding schemes
- Fragment PNGs across non-contiguous regions
- Add more decoys and red herrings
