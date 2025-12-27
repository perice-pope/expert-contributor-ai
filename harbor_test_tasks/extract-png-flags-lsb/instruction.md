# Extract Hidden Flags from PNG Images in Memory Dump

A forensic analyst has captured a raw memory dump from a compromised system. Intelligence suggests the dump contains embedded PNG image files that may hide secret information using steganographic techniques. Your task is to analyze the memory dump, recover any PNG images, and extract any hidden data.

## Requirements

1. **Analyze memory dump**: Examine `/app/memdump.raw` to identify and extract any embedded PNG images. The dump contains noise, partial data, corrupted regions, and red herrings.
2. **Extract valid images**: Save any complete, valid PNG images found to `/app/images/` with sequential filenames (e.g., `image_0.png`, `image_1.png`, etc.).
3. **Recover hidden data**: Investigate the extracted images for hidden information. The hidden data may use various encoding or obfuscation techniques that you must identify and reverse.
4. **Document findings**: Write all recovered data to `/app/flags.txt`. Format: one entry per line with the byte offset where the image was found (e.g., `0x1234: <recovered_data>`).

## Constraints

- **No external network calls**. All operations must work offline.
- **Do not modify the memory dump file**. Extract data from it, but leave `/app/memdump.raw` unchanged.
- **Use Python 3** with standard libraries. Pillow (PIL) is available for image processing.
- **PNG validation**: Only extract images that are complete and valid. Handle incomplete or corrupted data gracefully.
- **Output directory**: Create `/app/images/` if it doesn't exist.

## Files

- Memory dump: `/app/memdump.raw` (binary file containing embedded images among other data)
- Starter script: `/app/extract_flags.py` (minimal skeleton)
- Output directory: `/app/images/` (save extracted PNG files here)
- Output file: `/app/flags.txt` (write recovered data with offsets here)

## Outputs

- `/app/images/image_*.png` (extracted PNG image files)
- `/app/flags.txt` (text file with recovered data; format: `0x<offset>: <data>`)

## Notes

- The memory dump contains various data structures, partial files, noise, and decoys
- Not all PNG-like byte patterns represent valid images
- Hidden data may be encoded, obfuscated, or split across multiple sources
- The complete solution requires careful analysis and may involve multiple steps
- Pay attention to the order of extracted data
