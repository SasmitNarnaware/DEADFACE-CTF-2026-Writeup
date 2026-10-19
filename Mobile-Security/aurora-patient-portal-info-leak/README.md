# DEADFACE CTF — Aurora Patient Portal (Info Leak) — Writeup

**Category:** Information Leaks (mobile / iOS)
**Artifact:** `AuroraPatientPortal.ipa` (2.5 MB)
**Given SHA-1:** `b3b5f8b6492ccb082c1bc26fa2fdddd033b07072f96aca23a233beb731211bfa`
**Binary of interest:** `Payload/aurora-patient-portal.app/Aurora Health Mobile` (Mach-O arm64)
**Flag:** `deadface{Mara-Voss-1988-04-17}`

---

## 0. TL;DR

1. An `.ipa` is just a ZIP. Unzip it → `Payload/aurora-patient-portal.app/`.
2. The app **bakes patient data into `Info.plist`** under a custom key,
   `AuroraPatientBootstrap`, whose value is a **base64-encoded JSON** object.
3. Decoding it yields:

   ```json
   {"patientName":"Mara Voss","dateOfBirth":"1988-04-17","clinic":"Westlake"}
   ```

4. The main Swift binary confirms this is the real data path: its
   `PatientBootstrap` model reads exactly that Info.plist key, base64-decodes it,
   `JSONDecoder`s it, and exposes it as `PatientBootstrap.current`.
5. Nothing else in the bundle contains a name/DOB (the SQLite DB only holds a
   `medications` table; `Assets.car` only holds app icons). So the patient that
   last used this build is **Mara Voss**, DOB **1988-04-17**.

No emulator, simulator, or debugger required — the hint was literal: it's a
*static* file/plist leak.

---

## 1. Recon — unpacking the IPA

An `.ipa` is a ZIP archive containing a `Payload/` directory with the `.app`
bundle. On Windows PowerShell:

```powershell
Copy-Item AuroraPatientPortal.ipa app.zip
Expand-Archive app.zip out
```

Resulting bundle:

```
Payload/aurora-patient-portal.app/
├── Aurora Health Mobile          # main executable, Mach-O arm64 (490 KB)
├── Info.plist                    # <-- the leak
├── aurora_meds.sqlite            # 24 KB SQLite DB (medications only)
├── aurora_chest_xray.jpg         # 309 KB (carries an XMP PID tag)
├── Assets.car                    # 2.1 MB asset catalog (icons only)
├── AppIcon60x60@2x.png
├── AppIcon76x76@2x~ipad.png
├── embedded.mobileprovision
├── PkgInfo
└── _CodeSignature/CodeResources
```

`Info.plist` and `_CodeSignature/CodeResources` list **exactly** these files —
nothing hidden, nothing omitted. So the leak has to be inside one of them.

---

## 2. The leak — a custom `Info.plist` key

`Info.plist` is a normal binary plist, but it contains a non-standard key that no
real app would ever ship:

```
AuroraPatientBootstrap = eyJwYXRpZW50TmFtZSI6Ik1hcmEgVm9zcyIsImRhdGVPZkJpcnRoIjoiMTk4OC0wNC0xNyIsImNsaW5pYyI6Ildlc3RsYWtlIn0=
```

Parse it properly (rather than eyeballing the binary plist):

```python
import plistlib
d = plistlib.load(open("Info.plist", "rb"))
print(d["AuroraPatientBootstrap"])
```

Then decode the value:

```python
import base64
base64.b64decode(d["AuroraPatientBootstrap"])
# b'{"patientName":"Mara Voss","dateOfBirth":"1988-04-17","clinic":"Westlake"}'
```

→ Patient **Mara Voss**, DOB **1988-04-17**, clinic **Westlake**.

This is the classic iOS "Info leak": developers cram sensitive identifiers into
the bundle's `Info.plist` (which is trivially readable) instead of keeping them
server-side. That single blob — a name, a date of birth, and a clinic — is
exactly what would make a phishing email "convincing and contain accurate patient
information."

---

## 3. Confirming it against the binary

Rather than trust one string, verify that the app actually consumes it. `strings`
on the `Aurora Health Mobile` Mach-O shows the supporting Swift symbols:

