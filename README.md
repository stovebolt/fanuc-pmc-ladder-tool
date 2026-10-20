# Fanuc 0M PMC Ladder ROM ↔ #EX Tool

Clean-room Python reimplementation of the classic Fanuc UNROM.EXE / ROM.EXE workflow used to move Programmable Machine Controller (PMC) ladder images between EPROM pairs and the FAPT LADDER II / Fladder `#EX` format.

## What it does
- **Combine**: two 32 KB ROM images (OE1 + OE2) → fixed 75 360-byte `#EX` that Fladder can discompile.
- **Split**: `#EX` → two ROM images (first 28 630 bytes of each original ROM recovered; tail zero-padded).

## Format notes
The `#EX` is a fixed-size file with this layout:

| Offset   | Length | Content |
|----------|--------|---------|
| 0        | 162    | Structural header template |
| 162      | 32 768 | ROM1 region — 409 records of (70-byte payload + 10-byte marker) |
| 32 930   | 4 752  | Gap / filler |
| 37 682   | 80     | Structural template |
| 37 762   | 32 768 | ROM2 region — same 70+10 packing |
| 70 530   | 4 752  | Gap / filler |
| 75 282   | 78     | Trailing template |

Each 80-byte record holds 70 bytes of ROM data followed by the marker `ffffffffffffff4040`.

Payload regions, header, and trailing template match the original UNROM output on the tested sample pairs. Gap bytes receive a simple periodic marker and are not required for Fladder.

## Usage
```bash
# Combine
python3 fanuc_pmc_tool.py combine OE1.BIN OE2.BIN out.#EX

# Split
python3 fanuc_pmc_tool.py split in.#EX out1.BIN out2.BIN

# GUI
python3 fanuc_pmc_gui.py
```

## Files
- `fanuc_pmc_tool.py` — CLI and core logic (templates embedded)
- `fanuc_pmc_gui.py` — simple tkinter GUI
- `test_roundtrip.py` — verification harness (requires sample pairs; optional)
- `DOSBOX_NOTES.md` — how to run the original EXEs under DOSBox if needed

## License / scope
Clean-room format reverse and reimplementation for archival and right-to-repair use on aging Fanuc 0M-era machines. Does not include original Fanuc software or copyrighted ladder content.
