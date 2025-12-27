#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Step 1: Analyzing memory dump for embedded PNG images..."

# Create images directory
mkdir -p /app/images

echo "[oracle] Step 2: Carving PNG images and extracting XOR-encoded LSB flags..."

# Use Python for reliable binary processing
python3 << 'PYTHON_EOF'
import os
from PIL import Image
from io import BytesIO

PNG_HEADER = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
PNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'

def find_all_pngs(data):
    """Find all complete, valid PNG images in the memory dump."""
    images = []
    offset = 0
    
    while True:
        header_pos = data.find(PNG_HEADER, offset)
        if header_pos == -1:
            break
        
        # Find the corresponding footer
        footer_pos = data.find(PNG_FOOTER, header_pos)
        if footer_pos == -1:
            # Incomplete PNG, skip
            offset = header_pos + 1
            continue
        
        # Extract complete PNG
        png_end = footer_pos + len(PNG_FOOTER)
        png_data = data[header_pos:png_end]
        
        # Validate it's actually a valid PNG by trying to open it
        try:
            img = Image.open(BytesIO(png_data))
            img.verify()
            images.append((header_pos, png_data))
            print(f"[oracle] Found valid PNG at offset 0x{header_pos:x}, size {len(png_data)} bytes")
        except Exception as e:
            print(f"[oracle] Invalid/corrupted PNG at offset 0x{header_pos:x}, skipping: {e}")
        
        # Continue searching after this PNG
        offset = png_end
    
    return images

def extract_lsb_with_xor(image_data, offset):
    """
    Extract ASCII flag from XOR-encoded LSB steganography.
    
    The hidden data is XOR'd with a key derived from the PNG's offset.
    Key = low byte of offset (offset & 0xFF)
    """
    try:
        img = Image.open(BytesIO(image_data))
        img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        
        # Calculate XOR key from offset
        xor_key = offset & 0xFF
        print(f"[oracle] Using XOR key: 0x{xor_key:02x} (from offset 0x{offset:x})")
        
        # Extract LSBs in R, G, B order
        bits = []
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                bits.append(r & 1)
                bits.append(g & 1)
                bits.append(b & 1)
        
        # Convert bits to bytes (8 bits per byte, LSB first)
        raw_bytes = []
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits):
                break
            byte_val = 0
            for j in range(8):
                byte_val |= (bits[i + j] << j)
            raw_bytes.append(byte_val)
            
            # Check for XOR'd null terminator
            if byte_val == xor_key:  # 0x00 ^ xor_key = xor_key
                break
        
        # XOR decode
        decoded_bytes = bytes([b ^ xor_key for b in raw_bytes])
        flag = decoded_bytes.rstrip(b'\x00').decode('ascii', errors='ignore')
        
        return flag
    except Exception as e:
        print(f"[oracle] Error extracting flag: {e}")
        return None

# Main execution
memdump_path = '/app/memdump.raw'
images_dir = '/app/images'
flags_path = '/app/flags.txt'

# Read memory dump
with open(memdump_path, 'rb') as f:
    memdump_data = f.read()

print(f"[oracle] Memory dump size: {len(memdump_data)} bytes")

# Look for hints in the dump about encryption
if b'key = offset & 0xFF' in memdump_data or b'key derivation' in memdump_data.lower():
    print("[oracle] Found hint: key derivation uses offset")

# Find all valid PNG images
png_images = find_all_pngs(memdump_data)

print(f"[oracle] Found {len(png_images)} valid PNG image(s)")

# Extract flags from each image
flags = []
for idx, (offset, png_data) in enumerate(png_images):
    # Save PNG image
    image_path = os.path.join(images_dir, f'image_{idx}.png')
    with open(image_path, 'wb') as f:
        f.write(png_data)
    print(f"[oracle] Saved image_{idx}.png from offset 0x{offset:x}")
    
    # Extract flag with XOR decoding
    flag = extract_lsb_with_xor(png_data, offset)
    if flag and flag.startswith('FLAG{'):
        flags.append((offset, flag))
        print(f"[oracle] Extracted flag: {flag}")
    else:
        print(f"[oracle] No valid flag found in image {idx} (got: {repr(flag[:50]) if flag else 'None'}...)")

# Write flags to file with proper format
with open(flags_path, 'w') as f:
    for offset, flag in flags:
        f.write(f'0x{offset:x}: {flag}\n')

print(f"[oracle] Wrote {len(flags)} flag(s) to {flags_path}")
PYTHON_EOF

echo "[oracle] Step 3: Extraction complete"

# Show results
echo ""
echo "=== Results ==="
cat /app/flags.txt
