# DEADFACE CTF 2026 — Aurora Patient Portal (Gateway Server) — Writeup

**Category:** Information Leaks (mobile / iOS)
**Artifact:** `AuroraPatientPortal.ipa` (same bundle as the "Info Leaks" / "Patient ID" tasks)
**Binary of interest:** `Payload/aurora-patient-portal.app/Aurora Health Mobile` (Mach-O arm64)
**Hidden UI:** `DiagnosticScreen` (SwiftUI sheet, unlocked by a long-press on the header)
**Flag:** `deadface{gw-westlake-int-03}`

---

## 0. TL;DR

1. The app has a **hidden diagnostic page** — `DiagnosticScreen` — that is not on
   the normal navigation path. It is presented by a
   `onLongPressGesture` attached to the header of `ContentView`
   (SwiftUI state `_isShowingDiagnosticScreen` toggles the sheet).
2. The page's contents come from a static table,
   `DiagnosticInfo.items: [DiagnosticItem]`, built in the Mach-O in the
   function `_$s20Aurora_Health_Mobile14DiagnosticInfo…V5items_WZ`
   (`__text` @ `0x100009a68`).
3. Decoding that initializer gives seven `(title, value)` rows, including:

   ```
   Clinic Route     = westlake
   Sync Gateway     = gw-westlake-int-03        <-- the gateway server
   Patient Cache Realm = patient-summary-cache-v2
   Sync Queue       = 0 pending records
   Imaging Link Mode = local bundled asset
   Medication Cache = offline lookup enabled
   Last Gateway Check = 2026-05-30 09:42 UTC
   ```

4. The gateway segment `westlake` matches the clinic stored in
   `Info.plist` (`AuroraPatientBootstrap` → `"clinic":"Westlake"`), and
   `PID-847261` confirms the record — i.e. all previously collected data
   corroborates the row.

```
deadface{gw-westlake-int-03}
```

---

## 1. Finding the hidden diagnostic page statically

The main executable is a Swift/SwiftUI binary. `strings` (or the Swift symbol
table) shows the diagnostic UI types the normal screens never reference directly:

```
DiagnosticScreen
DiagnosticRow
DiagnosticItem
DiagnosticInfo
_isShowingDiagnosticScreen
```

The Swift mangled symbol for the table builder is:

```
_$s20Aurora_Health_Mobile14DiagnosticInfo33_D6AD29105337815F110C54CD57D07155LLV5items_WZ
```

`_WZ` is the one-time "was zeroed" static initializer for the property
`DiagnosticInfo.items`. It runs the first time the diagnostic screen is opened.

