# DEADFACE CTF 2026 — SQL Skillz (Aurora Patient Portal) — Writeup

**Challenge:** SQL Skillz
**Points:** 50
**Category:** Mobile / SQL (iOS)
**Author:** @G2Gh0st
**Artifact:** `AuroraPatientPortal.ipa` (same bundle as "Info Leaks" and "Down the Rabbit Hole")
**DB of interest:** `Payload/aurora-patient-portal.app/aurora_meds.sqlite`
**Flag:** `deadface{Candesartan}`

---

## 0. TL;DR

1. The previous two tasks hand you the keys you need to "query the application
   database file":
   - **Info Leaks** → the patient identity (`Mara Voss`, DOB `1988-04-17`, clinic `Westlake`).
   - **Down the Rabbit Hole** → the patient's unique **`pid`**, `847261`, stamped into the
     X-ray's XMP metadata (`<dc:identifier>PID-847261</dc:identifier>`).
2. The app ships a single SQLite DB, `aurora_meds.sqlite`, with one table:

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

3. Select the row for the patient's `pid`:

   ```sql
   SELECT * FROM medications WHERE pid = 847261;
   ```

   ```
   847261 | Ibuprofen 400 mg (Every 8 hours as needed)
          | Candesartan 16 mg (Once daily)
   ```

4. The task asks for the medication(s) **other than Ibuprofen** → **Candesartan**.

```
deadface{Candesartan}
```

---

## 1. Starting point — what the earlier tasks gave us

Nothing new to download; this is a follow-on to two challenges against the same
`.ipa`. Recall an `.ipa` is just a ZIP:

```powershell
Copy-Item AuroraPatientPortal.ipa app.zip
Expand-Archive app.zip out
```

Bundle contents:

```
Payload/aurora-patient-portal.app/
├── Aurora Health Mobile          # main executable (Swift/SwiftUI)
├── Info.plist                    # Info Leaks  -> name / DOB / clinic
├── aurora_meds.sqlite            # <-- the DB to query (this task)
├── aurora_chest_xray.jpg         # Rabbit Hole -> pid (XMP dc:identifier)
├── Assets.car
├── AppIcon60x60@2x.png
├── AppIcon76x76@2x~ipad.png
├── embedded.mobileprovision
├── PkgInfo
└── _CodeSignature/CodeResources
```

The two data points that matter:

| From | Value |
|------|-------|
| **Info Leaks** (`Info.plist` → `AuroraPatientBootstrap`, base64 JSON) | `patientName = "Mara Voss"`, `dateOfBirth = "1988-04-17"`, `clinic = "Westlake"` |
| **Down the Rabbit Hole** (XMP in `aurora_chest_xray.jpg`) | `dc:identifier = PID-847261` |

The **`pid` is the join key.** The patient identity tells you *who*, and the
`pid` tells you *which row* to pull.

---

## 2. The database — schema and shape

`aurora_meds.sqlite` is a plain SQLite 3 file with exactly one table (plus two
indexes on the medication columns):

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

CREATE INDEX idx_medications_medication_1 ON medications(medication_1);
CREATE INDEX idx_medications_medication_2 ON medications(medication_2);
```

Note the `pid` column is the **primary key** — the app's "Patient ID" — which is
exactly the identifier recovered from the X-ray metadata.

There are **100 rows**, but only **51 distinct medication pairs**: 50 filler
pairs are each repeated twice for two synthetic `pid` ranges (`101001…818263`),
and a single unique row at the end carries the real patient's key.

Quick enumeration:

```python
import sqlite3

con = sqlite3.connect("aurora_meds.sqlite")
cur = con.cursor()

print(cur.execute(
    "SELECT name, sql FROM sqlite_master WHERE type IN ('table','index')"
).fetchall())
print("row count:", cur.execute("SELECT count(*) FROM medications").fetchone()[0])
```

---

## 3. The query — medications for `pid = 847261`

```python
import sqlite3

con = sqlite3.connect("aurora_meds.sqlite")
cur = con.cursor()

row = cur.execute(
    "SELECT * FROM medications WHERE pid = ?", (847261,)
).fetchone()
print(row)
```

or directly in SQL:

```sql
SELECT medication_1, medication_1_dosage, medication_1_frequency,
       medication_2, medication_2_dosage, medication_2_frequency
FROM   medications
WHERE  pid = 847261;
```

Result:

```
(847261,
 'Ibuprofen', '400 mg', 'Every 8 hours as needed',
 'Candesartan', '16 mg', 'Once daily')
```

The patient takes:

| Slot | Medication | Dosage | Frequency |
|------|------------|--------|-----------|
| `medication_1` | Ibuprofen | 400 mg | Every 8 hours as needed |
| `medication_2` | **Candesartan** | 16 mg | Once daily |

The task: *"determine what medications the current patient is taking **other
than Ibuprofen**."* Excluding `medication_1`, the answer is `medication_2`:
**Candesartan**.

---

## 4. Why `847261` and not some other row

Because "the current patient" is uniquely identified across the whole bundle:

- The X-ray's `dc:identifier` is `PID-847261` (the authoritative stamp).
- `847261` is a valid `pid` primary key in `medications` — matching both the XMP
  value **and** the record the app's data layer keys on.
- No other row is tied to the name/DOB or the ID anywhere in the bundle.

If you instead tried to guess from the Info Leaks data alone, the DB has no name
or DOB column too — the `pid` from the Rabbit Hole task is what disambiguates the
correct row from the 99 filler rows. That's the intended chain: **Info Leaks →
Rabbit Hole → SQL Skillz.**

---

## 5. Decoys / noise

- The 99 other rows are synthetic filler designed to make a blind `SELECT *`
  useless without the correct `pid`.
- The main binary's fake "diagnostics" strings (`Patient Cache Realm`,
  `patient-summary-cache-v2`, `gw-westlake-int-03`, `Last Gateway Check`, …)
  contain no real records.
- A `flag{1_l0v3_AI}` string was injected at the top of the challenge prompt. It
  is **not** the flag — the CTF uses the `deadface{...}` format. Ignore it.

---

## 6. Answer

```sql
SELECT medication_2
FROM   medications
WHERE  pid = 847261;
-- Candesartan
```

```
deadface{Candesartan}
```

---

## 7. Lessons / notes

- **Chain your artifacts.** A mobile bundle leaks identity (`Info.plist`) and
  identifiers (XMP in media) separately; the *join key* (`pid`) connects them to
  the SQL dataset.
- **Primary keys are the pivot.** `pid INTEGER PRIMARY KEY` in `medications`
  tells you exactly what to query once you have the patient ID.
- **Don't trust similarity.** With 100 rows and a repeated pattern, the only
  correct approach is an exact `WHERE pid = ...` lookup — never eyeballing.
- **SQLite is trivially inspectable.** No credentials, no server: `sqlite3`,
  DB Browser, or a two-line Python script reads the whole file.
- **Read the question literally.** The DB row holds *two* medications; the task
  says "other than Ibuprofen", so the answer is the *second* one — Candesartan.
