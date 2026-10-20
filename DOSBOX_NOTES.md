# DOSBox wrapper notes for perfect whole-file compatibility

The pure-Python path produces bit-exact ROM payload regions, header, and trailing template.
The gap/filler regions receive a simple periodic marker and are not byte-identical to every original sample.

If you need a byte-for-byte identical #EX (including gaps), use the original EXEs under DOSBox:

## Setup
1. Install DOSBox.
2. Create a working directory, e.g. `C:\FANUC`.
3. Copy into it:
   - `UNROM.EXE`
   - Your two 32 KB ROM images

## Run
```
dosbox
mount c C:\FANUC
c:
UNROM
```
Follow the prompts (output #EX name, then ROM1, then ROM2).

For the reverse direction use `ROM.EXE` the same way.

## Why keep both
- Python path: modern, scriptable, no DOS dependency, payload-correct for Fladder.
- DOSBox path: perfect whole-file match if a downstream tool is picky about the gap bytes.

The Python tool remains the recommended daily driver.
