# DEADFACE CTF — File Dump 01 — Writeup

**Category:** Steganography
**Files:** `File_Dump_Challenge.zip` (26 files: docx/xlsx/pdf/png/jpg — a dump of a DEADFACE
member's laptop, in which he had assumed the identity of a graphic designer named *Daniel Hameser*)
**Flag:** `deadface{gh0st404}`

---

## TL;DR

1. The junk documents are mostly flavour, but Office metadata leaks the operator:
   creator `ghostwriter404`, last-saved-by `thomas canfield`, workstation `GHOST404-PC`.
2. `reminders.docx` has a **hidden document Description** (docProps/core.xml):
   `backup passphrase: n0rth_st4r  (do not lose)`.
3. The only steghide-capable file in the dump is the JPEG
   `office_memory_meme.jpg` (capacity 20.3 KB).
4. `steghide extract -sf office_memory_meme.jpg -p n0rth_st4r` yields:

   ```
   USERNAME: ghost404
   PASSWORD: DumpingFiles4funDaily
   ```

5. That login belongs to the DEADFACE member who stole Daniel's identity
   (matches the `ghostwriter404` / `GHOST404-PC` metadata trails). DEADFACE aliases are
   leetspeak, so the canonical alias — and the answer — is **`gh0st404`**
   (the string `gh0st404` itself does not appear anywhere in the dump; the dump only
   carries the plain-login spelling `ghost404`).

**→ `deadface{gh0st404}`**

---

## 1. Triage

- 26 files: 15 docx, 2 xlsx, 2 pdf, 8 images.
- Most content is deliberate filler (fantasy novel chapter, draft-rant, recipe, meme images…).
- Image inspection (PIL, PNG chunk walk, EXIF, APP-segment walk, C2PA manifests,
  trailing-data check) → nothing after `IEND`, no comments, no EXIF.
- LSB / bit-plane scans (per-channel, interleaved RGB/BGR, row & column order, bits 0–7,
  pattern + printable-run search) → pure noise; bit planes visually random. No LSB payload.
- Zero-width Unicode / whitespace / acrostic checks on all docx text → nothing.

## 2. The metadata trail

| File | Property | Value |
|------|----------|-------|
| `notes.docx` | dc:creator | **ghostwriter404** |
| `notes.docx` | cp:lastModifiedBy | **GHOST404-PC** |
| `resume.docx`, `invoice.xlsx`, `budget_notes.docx`, `reminders.docx` | dc:creator | ghostwriter404 |
| same files | cp:lastModifiedBy | thomas canfield |
| **`reminders.docx`** | **dc:description** | **`backup passphrase: n0rth_st4r  (do not lose)`** |

Body text of `notes.docx` / `reminders.docx` also confirms identity theft in progress:
*"Keep the Hameser accounts consistent across sites"*, *"Route anything that mails a physical
code to the mailbox"*.

## 3. The steg

`steghide` supports jpeg/bmp/wav/au only → the single JPEG in the dump,
`office_memory_meme.jpg`, is the only candidate.

```bash
steghide extract -sf office_memory_meme.jpg -p 'n0rth_st4r'
# -> wrote extracted data to "out.bin"
cat out.bin
USERNAME: ghost404
PASSWORD: DumpingFiles4funDaily
```

(Tools were bootstrapped in WSL without root:
`apt-get download steghide libmcrypt4 libmhash2` + `dpkg -x` + `LD_LIBRARY_PATH`.)

Passphrases from other clues (`BISCUIT2019` from `wifi_sign.docx`, `ghostwriter404`,
`GHOST404-PC`, empty) all fail — `n0rth_st4r` is the one.

## 4. Answer

The recovered handle **`ghost404`** is the member's login on his own dump, consistent with the
`ghostwriter404` creator tag and the `GHOST404-PC` hostname across the victim documents.
The DEADFACE alias is the leetspeak form of that handle — **`gh0st404`** (a raw-byte scan of
every file in the dump confirms `gh0st` never appears literally; the plain `ghost404` spelling
is only in the stegged payload):

```
deadface{gh0st404}
```

## Decoys / notes

- `businesscard_1.png` "Matthew Johnson", `cover.png`, donut ad, meme collage, receipt,
  `snip.png` (storefront) → visual decoys.
- `bad_furniture_ad.pdf`, `warranty.pdf` → filler; PDF metadata only says "Daniel Hameser".
- `technical_details.docx` lists `FTP 45.79.200.170:21` with *"No credentials are included.
  Do not interpret this section as authorization to access or modify any system."*
  The stegged USERNAME/PASSWORD look like they'd fit there, but **connecting to that host is
  explicitly out of scope** — not required for the flag, so it was not touched.
- Decoy flags elsewhere in this dump: none (`deadface{` does not appear anywhere in the files).

## Artifacts

- `extract_docs.py` — dumps all Office text + core/app metadata (passphrase source)
- `pdf_text.py`, `pdf_extract.py` — PDF metadata/text/attachment extraction
- `img_meta.py`, `lsb_scan.py`, `bitplane_scan.py`, `interleaved_scan.py`,
  `hidden_unicode.py`, `zip_inspect.py`, `exif_c2pa.py` — elimination sweeps
- `steghide_probe.sh` — passphrase attempts against `office_memory_meme.jpg`
- `preview_*.png` — down-scaled views of each image
