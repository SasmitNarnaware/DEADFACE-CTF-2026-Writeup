# DEADFACE CTF — "headshot" (steg / 10 pts)

**Flag: `deadface{b00m_h34Dsh0TTT}`**

## Challenge

> DEADFACE compromised a fileshare of Aurora Health corporate headshots and is tagging
> the photos with info that tells their group which employees to target next.
> Figure out which image was tampered with.

Files (from `headshot.zip`):

| file | size | notes |
|---|---|---|
| `headshot001.png` | 169 920 | clean |
| `headshot002.png` | 174 949 | clean |
| `headshot003.png` | 182 911 | **tampered** |
| `headshot003.png_original` | 182 866 | pristine copy, shipped in the zip |

## Solution

### 1. Split every PNG into chunks (`analyze.py`)

All three images are 512x512, 8-bit paletted PNGs (`IHDR / PLTE / tRNS / pHYs / IDAT / IEND`).
Only one file has an extra chunk:

```
== headshot003.png
    ...
    pHYs  9
    tEXt  33  b'Comment\x00deadface{b00m_h34Dsh0TTT}'
    IDAT  181740
    IEND  0
```

### 2. Prove 003 is the tampered one (`verify.py`)

* The `tEXt` chunk has a **valid CRC** (`zlib.crc32` matches) — it was written by a real
  PNG writer, not appended garbage.
* Rebuilding `headshot003.png` **without** the `tEXt` chunk yields a byte-for-byte exact
  match with `headshot003.png_original` → the only difference between the two is the
  45-byte inserted comment chunk (4 len + 4 type + 33 data + 4 CRC).
* Decoded pixels of `headshot003.png` and `_original` are **identical** (max diff = 0),
  so nothing was changed visually — the payload is purely metadata.
* `headshot001/002` have no extra chunks, no trailing bytes after `IEND`, no zip
  comments/extra fields, and their LSB planes show natural-image entropy (no embedded
  compressed stream, no `PK`/`JFIF`/`deadface` header in any bit plane) — `lsb_check.py`.

### 3. Read the payload

The author's stego tool wrote a PNG `tEXt` comment on `headshot003.png` (and left its
automatic `headshot003.png_original` backup in the archive — the giveaway that this is
the file DEADFACE touched).

```
Comment = deadface{b00m_h34Dsh0TTT}
```

## Answer

`deadface{b00m_h34Dsh0TTT}`

## Files

* `analyze.py` — dumps PNG chunks of every file
* `verify.py` — CRC check, rebuild-minus-tEXt equality test, pixel diff, LSB stats, metadata scan
* `lsb_check.py` — per-channel/palette LSB entropy + signature hunt, trailing-data check
* `flag.txt` — the flag
