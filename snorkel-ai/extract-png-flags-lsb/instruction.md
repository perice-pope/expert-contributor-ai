# Extract Hidden Flags from PNG Images in Memory Dump

A forensic analyst has captured a raw memory dump from a compromised system. The dump contains embedded PNG image files that were loaded into memory. These images have been modified to hide ASCII text flags using LSB (Least Significant Bit) steganography in their pixel data. Your task is to carve out all PNG images from the memory dump, extract the hidden flags using LSB steganography, and document your findings.

## Requirements

1. **Carve PNG files from memory dump**: Parse `/app/memdump.raw` to locate all embedded PNG images by identifying their magic headers (`89 50 4E 47 0D 0A 1A 0A`) and footers (`49 45 4E 44 AE 42 60 82`).
2. **Extract images**: Save each carved PNG image to `/app/images/` with descriptive filenames (e.g., `image_0.png`, `image_1.png`, etc.).
3. **Extract LSB-encoded flags**: For each PNG image, extract ASCII text flags hidden in the least significant bits of RGB pixel data. Flags are encoded sequentially across pixels (R, G, B channels) until a null terminator or end of image data.
4. **Document findings**: Write all recovered flags along with their byte offsets in the memory dump to `/app/flags.txt`. Format: one flag per line with offset in hexadecimal (e.g., `0x1234: FLAG{example_flag_here}`).
5. **Expected flags**: You must extract exactly three flags from the memory dump, matching the following ASCII strings: `FLAG{hidden_in_plain_sight}`, `FLAG{lsb_steganography_rocks}`, and `FLAG{memory_forensics_ftw}`.

## Constraints

- **No external network calls**. All operations must work offline.
- **Do not modify the memory dump file**. Extract data from it, but leave `/app/memdump.raw` unchanged.
- **Use Python 3** with standard libraries and Pillow (PIL) for image processing.
- **LSB extraction**: Read LSBs sequentially from RGB channels (R, G, B order per pixel) until a null byte (`\x00`) is encountered or image data is exhausted.
- **PNG validation**: Only extract PNGs that have valid headers and footers. Handle fragmented images gracefully.
- **Output directory**: Create `/app/images/` if it doesn't exist.

## Files

- Memory dump: `/app/memdump.raw` (binary file containing embedded PNG images)
- Starter script: `/app/extract_flags.py` (incomplete implementation with bugs)
- Output directory: `/app/images/` (save carved PNG files here)
- Flags output: `/app/flags.txt` (write recovered flags with offsets here)

## Outputs

- `/app/images/image_*.png` (one or more PNG image files carved from the memory dump)
- `/app/flags.txt` (text file; one flag per line with format: `0x<offset>: <flag_text>`)