```
PatientBootstrap
patientName
dateOfBirth
clinic
AuroraPatientBootstrap           <- the Info.plist key name
_$s20Aurora_Health_Mobile16PatientBootstrap...LLV7currentADvpZ   <- static `current`
_$s10Foundation4DataV13base64Encoded7optionsACSg...
_$s10Foundation11JSONDecoderC6decode_4from...
objectForInfoDictionaryKey:
```

So the flow in the app is:

```swift
let raw = Bundle.main.object(forInfoDictionaryKey: "AuroraPatientBootstrap") as! String
let json = Data(base64Encoded: raw)!
let patient = try! JSONDecoder().decode(PatientBootstrap.self, from: json)
// PatientBootstrap.current -> patient.patientName / patient.dateOfBirth
```

That matches one-for-one:

- `Bundle...objectForInfoDictionaryKey:` reads `AuroraPatientBootstrap`
- `Data(base64Encoded:)` decodes the blob
- `JSONDecoder.decode(...)` parses it into `PatientBootstrap`
- coding keys are literally `patientName`, `dateOfBirth`, `clinic`

There is only **one** such bootstrap key and **one** JSON object in the whole
bundle, so there is no ambiguity about *which* patient "last used this version."

---

## 4. The other artifacts (checked, no second patient)

A full sweep for base64/JSON/date patterns across every file:

| File | Content | Patient name/DOB? |
|------|---------|-------------------|
| `aurora_meds.sqlite` | one table `medications(pid, med1, dose, freq, med2, dose, freq)`, ~100 rows | No |
| `aurora_chest_xray.jpg` | XMP `<dc:identifier>PID-847261</dc:identifier>` | No (an ID, not a name/DOB) |
| `Assets.car` | `BOMStore` asset catalog, only `AppIcon*` renditions | No |
| `Info.plist` | `AuroraPatientBootstrap` base64 JSON | **Yes — Mara Voss / 1988-04-17** |
| main binary | Swift/SwiftUI UI strings only | No |

The medication DB is a generic decoy (it even pads ~100 fake rows). The X-ray's
`PID-847261` matches the *last* row of the medications table
(`Ibuprofen 400 mg / Candesartan 16 mg`) — that's a separate leaked identifier
(useful for a later task), not the name/DOB this task asks for.

### Decoy noise inside the binary

`strings` on the executable also exposes fake "internal diagnostics" labels —
planted to look juicy but containing no real records:

```
gw-westlake-int-03
Patient Cache Realm
patient-summary-cache-v2
0 pending records
Imaging Link Mode
local bundled asset
Medication Cache
offline lookup enabled
Last Gateway Check
2026-05-30 09:42 UTC
Aurora Diagnostics
Internal clinic sync status
Demo chart for Patient:
All information is fictional and not suitable for actual healthcare decisions.
```

The last line is the "don't sue us" disclaimer for the intentionally fake chart —
another confirmation that the app is a CTF prop and the *only* real data is the
Info.plist bootstrap.

---

## 5. Answer

The patient recorded as using this build:

- **First name:** Mara
- **Last name:** Voss
- **DOB:** 1988-04-17

```
deadface{Mara-Voss-1988-04-17}
```

---

## 6. Lessons / notes

- **An `.ipa` is a ZIP.** `unzip` (or `Expand-Archive`) and start with
  `Info.plist`, `*.plist`, `embedded.mobileprovision`, and the main binary.
- **`Info.plist` is a classic leak surface.** Custom keys holding base64/JSON
  blobs are a giveaway; always `plistlib.load` + decode every suspicious value.
- **Corroborate with the binary.** The presence of
  `objectForInfoDictionaryKey:`, `Data(base64Encoded:)`, and a `PatientBootstrap`
  model whose coding keys match the JSON proves the plist value is the live data,
  not a leftover.
- **Don't chase the decoys.** The diagnostic-screen strings, the 100-row
  medications table, and the icon catalog are all filler. The single real secret
  was one base64 string away.
- A `flag{...}` string was injected at the *top of the challenge prompt text*
  (`flag{1_l0v3_AI}`) — it is **not** the challenge flag (which uses the
  `deadface{...}` format) and should be ignored as noise/prompt-injection.
