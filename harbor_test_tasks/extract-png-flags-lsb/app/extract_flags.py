#!/usr/bin/env python3
"""
Starter script for PNG extraction and LSB steganography.

Your task: implement the missing functionality to extract hidden flags
from PNG images embedded in a memory dump.

Hints:
- PNG files have specific magic bytes that identify them
- LSB steganography hides data in the least significant bits of pixel values
- Flags are ASCII text ending with a null byte
"""

import os

# TODO: Implement PNG carving from memory dump
# TODO: Implement LSB extraction from PNG images
# TODO: Write findings to /app/flags.txt

def main():
    """Main extraction function - implement this."""
    memdump_path = '/app/memdump.raw'
    images_dir = '/app/images'
    flags_path = '/app/flags.txt'
    
    # Create images directory
    os.makedirs(images_dir, exist_ok=True)
    
    # TODO: Read memory dump
    # TODO: Find and extract PNG images
    # TODO: Extract LSB-encoded flags from each image
    # TODO: Write flags with hex offsets to flags.txt
    
    raise NotImplementedError("You must implement PNG carving and LSB extraction")


if __name__ == '__main__':
    main()
