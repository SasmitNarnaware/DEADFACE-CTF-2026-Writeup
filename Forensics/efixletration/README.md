# Writeup — Exifltration (DEADFACE CTF)

**Flag:** `deadface{timing-is-everything}`

---

## 1. Challenge

> DEADFACE frequently uses unconventional methods to exchange information and
> avoid detection. Analysts recovered a set of images from a compromised
> communications channel that appear unrelated at first glance. We suspect the
> collection contains a hidden message intended for other members of the group.
> Recover the message and identify what DEADFACE is trying to say.

**Files:** `image_01.jpg` … `image_20.jpg` (plus `exfiltration.zip`, the same set)

---

## 2. Recon

Opening the images shows 20 small, unrelated pictures (307–308 × 256 px). No
obvious visual pattern, so we go straight to metadata. The challenge hint
("unconventional methods to exchange information") points at steganography or
hidden metadata — and EXIF is the natural first stop.

```bash
exiftool image_*.jpg
```

Everything looks boilerplate **except** one field that stands out:

```
Exif ImageUniqueID = IMG_6465
```

Per-image values:

| File | ImageUniqueID |
|---|---|
| image_01 | `IMG_6365` |
| image_02 | `IMG_2d69` |
| image_03 | `IMG_6466` |
| image_04 | `IMG_6572` |
| image_05 | `IMG_696e` |
| image_06 | `IMG_69` |
| image_07 | `IMG_6465` |
| image_08 | `IMG_7469` |
| image_09 | `IMG_2d65` |
| image_10 | `IMG_7468` |
| image_11 | `IMG_7d` |
| image_12 | `IMG_7b` |
| image_13 | `IMG_76` |
| image_14 | `IMG_61` |
| image_15 | `IMG_79` |
| image_16 | `IMG_67` |
| image_17 | `IMG_6e67` |
| image_18 | `IMG_73` |
| image_19 | `IMG_61` |
| image_20 | `IMG_6d` |

A real `ImageUniqueID` would be an MD5 hash or an opaque serial. These are
**hex-encoded ASCII**.

---

## 3. Decoding the fragments

Strip the `IMG_` prefix, hex-decode, and keep going:

```
6365 -> ce
2d69 -> -i
6466 -> df
6572 -> er
696e -> in
69   -> i
6465 -> de
7469 -> ti
2d65 -> -e
7468 -> th
7d   -> }
7b   -> {
76   -> v
61   -> a
79   -> y
67   -> g
6e67 -> ng
73   -> s
61   -> a
6d   -> m
```

We get 20 short fragments: `de`, `a`, `df`, `a`, `ce`, `{`, `ti`, `m`, `in`,
`g`, `-i`, `s`, `-e`, `v`, `er`, `y`, `th`, `i`, `ng`, `}`.

Concatenating them **in filename order** gives garbage:

```
ce -i df er in i de ti -e th } { v a y g ng -i s -e v er y th i ng }
```

So the fragments are real, but the ordering is wrong. We need the key that
puts them back in sequence.

---

## 4. The key is time

The filenames (`image_01` … `image_20`) are a red herring — they're sorted, but
arbitrarily. The remaining distinctive EXIF field is **`DateTimeOriginal`**, and
remember the flag itself hints at it:

> **timing**-is-everything

Every image was "taken" on `2026:06:01`, within a ~70-minute window, at
irregular intervals. Sorting by timestamp:

| Time | File | Hex | Decoded |
|---|---|---|---|
| 14:02:17 | image_07 | `6465` | `de` |
| 14:04:52 | image_14 | `61`   | `a` |
| 14:08:11 | image_03 | `6466` | `df` |
| 14:11:36 | image_19 | `61`   | `a` |
| 14:13:09 | image_01 | `6365` | `ce` |
| 14:18:44 | image_12 | `7b`   | `{` |
| 14:21:03 | image_08 | `7469` | `ti` |
| 14:24:58 | image_20 | `6d`   | `m` |
| 14:29:12 | image_05 | `696e` | `in` |
| 14:31:47 | image_16 | `67`   | `g` |
| 14:35:20 | image_02 | `2d69` | `-i` |
| 14:39:06 | image_18 | `73`   | `s` |
| 14:42:55 | image_09 | `2d65` | `-e` |
| 14:46:13 | image_13 | `76`   | `v` |
| 14:51:38 | image_04 | `6572` | `er` |
| 14:55:04 | image_15 | `79`   | `y` |
| 14:59:27 | image_10 | `7468` | `th` |
| 15:03:10 | image_06 | `69`   | `i` |
| 15:07:42 | image_17 | `6e67` | `ng` |
| 15:12:29 | image_11 | `7d`   | `}` |

Read down the **Decoded** column:

```
de a df a ce { ti m in g -i s -e v er y th i ng }
```

```
deadface{timing-is-everything}
```

The puzzle is self-documenting: the message was hidden in EXIF, and it could
only be recovered by **ordering the images by time**.

---

## 5. Solve script (Pillow)

```python
import glob, os
from PIL import Image
from PIL.ExifTags import IFD

fragments = []
for path in glob.glob(r"E:\Deadface\efixletration\*.jpg"):
    exif = Image.open(path).getexif().get_ifd(IFD.Exif)
    timestamp = exif[36867]                                  # DateTimeOriginal
    unique_id  = exif[42016].split("_")[1]                   # ImageUniqueID
    fragments.append((timestamp, bytes.fromhex(unique_id).decode()))

fragments.sort()                                             # time is the key
flag = "".join(text for _, text in fragments)
print(flag)   # deadface{timing-is-everything}
```

Same logic with `exiftool` + shell:

```bash
for f in image_*.jpg; do
  printf "%s %s\n" \
    "$(exiftool -s3 -DateTimeOriginal "$f")" \
    "$(exiftool -s3 -ImageUniqueID "$f" | sed 's/IMG_//' | xxd -r -p)"
done | sort | awk '{printf $2} END {print ""}'
```

---

## 6. Takeaways

- **Metadata is a payload channel.** `ImageUniqueID`, `UserComment`,
  `Artist`, `XPComment`, GPS fields, etc. are all attacker-controlled and
  rarely rendered anywhere.
- **"Sorted" isn't ordered.** A set of artifacts that looks alphabetically
  sorted may have a different canonical order (timestamps, EXIF offsets,
  frame numbers). Try sorting by every field you have.
- **The flag hints at the method.** "timing-is-everything" told us the
  `DateTimeOriginal` tag was the ordering key — always re-read the prompt.
