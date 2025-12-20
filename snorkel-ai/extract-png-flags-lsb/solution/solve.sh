#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Step 1: Carving PNG images from memory dump..."

# Create images directory
mkdir -p /app/images

# Read memory dump
memdump_data=$(cat /app/memdump.raw | base64 -w 0)
# Actually, let's use Python for this - it's more reliable for binary data

echo "[oracle] Step 2: Finding all PNG images by magic headers and footers..."

# Use Python to carve PNGs and extract flags
python3 << 'PYTHON_EOF'
import os
from PIL import Image
from io import BytesIO

PNG_HEADER = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
PNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'

def find_all_pngs(data):
    """Find all PNG images in the memory dump."""
    images = []
    offset = 0
    
    while True:
        header_pos = data.find(PNG_HEADER, offset)
        if header_pos == -1:
            break
        
        # Find the corresponding footer
        footer_pos = data.find(PNG_FOOTER, header_pos)
        if footer_pos == -1:
            # Skip incomplete PNG
            offset = header_pos + 1
            continue
        
        # Extract complete PNG
        png_end = footer_pos + len(PNG_FOOTER)
        png_data = data[header_pos:png_end]
        
        images.append((header_pos, png_data))
        
        # Continue searching after this PNG
        offset = png_end
    
    return images

def extract_lsb_flag(image_data):
    """Extract ASCII flag from LSB steganography."""
    try:
        img = Image.open(BytesIO(image_data))
        # Convert to RGB to handle RGBA and other modes
        img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        
        bits = []
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                
                # Extract LSBs in R, G, B order
                bits.append(r & 1)
                bits.append(g & 1)
                bits.append(b & 1)
        
        # Convert bits to bytes (8 bits per byte, LSB first)
        flag_bytes = []
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits):
                break
            byte_val = 0
            for j in range(8):
                byte_val |= (bits[i + j] << j)  # LSB first
            flag_bytes.append(byte_val)
            
            # Stop at null terminator
            if byte_val == 0:
                break
        
        # Decode ASCII
        flag = bytes(flag_bytes).decode('ascii', errors='ignore').rstrip('\x00')
        return flag
    except Exception as e:
        print(f"Error extracting flag: {e}", file=os.sys.stderr)
        return None

# Main execution
memdump_path = '/app/memdump.raw'
images_dir = '/app/images'
flags_path = '/app/flags.txt'

# Read memory dump
with open(memdump_path, 'rb') as f:
    memdump_data = f.read()

# Find all PNG images
png_images = find_all_pngs(memdump_data)

print(f"[oracle] Found {len(png_images)} PNG image(s)")

# Extract flags from each image
flags = []
for idx, (offset, png_data) in enumerate(png_images):
    # Save PNG image
    image_path = os.path.join(images_dir, f'image_{idx}.png')
    with open(image_path, 'wb') as f:
        f.write(png_data)
    print(f"[oracle] Saved image {idx} at offset 0x{offset:x}")
    
    # Extract flag
    flag = extract_lsb_flag(png_data)
    if flag:
        flags.append((offset, flag))
        print(f"[oracle] Extracted flag: {flag}")
    else:
        print(f"[oracle] Warning: Could not extract flag from image {idx}")

# Write flags to file with proper format
with open(flags_path, 'w') as f:
    for offset, flag in flags:
        f.write(f'0x{offset:x}: {flag}\n')

print(f"[oracle] Wrote {len(flags)} flag(s) to {flags_path}")
PYTHON_EOF

echo "[oracle] Step 3: Validation complete"
