# Car Crash — DEADFACE CTF 2026 Write-up

| | |
|---|---|
| **Category** | OSINT |
| **Provided File** | `14876559-99c8-4f1d-ba01-42bce7ec374d.jpg` (`car_crash.jpg`) |
| **Flag** | `deadface{08_10_1961}` |

## Objective

Identify the company that owns the commercial truck in the provided crash image, find its founding date, and format it as `deadface{MM_DD_YYYY}`.

---

## Step 1: Image Analysis & Pivot Identification

When analyzing the provided image of the intersection crash, the white box truck lacks obvious corporate branding or logos on the trailer. However, scanning the vehicle for regulatory markings reveals a key piece of metadata on the upper side of the truck's cab. Zooming in shows a registered Department of Transportation number:

**Extracted Data:** `USDOT: 080806`

---

## Step 2: Database Lookup

Commercial carriers in the United States are required to display this number. Plugging `080806` into the Federal Motor Carrier Safety Administration (FMCSA) SAFER Company Snapshot tool—or simply running a targeted search for `"USDOT" "080806"`—pulls up the carrier registration records.

**Identified Company:** J.B. Hunt Transport, Inc.

---

## Step 3: Historical Reconnaissance

With the target company identified as J.B. Hunt, the next step is finding its origin. A quick check of their corporate history or Wikipedia page confirms that Johnnie Bryan Hunt founded the trucking company in August 1961.

**Founding Date:** August 10, 1961

---

## Step 4: Flag Formatting

The challenge parameters require the flag to be formatted exactly as `deadface{MM_DD_YYYY}`:

- **Month:** `08` (August)
- **Day:** `10`
- **Year:** `1961`

## Final Flag

```text
deadface{08_10_1961}
```
