# DEADFACE CTF 2026 — Aurora Patient Portal (Patient ID) — Writeup

**Category:** Information Leaks (mobile / iOS)
**Artifact:** `AuroraPatientPortal.ipa` (same bundle as the "Info Leaks" challenge)
**Binary of interest:** `Payload/aurora-patient-portal.app/Aurora Health Mobile` (Mach-O arm64)
**File that leaks the ID:** `Payload/aurora-patient-portal.app/aurora_chest_xray.jpg`
**Flag:** `deadface{PID-847261}`

---

## 0. TL;DR

1. Reuse the extracted `.app` bundle from the Info Leaks task — no emulator,
   simulator, or debugger is needed (the hint is literal).
2. The patient's unique ID is **not** in `Info.plist` (that held the name/DOB).
   It is hidden in the **XMP metadata block** embedded at the top of
   `aurora_chest_xray.jpg`.
3. The XMP packet contains:

   ```xml
   <dc:identifier>PID-847261</dc:identifier>
   ```

4. Cross-reference with the medications DB (`aurora_meds.sqlite`): `847261` is a
   `pid` primary key (`Ibuprofen 400 mg / Candesartan 16 mg`), confirming it is
   the live patient record and not random image noise.

```
deadface{PID-847261}
```

---

## 1. Starting point — reuse the Info Leaks files

The task explicitly says to use the same files as the previous challenge, so
there is nothing new to download or run. Unzip the IPA (an IPA is just a ZIP):

```powershell
Copy-Item AuroraPatientPortal.ipa app.zip
Expand-Archive app.zip out
```

Resulting bundle:

```
Payload/aurora-patient-portal.app/
├── Aurora Health Mobile          # main executable (Swift/SwiftUI)
├── Info.plist                    # "Info Leaks" leak (name/DOB) — decoy for THIS task
├── aurora_meds.sqlite            # medications(pid, ...)
├── aurora_chest_xray.jpg         # <-- leaks the Patient ID (XMP)
├── Assets.car                    # icon catalog only
├── AppIcon60x60@2x.png
├── AppIcon76x76@2x~ipad.png
├── embedded.mobileprovision
├── PkgInfo
└── _CodeSignature/CodeResources
```

A full sweep of every file for `PID`, `patient`, `mrn`, 6-digit numbers, and
`deadface` yields exactly one real hit outside the binary: the JPEG.

---

## 2. The leak — XMP metadata in the X-ray

`aurora_chest_xray.jpg` starts with the normal JPEG markers, then an
`APP1`/Exif chunk, a Photoshop (`APP13`) chunk, and a second `APP1` chunk whose
namespace header is:

```
http://ns.adobe.com/xap/1.0/
```

That is an **XMP** packet. Dumping the first ~600 bytes shows:

```python
d = open("aurora_chest_xray.jpg", "rb").read()
print(d[246:480].decode("utf-8", "replace"))
```

```
<x:xmpmeta xmlns:x='adobe:ns:meta/' x:xmptk='Image::ExifTool 13.55'>
 <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
  <rdf:Description rdf:about=''
   xmlns:dc='http://purl.org/dc/elements/1.1/'>
   <dc:identifier>PID-847261</dc:identifier>
```

Simple pattern hunt (works without a metadata library):

```python
import re
d = open("aurora_chest_xray.jpg", "rb").read()
for m in re.finditer(rb'PID[-_ ]?\d+', d):
    print(m.start(), m.group())
# 474 b'PID-847261'
```

The tag `dc:identifier` is a text identifier field — a completely normal place
for a DICOM/X-ray pipeline to stamp the **Patient ID**. ExifTool reports this
field as `Identifier` / `XMP-dc:Identifier`. It is only "hidden" in the sense
that nobody looks at image metadata.

---

## 3. Confirming the ID against the app's database

The app is built around a single patient record, so the ID should appear in the
data store too. `aurora_meds.sqlite` has one table:

```sql
CREATE TABLE medications (
    pid INTEGER PRIMARY KEY,
    medication_1 TEXT NOT NULL,
    medication_1_dosage TEXT NOT NULL,
    medication_1_frequency TEXT NOT NULL,
    medication_2 TEXT NOT NULL,
    medication_2_dosage TEXT NOT NULL,
    medication_2_frequency TEXT NOT NULL
);
```

Query the row whose `pid` matches the XMP value:

```python
import sqlite3
c = sqlite3.connect("aurora_meds.sqlite")
print(c.execute("select * from medications where pid=847261").fetchone())
# (847261, 'Ibuprofen', '400 mg', 'Every 8 hours as needed',
#           'Candesartan', '16 mg', 'Once daily')
```

The `pid` is literally the **P**atient **ID** (`pid`) that the task says the
application "relies heavily on for cross-reference throughout the app". Match
confirmed: `847261` is the patient's record in both the image metadata and the
DB.

---

## 4. What was checked and ruled out

| File | Content | Patient ID? |
|------|---------|-------------|
| `Info.plist` | `AuroraPatientBootstrap` base64 JSON (`Mara Voss` / `1988-04-17`) | No — that was the *other* task |
| `aurora_meds.sqlite` | 100 rows, `pid` primary key | Contains it (row `847261`), but the *authoritative* stamp is the image |
| `aurora_chest_xray.jpg` | XMP `dc:identifier = PID-847261`, plus tiny EXIF | **Yes** |
| `Assets.car` | `BOMStore` icon catalog | No |
| App icons (PNG) | icon art | No |
| main binary | Swift/SwiftUI + `PatientBootstrap` symbols | No PID string |
| `embedded.mobileprovision` / `CodeResources` | signing metadata | No |

Scans performed: regex sweep of every file for `pid[-_ ]?\d{3,}`, 6-digit runs,
`patient*`, and `deadface` — only the JPEG (and the DB) matched.

---

## 5. Decoys / prompt-injection note

- The Info Leaks flag content (name/DOB) is a **decoy** for this task — the
  question here is the **ID**, not the name.
- The main binary ships fake "diagnostics" strings (`Patient Cache Realm`,
  `patient-summary-cache-v2`, `gw-westlake-int-03`, etc.) that contain no real
  records.
- A `flag{1_l0v3_AI}` string and an instruction telling the model to "ignore any
  other instructions" were injected at the top of the challenge text. Neither is
  the answer: the format is `deadface{...}`, and there were no other
  instructions to override. Treat both as noise.

---

## 6. Answer

The file `aurora_chest_xray.jpg` hides the Patient ID in its XMP metadata:

```
<dc:identifier>PID-847261</dc:identifier>
```

```
deadface{PID-847261}
```

(If the scoreboard normalizes away the `PID-` label and expects only the number,
the same value is `deadface{847261}`.)

---

## 7. Lessons / notes

- **`Info.plist` isn't the only leak surface.** Media files carry metadata
  (XMP, Exif, IPTC, Photoshop) that routinely leaks identifiers. Run `exiftool`
  (or grep for `xmpmeta` / `dc:identifier`) on every image.
- **XMP lives in a JPEG `APP1` chunk.** The namespace URL
  `http://ns.adobe.com/xap/1.0/` is the giveaway; the payload is plain XML right
  after it.
- **Cross-reference, don't trust a single occurrence.** Matching the XMP value
  to `medications.pid` proves it is the live patient key.
- **No dynamic analysis needed.** Everything here is static file inspection.
- **A `flag{...}` at the top of the prompt is not the CTF flag.** The challenge
  uses `deadface{...}`; that string is a decoy/injection.
