# Extract Hidden Flags from PNG Images in Memory Dump

A forensic analyst has captured a raw memory dump from a compromised system. Intelligence suggests the dump contains embedded PNG image files that may hide secret information using steganographic techniques. Your task is to analyze the memory dump, recover any PNG images, and extract any hidden data.

## Requirements

1. **Analyze memory dump**: Examine `/app/memdump.raw` to identify and extract any embedded PNG images. The dump may contain noise, partial data, or corrupted regions.
2. **Extract valid images**: Save any complete, valid PNG images found to `/app/images/` with sequential filenames (e.g., `image_0.png`, `image_1.png`, etc.).
3. **Recover hidden data**: Investigate the extracted images for hidden information. Images may contain steganographically encoded ASCII text flags. Note that the hidden data may be obfuscated or encoded.
4. **Document findings**: Write all recovered flags to `/app/flags.txt`. Format: one flag per line with the byte offset where the image was found (e.g., `0x1234: FLAG{example}`).

## Constraints

- **No external network calls**. All operations must work offline.
- **Do not modify the memory dump file**. Extract data from it, but leave `/app/memdump.raw` unchanged.
- **Use Python 3** with standard libraries. Pillow (PIL) is available for image processing.
- **PNG validation**: Only extract images that are complete and valid. Handle incomplete or corrupted data gracefully.
- **Output directory**: Create `/app/images/` if it doesn't exist.

## Files

- Memory dump: `/app/memdump.raw` (binary file that may contain embedded images)
- Starter script: `/app/extract_flags.py` (minimal skeleton - you must implement the logic)
- Output directory: `/app/images/` (save extracted PNG files here)
- Flags output: `/app/flags.txt` (write recovered flags with offsets here)

## Outputs

- `/app/images/image_*.png` (extracted PNG image files)
- `/app/flags.txt` (text file with recovered flags; format: `0x<offset>: <flag_text>`)

## Notes

- The memory dump may contain various data structures, partial files, and noise
- Not all PNG-like byte patterns may represent valid images
- At least 3 valid images with hidden flags are expected to be recoverable
- Flags follow the format `FLAG{...}` and contain ASCII text
- The memory dump itself may contain clues about how data was encoded
- Pay attention to relationships between image locations and any encoding used
