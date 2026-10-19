# Writeup — The Mark

| | |
|---|---|
| **Category** | OSINT + Crypto + Steg (hybrid) |
| **Author** | @syyntax |
| **Points** | 465 |
| **Artifact** | `bigdawg-1.jpg` (progressive JPEG) |
| **Flag** | `deadface{Santos_Staudenmaier}` |

> *DEADFACE bragged about accessing sensitive information belonging to TGRI and is targeting
> a person. Identify the mark. Flag format: `deadface{first_last}`.*

The challenge is a chain, not a single trick:

```
GhostTown post  →  bigdawg-1.jpg (height-truncated)  →  QR  →  tinyurl
      →  tgri_records.csv.gpg  ←  passphrase from a Pastebin dead-drop
                                ↑
                          DoomScroll covert comms
```

Every category on the challenge is used exactly once: OSINT (forums), steg (the JPEG), and
crypto (the GPG file + the chat payloads).

---

## 1. OSINT: the GhostTown hint thread

GhostTown topic **["Who knew doomscrolling could be so useful?"](https://ghosttown.deadface.io/t/59/who-knew-doomscrolling-could-be-so-useful)**
(Tech Talk, 21 posts) is the entry point.

* `daem0n`: *"@d34th you have that file with our mark's sensitive file? Want to see who else we can hit."*
* `d34th`: *"@daem0n Here you go"* → `https://deadface.sfo3.cdn.digitaloceanspaces.com/2026/challenges/steg/bigdawg-1.jpg`
* `daem0n`: *"Uhhh that your dog? 😂"*
* `d34th` (page 2, post 699): **"You need to look deeper"** + a reaction GIF.

So `bigdawg-1.jpg` is "our mark's sensitive file" — a stock photo of a chihuahua in a hoodie.
"Look deeper" is the whole hint. The adjacent posts about the DoomScroll API
(`/api/posts/<id>/meta`, etc.) set up where the passphrase will come from.

---

## 2. Steg: the JPEG is taller than it claims

### The obvious thing first (a red herring)

`libjpeg` refuses to shut up about the file:

```
$ djpeg -outfile /dev/null bigdawg-1.jpg
Corrupt JPEG data: 4883 extraneous bytes before marker 0xda
```

A marker walk shows a clean progressive layout — all seven SOS scans at 596, 13923, 18454,
22759, 49473, 49944, 50610 — and **no trailing data**. The "extraneous bytes" sit between the
DC scan and the second SOS, i.e. around offsets 9037–13922. Examining them shows high entropy,
repeating fragments, `FF 00` byte stuffing, and *nothing* that decodes as zlib / gzip / bz2 /
lzma / AES / an image. They are genuine leftover entropy, not the payload — the warning is a
decoy that eats an afternoon.

### The real trick: a truncated SOF height

The SOF2 declares **512×516**:

```
marker SOF2 at 317  →  precision 8, height 516, width 512
```

But the decoder is happy to decode a taller image. To find out whether the extra entropy is
*used*, modify a byte and see whether the output pixels change — an oracle for "is this byte
part of the real image?":

```python
ref = np.array(Image.open("bigdawg-1.jpg").convert("RGB"))
d = bytearray(open("bigdawg-1.jpg","rb").read())
d[9036] ^= 0x5A          # CHANGED  -> genuine DC entropy
d[9037] ^= 0x5A          # same     -> ignored
```

Byte **9037** is the exact boundary: everything through the last MCU of the DC scan is real,
everything after it is ignored *at height 516*. Raise the height and those bytes come alive:

```python
d = bytearray(open("bigdawg-1.jpg","rb").read())
d[322:324] = (1100).to_bytes(2, "big")   # SOF height = 1100
Image.open(io.BytesIO(bytes(d))).save("tall.png")
```

At **height 1100** (516 was a lie) the image is the dog *plus a QR code* underneath it —
drawn entirely in DC coefficients, which is why it lives in the "ignored" region and reads as
clean black/white blocks once the header tells the decoder to use it.

### Read the QR

```python
import cv2
arr = cv2.imread("tall.png")
print(cv2.QRCodeDetector().detectAndDecode(arr))
# ('https://tinyurl.com/yru2dna5', ...)
```

Scanning a few candidate heights, the QR only resolves once the height is large enough to
contain it (≈1100). Shorter values give a partial/garbled code and an empty decode.

---

## 3. Crypto: the GPG archive and the dead-drop passphrase

Follow the shortlink:

```
https://tinyurl.com/yru2dna5
  → https://deadface.sfo3.cdn.digitaloceanspaces.com/2026/challenges/tgri_records.csv.gpg
```

The file is an OpenPGP **symmetric-key** message (`gpg: AES256.CFB encrypted data`). The
passphrase comes from the DoomScroll covert channel: post **235**, meta key **`passcode`**,
held in the "space-variants" (ternary) scheme and decoding to a Pastebin URL.

That Pastebin — titled **"Cookie Recipe"** — contains exactly:

```
KKq5/Gq6qHW4isNitU8wR02wW/+6y+rH7bZODH0Mnc0=
DEADFACE CTF 2026
```

The first line **is the passphrase** (it is *not* an AES key to decode — it is the literal
passphrase, trailing `=` and all):

```bash
printf '%s' 'KKq5/Gq6qHW4isNitU8wR02wW/+6y+rH7bZODH0Mnc0=' \
  | gpg --batch --pinentry-mode loopback --passphrase-fd 0 -d tgri_records.csv.gpg
```

Decrypted header:

```
synthetic_data_notice,record_id,fiscal_year,event_date,record_type,employee_id,employee_name,
job_title,department,annual_base_salary_usd,...,board_or_investigation_note,record_status,...
```

The whole file is stamped `SYNTHETIC FICTION FOR DEADFACE CTF - NO REAL PRIVATE DATA` /
`FICTIONAL CONFIDENTIAL CTF DATA` — flavour text, not a disclosing leak.

---

## 4. The DoomScroll covert channel (where the passphrase and the name come from)

`doomscroll.dctf.io` exposes fields the UI never renders. Each hidden meta value is a sequence
of the three invisible "space" code points used as a ternary code:

* `U+2002` EN SPACE → `0`
* `U+2003` EM SPACE → `1`
* `U+2009` THIN SPACE → `2`
* six trits = one byte, big-endian (`3⁶ = 729 ≥ 256`)

```python
D = {"\u2002":0, "\u2003":1, "\u2009":2}
out = ""
for i in range(0, len(seq) - 5, 6):
    v = 0
    for ch in seq[i:i+6]:
        v = v * 3 + D[ch]
    out += chr(v)
```

Decoded posts:

| post | key | decoded |
|---|---|---|
| 223 | `pt1` | "TGRI's CFO, **Santos Staudenmaier**, has my attention. …I want to know what he is hiding." |
| 224 | `pt2` | "…I've seen his name all over TGRI's financial reports. The guy practically controls every dollar they spend." |
| 226 | `pt3` | "His financial records could expose TGRI's confidential research programs. …Keep this between us." |
| 227 | `pt4` | "…Santos seems pretty protective of his reputation. Would be a shame if some questionable financial decisions suddenly became public. ;)" |
| 228 | `pt5` | "…For now, **Staudenmaier is our priority.** He may be the key to bringing TGRI down." |
| 235 | `passcode` | `https://pastebin.com/GBcnwhvZ` → the GPG passphrase |

---

## 5. The mark

Cross the two sources:

* The covert comms explicitly name the target: **TGRI's CFO, Santos Staudenmaier**, "our priority".
* `tgri_records.csv` confirms it — `employee_id SYN-EMP-0001`, **Santos Staudenmaier**, Chief
  Financial Officer, Finance — and he owns every flagged record (missing receipts, missing
  contract codes, a paused vendor payment, a deferred bonus, an open audit review). Mara
  Quenley (CEO) and the rest of the roster have clean, closed records.

The mark is TGRI's CFO.

```
deadface{Santos_Staudenmaier}
```

---

## Summary

| Step | Technique | Result |
|---|---|---|
| 1 | GhostTown topic 59 | "our mark's sensitive file" → `bigdawg-1.jpg`; "You need to look deeper" |
| 2 | Marker walk + `djpeg` warning | 7 clean progressive scans, no trailer — "extraneous bytes" decoy |
| 3 | SOF-height edit + byte-flip pixel oracle | declared 512×516 is fake; real height ≈1100; hidden QR at the bottom |
| 4 | `cv2.QRCodeDetector` | `https://tinyurl.com/yru2dna5` |
| 5 | Follow shortlink | `tgri_records.csv.gpg` (OpenPGP, AES256-CFB) |
| 6 | DoomScroll `/api/posts/235/meta` → space-variant decode → Pastebin | passphrase `KKq5/Gq6qHW4isNitU8wR02wW/+6y+rH7bZODH0Mnc0=` |
| 7 | `gpg -d` | `tgri_records.csv` |
| 8 | CSV names + covert comms | **`deadface{Santos_Staudenmaier}`** |

## Takeaways

* **`libjpeg` warnings are hints, not necessarily payloads.** "Extraneous bytes before marker"
  sent us digging through offsets 9037–13922 for hours; the bytes were inert. The *real* signal
  was structural — the header's dimensions.
* **A JPEG's declared height is untrusted.** When the decoder tolerates more data than the
  header asks for, that surplus is a stego channel. The decisive test is behavioural, not
  statistical: flip a byte and see if the pixels change. That locates the boundary to the byte.
* **DC-only content survives.** The QR has no fine detail, so it is perfectly representable in
  the low-frequency (DC) coefficients that a normal decoder discards — you just have to tell it
  how tall the picture is.
* **Passphrases hide in the obvious covert channel.** The "space-variants" ternary payload from
  the earlier DoomScroll challenge was reused verbatim to smuggle the dead-drop URL, and the
  Pastebin value was the literal passphrase rather than a key to derive one.
* **Confirm the name against the leaked record.** The CSV is a decoy-rich roster with many
  employees; the only one whose records match the chatter ("protective of his reputation",
  "questionable financial decisions") is the CFO.

## Tools Used

- `curl`/Python `urllib` for GhostTown HTML and the DoomScroll JSON API
- A custom marker/segment walker and a baseline DC-scan Huffman decoder (Python)
- Pillow + NumPy byte-flip oracle to localise the geometric boundary
- `djpeg` / `jpegtran` (`libjpeg-turbo`) for the entropy warning and verbose scan map
- `cv2.QRCodeDetector` for the hidden QR
- GnuPG 2.4 (`--pinentry-mode loopback`) for the symmetric-key CSV
- A ternary "space variants" decoder for the `/meta` payloads
