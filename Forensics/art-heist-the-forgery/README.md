# Art Heist: The Forgery — Furie Forensics Writeup

## Challenge
The Turla Museum got five paintings back from a loan to a neighboring gallery.
DEADFACE allegedly infiltrated the gallery and swapped one original for a forgery.
All five were scanned into the museum's digital archive on return. Find the
compromised artwork and recover the flag left behind.

Format: `deadface{...}`

## Files
`CTF_Forgery_Paintings.zip` (9.35 MB)
- SHA256: `f4d4d1185b94639bfbcfadb81abbea667977760dd31834dfc52d4d65a846cb12`

Contents (all 1024×1024, 8-bit RGB PNG):

| File | Title (XMP) | Creator (XMP) |
|------|-------------|---------------|
| `Painting_001.png` | Starry Night Over the Cyber City | Vincent van Gogh |
| `Painting_002.png` | Mona Lisa Loading | Leonardo da Vinci / LAMIA |
| `Painting_003.png` | The Blue Scream of Death | Edvard Munch |
| `Painting_004.png` | The Card Players | Paul Cézanne |
| `Painting_005.png` | Sunflowers.exe | Vincent van Gogh |

(Plus a macOS `__MACOSX/` folder of `._` AppleDouble sidecar files — noise, no
challenge content.)

## Triage

**1. Filesystem timestamps** — four files share a mtime; one does not:

| File | LastWriteTime |
|------|---------------|
| Painting_001 | 02-09-2026 01:43 |
| **Painting_002** | **15-10-2026 09:17** |
| Painting_003 | 02-09-2026 01:49 |
| Painting_004 | 02-09-2026 01:50 |
| Painting_005 | 02-09-2026 01:51 |

Painting_002 was rewritten ~6 weeks after the rest of the set. Suspicious, but
timestamps survive `unzip` unreliably — so confirm in the file itself.

**2. PNG chunk structure** — every file parses cleanly as
`IHDR → (chunks) → IDAT… → IEND`. Nothing appended after `IEND`, no unknown
chunk types. The difference is in the *text* chunks:

Paintings 001, 003, 004, 005 all carry a single, uniform archival stamp:

```
tEXt: Software\0Atelier Archive
```

Painting_002 carries a completely different toolchain and an admission of guilt:

```
tEXt: Comment\0checksum mismatch; palette recovered from cache
tEXt: Software\0LAMIA Restoration Utility 0.0.13
```

**3. XMP metadata** — the genuine four have consistent provenance: a real artist
name, a description, a title, and `xmp:CreateDate == xmp:ModifyDate` (the
painting's historical date, e.g. `1889-06-01` for Starry Night).

Painting_002's XMP is the anomaly in every field:

```xml
<dc:creator>…<rdf:li>Leonardo da Vinci / LAMIA</rdf:li></dc:creator>
<dc:description>…Authenticity status: pending. Restoration log incomplete.…</dc:description>
<dc:identifier>deadface{L4MIA_SIGNS_HER_WORK}</dc:identifier>
<dc:rights>…LAMIA temporary acquisition…</dc:rights>
<dc:subject><rdf:Bag><rdf:li>archive; restoration; pending; checksum</rdf:li></rdf:Bag></dc:subject>
<dc:title>…Mona Lisa Loading…</dc:title>
<pdf:Keywords>portrait, renaissance, loading, cache, checksum</pdf:Keywords>

<xmp:CreateDate>1503-04-01T00:00:00</xmp:CreateDate>
<xmp:ModifyDate>2026-09-01T20:00:00</xmp:ModifyDate>
```

Create/Modify diverge (the only file where they do), a third-party "LAMIA"
restoration utility replaced the museum's `Atelier Archive` tool, and the
creator credit has been co-signed by the forger. That's the forged painting.

## Recovering the flag

No stego needed — the forger signed her work in the XMP `dc:identifier` field at
file offset 739:

```python
import re
data = open('Painting_002.png','rb').read()
re.findall(rb'deadface\{[^}]{0,80}\}', data, re.I)
# [b'deadface{L4MIA_SIGNS_HER_WORK}']
```

**Confirming there's no second layer.** Because the metadata mentions
"checksum mismatch / palette recovered from cache", I checked for stego as well:

- LSB bit planes (R, G, B) of all five images packed to bytes → no readable
  strings, no `deadface{` anywhere.
- Trailing bytes after `IEND` → none, all five terminate cleanly on the IEND
  chunk.
- Full raw byte scan of all five files → the flag string occurs exactly once,
  in Painting_002.

The checksum/cache comments are flavor text that also serve as the pointing
finger, not a second puzzle.

## Flag
```
deadface{L4MIA_SIGNS_HER_WORK}
```

## Notes
- "LAMIA" is the DEADFACE-affiliated forger persona referenced throughout the
  story; the challenge name and her utility version (`0.0.13`) are the tells.
- The `tEXt Comment` is the intended breadcrumb: a real restoration tool logging
  a checksum mismatch in the same file whose metadata it then rewrote.
- Timestamps are a hint, not proof — always confirm inside the file format
  itself. Here the metadata was conclusive on its own.