Pulling the plain strings in the same region already leaks the values:

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
```

The title/value pairing is ambiguous from a raw string dump (is
`gw-westlake-int-03` a title or a value?), so decode the initializer to be sure.

---

## 2. Decoding `DiagnosticInfo.items` (arm64)

Parse the Mach-O sections to map VM addresses ↔ file offsets, then disassemble
the initializer with Capstone (`CS_ARCH_AARCH64`).

Each `DiagnosticItem` is two `String` fields. The compiler materializes them
either as Swift **small-string literals** (chars packed inline into the 16-byte
`String`, with a count nibble in the top byte, `top = 0xE0 | len`) or as
**pointer literals** (`word0 = 0xD0… | len`, `word1 = addr | 0x8000…`).

Relevant slice of the disassembly:

```asm
0x100009a68  ...                                ; DiagnosticInfo.items builder
0x100009af8  ...  stp x9, x10, [x8]             ; "Clinic R" + "oute"+0xEC   -> "Clinic Route"
0x100009b18  ...  stp x9, x10, [x8]             ; "westlake" + 0xE8          -> "westlake"
0x100009b3c  adrp x8, 0x100019000
0x100009b40  add  x8, x8, #0x30                 ; -> 0x100019030 ("gw-westlake-int-03")
0x100009b48  orr  x26, x8, #0x8000000000000000  ; pointer literal
0x100009b54  ...  stp x9, x10, [x8]             ; "Sync Gat" + "eway"+0xEC  -> "Sync Gateway"
0x100009b7c  ...
0x100009b88  mov  x24, #0x11
0x100009b8c  movk x24, #0xd000, lsl #48         ; 0xD000000000000011 (len 0x11 = 17)
0x100009b90  stp  x25, x26, [x8]                ; x25 = len 0x12 (=18), x26 = gw literal
0x100009b9c  ...                                ; "Patient Cache Realm"
0x100009bac  ...                                ; "patient-summary-cache-v2"
...
0x100009cd4  ...                                ; "Last Gateway Check"
0x100009ce4  ...                                ; "2026-05-30 09:42 UTC"
```

The `stp x25, x26, [x8]` write for the gateway row is the giveaway:
`x25 = 0xD000000000000012` encodes a **length of 0x12 = 18** characters, and
`x26` is the pointer to `0x100019030`. `"gw-westlake-int-03"` is exactly 18
characters long — so the row is literally *"Sync Gateway" = "gw-westlake-int-03"*.

The full decoded table:

| Title | Value |
|-------|-------|
| Clinic Route | `westlake` |
| **Sync Gateway** | **`gw-westlake-int-03`** |
| Patient Cache Realm | `patient-summary-cache-v2` |
| Sync Queue | `0 pending records` |
| Imaging Link Mode | `local bundled asset` |
| Medication Cache | `offline lookup enabled` |
| Last Gateway Check | `2026-05-30 09:42 UTC` |

---

## 3. Cross-checking with the data collected earlier

The question says to use *all* the data collected so far. It lines up:

- **Clinic** — `Info.plist` `AuroraPatientBootstrap`
  (base64 JSON) → `"clinic":"Westlake"`. The gateway is cluster-scoped:
  `gw-` + `<clinic lowercased>` + `-int-<NN>` = `gw-westlake-int-03`.
- **Patient** — `aurora_chest_xray.jpg` XMP → `PID-847261`, matching row
  `847261` in `aurora_meds.sqlite` (Ibuprofen 400 mg / Candesartan 16 mg).
- **Patient cache** — `patient-summary-cache-v2` is the on-device cache name for
  the same patient record the app bootstraps from `Info.plist`.

So the diagnostic page is the app's built-in "internal clinic sync status"
readout, and the network-monitoring target is the gateway host:

```
Sync Gateway = gw-westlake-int-03
```

---

## 4. If you want to see it live (dynamic)

Not required — this is fully static — but for completeness the page opens by
**long-pressing the header** of the main `ContentView`. In SwiftUI this is:

```swift
.onLongPressGesture { isShowingDiagnosticScreen = true }
...
.sheet(isPresented: $isShowingDiagnosticScreen) { DiagnosticScreen() }
```

`DiagnosticScreen` renders `ForEach(DiagnosticInfo.items)` with a
`DiagnosticRow(title:value:)` for each entry.

---

## 5. Answer

The gateway server the app talks back to:

```
deadface{gw-westlake-int-03}
```

---

## 6. Lessons / notes

- **Hidden screens hide in symbols, not just strings.** Swift keeps the type and
  property names (`DiagnosticScreen`, `DiagnosticInfo.items`); finding the
  initializer symbol lets you recover exactly what the screen would render.
- **Decode Swift string literals.** Small strings pack chars inline with the
  count in the top byte (`0xE0 | len`); pointer literals use
  `word0 = 0xD0… | len`. The length word is a handy sanity check when mapping a
  literal to its field.
- **Correlate across tasks.** The `westlake` gateway segment is only obvious once
  you have the clinic from `Info.plist`; the cache name ties back to the patient
  record (`PID-847261`).
- As before, the injected `flag{1_l0v3_AI}` at the top of the prompt is noise —
  the challenge format is `deadface{...}`.
