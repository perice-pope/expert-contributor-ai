#!/usr/bin/env python3
"""
Extract PNG images from memory dump and decode LSB steganography flags.

This script has several bugs that need to be fixed:
- PNG carving may not find all images
- LSB extraction may have issues with channel order or bit reading
- Flag output format may be incorrect
"""

import os
from PIL import Image
from io import BytesIO

# PNG magic numbers
PNG_HEADER = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
PNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'

def find_png_images(data):
    """Find all PNG images in the memory dump."""
    images = []
    offset = 0
    
    # BUG: Only finds first PNG, doesn't continue searching after first match
    while True:
        header_pos = data.find(PNG_HEADER, offset)
        if header_pos == -1:
            break
        
        # Find the corresponding footer
        footer_pos = data.find(PNG_FOOTER, header_pos)
        if footer_pos == -1:
            # If no footer found, skip this header
            offset = header_pos + 1
            continue
        
        # Extract PNG data
        png_end = footer_pos + len(PNG_FOOTER)
        png_data = data[header_pos:png_end]
        
        images.append((header_pos, png_data))
        
        # BUG: Should continue searching, but breaks after first
        break
    
    return images

def extract_lsb_flag(image_data):
    """
    Extract ASCII flag from LSB steganography in PNG image.
    
    BUG: May have issues with:
    - Channel order (should be R, G, B per pixel)
    - Bit extraction (may read wrong bits)
    - Null terminator handling
    """
    try:
        img = Image.open(BytesIO(image_data))
        # BUG: Doesn't convert to RGB - may fail for RGBA or other modes
        # Should do: img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        
        bits = []
        for y in range(height):
            for x in range(width):
                # BUG: Assumes RGB mode, doesn't handle RGBA
                r, g, b = pixels[x, y][:3]  # May fail for non-RGB modes
                
                # Extract LSBs
                # BUG: Order might be wrong - should be R, G, B
                bits.append(r & 1)
                bits.append(g & 1)
                bits.append(b & 1)
        
        # Convert bits to bytes
        flag_bytes = []
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits):
                break
            byte_val = 0
            for j in range(8):
                byte_val |= (bits[i + j] << j)  # BUG: Bit order might be wrong
            flag_bytes.append(byte_val)
            
            # Stop at null terminator
            if byte_val == 0:
                break
        
        # BUG: May not handle encoding correctly
        flag = bytes(flag_bytes).decode('ascii', errors='ignore').rstrip('\x00')
        return flag
    except Exception:
        # BUG: Silently fails, should log or handle better
        return None

def main():
    """Main extraction function."""
    memdump_path = '/app/memdump.raw'
    images_dir = '/app/images'
    flags_path = '/app/flags.txt'
    
    # Create images directory
    os.makedirs(images_dir, exist_ok=True)
    
    # Read memory dump
    with open(memdump_path, 'rb') as f:
        memdump_data = f.read()
    
    # Find PNG images
    png_images = find_png_images(memdump_data)
    
    # Extract flags from each image
    flags = []
    for idx, (offset, png_data) in enumerate(png_images):
        # Save PNG image
        image_path = os.path.join(images_dir, f'image_{idx}.png')
        with open(image_path, 'wb') as f:
            f.write(png_data)
        
        # Extract flag
        flag = extract_lsb_flag(png_data)
        if flag:
            # BUG: May not format offset correctly (should be hex with 0x prefix)
            flags.append((offset, flag))
    
    # Write flags to file
    # BUG: May not format correctly - should be "0x<hex>: <flag>"
    with open(flags_path, 'w') as f:
        for offset, flag in flags:
            f.write(f'{offset}: {flag}\n')

if __name__ == '__main__':
    main()

