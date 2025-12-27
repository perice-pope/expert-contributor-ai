#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Analyzing memory dump for embedded PNG images..."

mkdir -p /app/images

python3 << 'PYTHON_EOF'
import os
import base64
import re
from PIL import Image
from io import BytesIO

PNG_HEADER = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
PNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'


def rot13(text):
    """Apply ROT13 decoding."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)


def multi_byte_xor(data, key_bytes):
    """XOR data with multi-byte key (cycling)."""
    return bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])


def looks_like_flag_part(text):
    """Check if text looks like part of a flag."""
    if not text or not text.isprintable():
        return False, 0
    
    score = 0
    
    # Strong indicators
    if text.startswith('FLAG{'):
        score += 100
    if text.endswith('}'):
        score += 50
    if '_' in text and text.replace('_', '').replace('{', '').replace('}', '').isalpha():
        score += 30
    
    # Check for common English patterns
    common_substrings = ['flag', 'expert', 'forensic', 'challenge', 'hidden', 'secret']
    for s in common_substrings:
        if s in text.lower():
            score += 40
    
    # Penalize if it looks like random letters
    if re.match(r'^[a-z]+_?$', text) and len(text) > 3:
        # Could be a word - check if it has vowels
        vowels = sum(1 for c in text if c in 'aeiou')
        if vowels >= len(text.replace('_', '')) * 0.2:
            score += 20
    
    return score > 0, score


def find_all_pngs(data):
    """Find all complete, valid PNG images in memory dump."""
    images = []
    offset = 0
    
    while True:
        header_pos = data.find(PNG_HEADER, offset)
        if header_pos == -1:
            break
        
        footer_pos = data.find(PNG_FOOTER, header_pos)
        if footer_pos == -1:
            offset = header_pos + 1
            continue
        
        png_end = footer_pos + len(PNG_FOOTER)
        png_data = data[header_pos:png_end]
        
        try:
            img = Image.open(BytesIO(png_data))
            img.verify()
            images.append((header_pos, png_data))
            print(f"[oracle] Valid PNG at 0x{header_pos:x}, {len(png_data)} bytes")
        except Exception as e:
            print(f"[oracle] Invalid PNG at 0x{header_pos:x}: {e}")
        
        offset = png_end
    
    return images


def extract_lsb_raw(image_data):
    """Extract raw LSB bytes from image."""
    try:
        img = Image.open(BytesIO(image_data))
        img = img.convert('RGB')
        pixels = img.load()
        width, height = img.size
        
        bits = []
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                bits.append(r & 1)
                bits.append(g & 1)
                bits.append(b & 1)
        
        raw_bytes = []
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits):
                break
            byte_val = 0
            for j in range(8):
                byte_val |= (bits[i + j] << j)
            raw_bytes.append(byte_val)
            if byte_val == 0:
                break
        
        return bytes(raw_bytes[:-1]) if raw_bytes and raw_bytes[-1] == 0 else bytes(raw_bytes)
    except Exception as e:
        print(f"[oracle] LSB extraction error: {e}")
        return b''


def try_all_decodings(raw_bytes, offset):
    """Try all decoding schemes and return all valid results with scores."""
    results = []
    
    # Scheme 1: Multi-byte XOR with 2-byte offset key
    try:
        xor_key = [(offset >> 8) & 0xFF, offset & 0xFF]
        decoded = multi_byte_xor(raw_bytes, xor_key)
        text = decoded.decode('ascii', errors='strict')
        is_flag, score = looks_like_flag_part(text)
        if text.isprintable():
            results.append(('xor', text, score + 5))  # Small bonus for XOR
            print(f"[oracle] XOR key={xor_key}: '{text}' (score={score + 5})")
    except:
        pass
    
    # Scheme 2: ROT13
    try:
        text = raw_bytes.decode('ascii', errors='strict')
        decoded = rot13(text)
        is_flag, score = looks_like_flag_part(decoded)
        if decoded.isprintable():
            results.append(('rot13', decoded, score))
            print(f"[oracle] ROT13: '{decoded}' (score={score})")
    except:
        pass
    
    # Scheme 3: Base64
    try:
        text = raw_bytes.decode('ascii', errors='strict')
        decoded = base64.b64decode(text).decode('ascii')
        is_flag, score = looks_like_flag_part(decoded)
        if decoded.isprintable():
            results.append(('base64', decoded, score + 10))  # Bonus for valid base64
            print(f"[oracle] Base64: '{decoded}' (score={score + 10})")
    except:
        pass
    
    # Scheme 4: Plain ASCII
    try:
        text = raw_bytes.decode('ascii', errors='strict')
        is_flag, score = looks_like_flag_part(text)
        if text.isprintable():
            results.append(('plain', text, score))
            print(f"[oracle] Plain: '{text}' (score={score})")
    except:
        pass
    
    return results


# Main execution
memdump_path = '/app/memdump.raw'
images_dir = '/app/images'
flags_path = '/app/flags.txt'

with open(memdump_path, 'rb') as f:
    memdump_data = f.read()

print(f"[oracle] Memory dump: {len(memdump_data)} bytes")

png_images = find_all_pngs(memdump_data)
print(f"[oracle] Found {len(png_images)} valid PNG(s)")

# Extract and decode from each image
all_parts = []
for idx, (offset, png_data) in enumerate(png_images):
    image_path = os.path.join(images_dir, f'image_{idx}.png')
    with open(image_path, 'wb') as f:
        f.write(png_data)
    
    raw_bytes = extract_lsb_raw(png_data)
    print(f"[oracle] Image {idx} at 0x{offset:x}: raw = {raw_bytes[:20]}...")
    
    decoded_results = try_all_decodings(raw_bytes, offset)
    
    # Select the result with highest score
    if decoded_results:
        decoded_results.sort(key=lambda x: x[2], reverse=True)
        best = decoded_results[0]
        scheme, text, score = best
        all_parts.append((offset, text, scheme))
        print(f"[oracle] Selected: {scheme} -> '{text}' (score={score})")

# Sort by offset to get correct order
all_parts.sort(key=lambda x: x[0])

# Combine flag parts
combined_flag = ''.join([part[1] for part in all_parts])
print(f"[oracle] Combined flag: {combined_flag}")

# Write output
with open(flags_path, 'w') as f:
    for offset, text, scheme in all_parts:
        f.write(f'0x{offset:x}: {text}\n')

print(f"[oracle] Wrote {len(all_parts)} part(s) to {flags_path}")
PYTHON_EOF

echo "[oracle] Extraction complete"
echo ""
echo "=== Results ==="
cat /app/flags.txt
