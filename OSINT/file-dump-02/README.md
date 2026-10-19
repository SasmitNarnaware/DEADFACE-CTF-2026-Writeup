# Deadface 2026 — "File Dump 02"

**Category:** OSINT
**Author:** @RP-01
**Points:** 75
**Artifacts:** the same dump as *File Dump 01* (`File_Dump_Challenge.zip`, 26 files — a DEADFACE member's laptop containing documents stolen from / impersonating the graphic designer **Daniel Hameser**)
**Flag:** `deadface{alaska_macstore}`

> *"Now we know who is responsible for impersonating Daniel. Can you dig through
> these documents and maybe find a where? We are pretty sure Daniel had a computer
> stolen so where could that have happened?"*
>
> Submit the flag as `deadface{store_name}`. Example: `deadface{texas_tires}`.

---

## TL;DR

1. File Dump 01 told us **who** (`gh0st404` / `ghostwriter404`). This challenge wants
   **where**.
2. The dump contains a storefront photo (`snip.png`) and a computer-service receipt
   (`reciept_1.png`). Both point at the same business:
   - `snip.png` → a window with **`17`**, an Apple logo, and the words **"Apple Specialist"**.
   - `reciept_1.png` → header **`Store  17`**, line item *"Computer Services — Diagnostic,
     system cleanup, malware removal, system optimization, and updates"*, **$250.00**,
     dated 08/14/2026.
3. Every retail/business clue in the dump is in **Anchorage, Alaska**, on the **E Tudor Rd** strip:
   - `advertising_ad_1.png` → **Golden Donuts**, 2213 E Tudor Rd, Anchorage (a real shop).
   - `snip.png` / receipt → the Apple reseller at **2217 E Tudor Rd, Suite #17**.
4. That address is **Alaska MacStore**, an *Apple Authorized Service Provider*.
   Suite **17** = the `17` in the window = `Store 17` on the receipt.
5. So the place Daniel's machine was last in someone else's hands (and could have been
   stolen) is **Alaska MacStore**.

**→ `deadface{alaska_macstore}`**

---

## 1. What the previous dump already gave us

*File Dump 01* established:

- The dump is from a DEADFACE operator's machine: Office metadata repeatedly shows
  creator `ghostwriter404` and last-saved-by `GHOST404-PC` / `thomas canfield`.
- The member was systematically taking over **Daniel Hameser's** identity
  ("keep the Hameser accounts consistent across sites", "route anything that mails a
  physical code to the mailbox").
- The stegged payload in `office_memory_meme.jpg` recovered `USERNAME: ghost404`.

That answers **who**. This challenge is the geographic follow-up: **where did Daniel's
computer go / get taken?**

## 2. The two "location" artifacts

### `snip.png` — the storefront

A cropped photo of a shop window. Reading left to right:

| Pane | Content |
|------|---------|
| 1 | Neon `OPEN` sign |
| 2 | **`17`** |
| 3 | Apple logo decal |
| 4 | **`Apple Specialist`** |

So: a numbered (17) location that sells/services Apple gear and displays the
*Apple Specialist* reseller wording.

*Technical note:* `snip.png` is the odd one out in the image set — it is `RGBA`,
`1667×244`, with real PNG ancillary chunks (`sRGB`, `gAMA`, `pHYs` ≈ 96 dpi). Every
other photo in the dump is an AI-generated RGB image carrying a C2PA manifest.
`snip.png` is a genuine screenshot/photo crop — the planted OSINT clue.

### `reciept_1.png` — the receipt

A crumpled, coffee-stained receipt:

```
Store
17 ...................................................

Receipt #: 008742
Date: 08/14/2026   Time: 12:15 PM

Item / Description                         Amount
Computer Services                          $250.00
  Diagnostic, system cleanup,
  malware removal, system
  optimization, and updates

Total                                      $250.00
Payment Method
Card (**** 4242)                           $250.00
```

Two things matter here:

1. The **`Store 17`** header (matches the `17` in the shop window).
2. The service is **computer repair / malware removal** — i.e. Daniel physically
   handed his machine to this shop.

## 3. Pinning the location (OSINT)

The dump is full of flavour documents, but the *real, checkable* businesses are all
in one place.

### Golden Donuts → Anchorage, AK

`advertising_ad_1.png` is an ad for **Golden Donuts** ("Thank you for supporting
local!"). That is a real shop:

> Golden Donuts — 2213 E Tudor Rd #52, Anchorage, AK 99507

### The Apple reseller → Alaska MacStore, Suite 17

The shop at **2217 E Tudor Rd, Suite #17, Anchorage** is **Alaska MacStore**, and it is
described everywhere as an Apple service provider:

| Source | Snippet |
|--------|---------|
| MapQuest | *"2217 E Tudor Rd, #17, Anchorage … an Apple Authorized Service Provider that offers repair services"* |
| BBB | *"The Alaska Mac Store — 2217 E Tudor Rd Ste 17, Anchorage, AK 99507 … Computer Repair"* |
| Yelp | *"ALASKA MACSTORE, 2217 E Tudor Rd, Ste 17, Anchorage, AK 99507"* |
| akmacstore.com | *"VISIT 2217 E. TUDOR RD. STE. 17"* / *"As an Apple Authorized service provider, we fix devices…"* / footer `© ALASKA MACSTORE` |

The chain is airtight:

- `17` in the shop window → **Suite 17** at 2217 E Tudor Rd
- `Store 17` on the repair receipt → the same business
- "Apple Specialist" + "computer services" → the Apple service provider at that address
- Same street as the Golden Donuts ad → same neighbourhood, confirming the locale

Daniel left his computer at **Alaska MacStore** for service — which is exactly where it
could have gone missing.

## 4. Answer

```
deadface{alaska_macstore}
```

Format matches the `deadface{store_name}` hint (lower-case, underscores), and the
store's own branding is **"ALASKA MACSTORE"**.

---

## Decoys / notes

- `businesscard_1.png` — **Alpine Mechanical, Inc.**, "Matthew Johnson", (907) 344-9011.
  Looks like a lead but doesn't resolve to a real Anchorage business; it's a red herring
  (or simply more Anchorage-area colour).
- `bad_furniture_ad.pdf` — "Oops! Furniture Emporium", *"UP TO 17% OFF"*, explicitly says
  *"No real address. No real phone."* The `17` here is a deliberate decoy/echo — don't
  chase it.
- `warranty.pdf` — "NorthPeak" microwave warranty for Daniel Hameser; fictional retailer,
  no location.
- `invoice.xlsx` — Bill To "Mary Sue, 1243 Pretend Street, Florence, NM"; fake address,
  not the answer.
- `notes.docx` — *"Use the FL address for anything that mails a code."* / `budget_notes.docx`
  *"Renew car registration at the FL DMV."* These point at a **Florida** address used as a
  mail drop for the identity theft — not where the computer was stolen.
- The receipt's `Card (**** 4242)` and the `technical_details.docx` FTP endpoint
  (`45.79.200.170:21`) are flavour; the FTP host is explicitly out of scope.

## Artifacts (helper scripts left in the folder)

- `dump_all.py` / `_dump_all.txt` — full text + metadata dump of every docx/xlsx.
- `crop_receipt.py` / `_receipt_header.png` / `_receipt_store.png` — zooms on the receipt
  header showing `Store 17`.
- `crop_snip.py` / `_snip_white.png` — alpha-flattened, enlarged storefront crop showing
  `17` + Apple logo + `Apple Specialist`.
- `img_meta.py`, `exif_c2pa.py`, `pdf_text.py`, `pdf_extract.py` — metadata sweeps used to
  rule out EXIF/GPS and confirm the documents are the only leads.
