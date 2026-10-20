#!/usr/bin/env python3
"""
Fanuc 0M PMC Ladder ROM <-> Fladder II #EX converter
Clean-room modern reimplementation of the UNROM.EXE / ROM.EXE workflow.

Observed #EX layout (75360 bytes fixed):
  0-161:     162.BIN template header
  162-32929: ROM1 region — 409 records of (70 bytes payload + 10-byte marker)
  32930-37681: gap / filler
  37682-37761: 80.BIN template
  37762-70529: ROM2 region — same 70+10 packing
  70530-75281: gap / filler
  75282-75359: 78.BIN trailing template

Packing: each 80-byte record holds 70 bytes of ROM data followed by the
fixed marker ffffffffffffffff4040. Only the first 28630 bytes of each
ROM are stored; the tail is not present in the #EX.
"""

import sys
from pathlib import Path

ROM_SIZE = 32768
EX_SIZE = 75360
HEADER_162_SIZE = 162
TEMPLATE_80_SIZE = 80
TEMPLATE_78_SIZE = 78

ROM1_OFFSET = 162
TEMPLATE_80_OFFSET = 37682
ROM2_OFFSET = 37762
TEMPLATE_78_OFFSET = 75282

MARKER = bytes.fromhex("ffffffffffffffff4040")

# Embedded templates (structural headers used by the original UNROM)
TEMPLATE_162 = bytes.fromhex("4040f0c5f1f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f061f0f0f061f3f6f061f840f0f0f0f0f0f0f0f0ffffffffffffffff4040f0f0f0f0c5f1f0e0f1f0f0f0f0e0f1c6c6c6c6e0d3e300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005cffffffffffffffff4040")
TEMPLATE_80  = bytes.fromhex("f0f0f0f0c5f2f0e0f1f0f0f0f0e0f1c6c6c6c6e0c8e300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005cffffffffffffffff4040")
TEMPLATE_78  = bytes.fromhex("c5d5c400020002004040404040404040404040404040404040404040404040404040404040404040404040404040404040404040404040404040404040404040404040404040ffffffffffffffff")

def load_templates(template_dir: Path = None):
    """Return the three structural templates. Optional dir override kept for compatibility."""
    return {"162": TEMPLATE_162, "80": TEMPLATE_80, "78": TEMPLATE_78}

def pack_region(rom: bytes) -> bytes:
    """Pack ROM data into 70-byte payloads + 10-byte marker records.
    Fills exactly ROM_SIZE bytes (409 full records + 48 leftover zeros)."""
    region = bytearray(ROM_SIZE)
    pos = 0
    out = 0
    while out + 80 <= ROM_SIZE and pos < len(rom):
        take = min(70, len(rom) - pos)
        region[out:out + take] = rom[pos:pos + take]
        region[out + 70:out + 80] = MARKER
        pos += take
        out += 80
    return bytes(region)

def unpack_region(region: bytes) -> bytes:
    """Extract the 70-byte payloads from a packed ROM region."""
    payloads = []
    off = 0
    while off + 80 <= len(region):
        if region[off + 70:off + 80] == MARKER:
            payloads.append(region[off:off + 70])
            off += 80
        else:
            break
    return b"".join(payloads)

def fill_gaps(ex: bytearray):
    """Stamp a simple periodic marker pattern into the two gap regions
    for closer whole-file visual match. Stops short of the templates."""
    for start, end in ((32930, 37682), (70530, 75282)):
        off = start
        while off + 80 <= end:
            marker_pos = off + 60
            if marker_pos + 10 <= end:
                ex[marker_pos:marker_pos + 10] = MARKER
            off += 80

def combine_roms(rom1: bytes, rom2: bytes, templates: dict) -> bytes:
    """Produce a #EX image from two ROM binaries using the observed packing."""
    if len(rom1) != ROM_SIZE or len(rom2) != ROM_SIZE:
        raise ValueError(f"Each ROM must be exactly {ROM_SIZE} bytes")

    ex = bytearray(EX_SIZE)
    ex[0:HEADER_162_SIZE] = templates["162"]
    ex[ROM1_OFFSET:ROM1_OFFSET + ROM_SIZE] = pack_region(rom1)
    ex[TEMPLATE_80_OFFSET:TEMPLATE_80_OFFSET + TEMPLATE_80_SIZE] = templates["80"]
    ex[ROM2_OFFSET:ROM2_OFFSET + ROM_SIZE] = pack_region(rom2)
    ex[TEMPLATE_78_OFFSET:TEMPLATE_78_OFFSET + TEMPLATE_78_SIZE] = templates["78"]
    fill_gaps(ex)
    return bytes(ex)

def split_ex(ex: bytes) -> tuple[bytes, bytes]:
    """Extract the two ROM images from a #EX by unpacking the 70-byte payloads.
    Only the first 28630 bytes of each original ROM are stored;
    the remainder is zero-padded on extract."""
    if len(ex) != EX_SIZE:
        raise ValueError(f"#EX must be exactly {EX_SIZE} bytes")

    rom1 = unpack_region(ex[ROM1_OFFSET:ROM1_OFFSET + ROM_SIZE]).ljust(ROM_SIZE, b"\x00")
    rom2 = unpack_region(ex[ROM2_OFFSET:ROM2_OFFSET + ROM_SIZE]).ljust(ROM_SIZE, b"\x00")
    return rom1, rom2

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage:")
        print("  combine  <rom1.bin> <rom2.bin> <out.#EX> [template_dir]")
        print("  split    <in.#EX> <out_rom1.bin> <out_rom2.bin>")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "combine":
        if len(sys.argv) < 5:
            print("Need: rom1 rom2 out.#EX [template_dir]")
            sys.exit(1)
        rom1 = Path(sys.argv[2]).read_bytes()
        rom2 = Path(sys.argv[3]).read_bytes()
        out_path = Path(sys.argv[4])
        templates = load_templates()
        ex = combine_roms(rom1, rom2, templates)
        out_path.write_bytes(ex)
        print(f"Wrote {out_path} ({len(ex)} bytes)")

    elif cmd == "split":
        if len(sys.argv) < 5:
            print("Need: in.#EX out_rom1 out_rom2")
            sys.exit(1)
        ex = Path(sys.argv[2]).read_bytes()
        rom1, rom2 = split_ex(ex)
        Path(sys.argv[3]).write_bytes(rom1)
        Path(sys.argv[4]).write_bytes(rom2)
        print(f"Extracted ROM1 ({len(rom1)}) and ROM2 ({len(rom2)})")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
