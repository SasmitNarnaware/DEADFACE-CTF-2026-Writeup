# Live Boot — Writeup

**Challenge:** Live Boot (DEADFACE CTF)
**Creator:** @syyntax
**Category:** Medical device / Linux
**Flag format:** `deadface{...}`
**Device:** http://emedra.dctf.io:8080/

> DEADFACE got a live shell on the device. Hospital staff say there is no way
> to reach the underlying OS. Find the hardcoded keys that are NOT in the
> Field Manual.

---

## TL;DR

Boot the **Live Linux USB-A** into the **USB-A port** → a simulated shell opens
(`ubuntu@live`). `lsblk` shows the internal disk, mount it, and read the
ScanWorks config. The hardcoded upstream API key is:

```
deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}
```

---

## Walkthrough

1. **Recon / API** — the device serves a small JSON API:
   - `GET /api/device` → tools (HDMI, DisplayPort, Live Linux USB-A, Rubber
     Ducky, BLE Sniffer), ports, hotspots.
   - `POST /api/connect {tool, port}` → returns `{ok, windowType, token}`.

2. **Live boot** — connect the Live Linux USB-A to the USB-A port:
   ```
   POST /api/connect {"tool":"live-linux","port":"usb-a"}
   → {"ok":true,"windowType":"terminal","token":"..."}
   ```

3. **Shell** — every command goes to `POST /api/shell {token, line}`:
   ```
   lsblk
   → sda 32G / sda1 512M vfat /boot/efi / sda2 31G ext4 "scanworks-data"

   sudo mount /dev/sda2 /mnt
   ls -la /mnt/opt/scanworks
   → config.yaml, scanworks.bin, calibration/, logs/
   ```

4. **The key** — `/mnt/opt/scanworks/config.yaml`:
   ```yaml
   api_key: deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}
   ```

---

## Other hardcoded keys / tokens found (side channels)

These are all `deadface{...}` strings exposed by the same device. They are
useful context but the challenge flag is the config `api_key`.

| # | Flag | Where |
|---|------|-------|
| 1 | `deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}` | `/mnt/opt/scanworks/config.yaml` (`api_key`) — **primary** |
| 2 | `deadface{v13w_s0urc3_sav3s_l1v3s}` | Kiosk login page HTML (temp QA technician PIN) |
| 3 | `deadface{d3fault_cr3ds_n3v3r_ch4ng3d}` | `POST /api/kiosk/auth` with `emedra-svc` / `ChangeMe!2019` (`maintenanceToken`) |
| 4 | `deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}` | HDMI mirror OSD at verbosity level 3 (`diagSession`) |
| 5 | `deadface{un3ncrypt3d_b4bbl3_fr0m_th3_sku11}` | BLE maintenance-log characteristic `0x37` (reseq + base64) |
| 6 | `deadface{un10ck3d_k10sk_qu4cks_b4ck}` | Rubber Ducky `debug.dump(patients)` on the kiosk debug console |

### Notes on the side channels

- **Field Service Manual** (`/assets/cs9000-field-service-manual.pdf`): gives
  the factory technician account `emedra-svc` / `ChangeMe!2019` and the BLE
  GATT layout (0x2a vitals, 0x37 maintenance log). The challenge's key is the
  one *not* spelled out there.
- **Kiosk login**: `/api/kiosk/login` HTML leaks a temp QA PIN; authenticating
  with the manual creds returns a `maintenanceToken`.
- **HDMI mirror**: connect `hdmi`→`hdmi`, then raise OSD to level 3 via
  `GET /api/external-display?level=3` (raw dump).
- **BLE**: connect `ble-sniffer`→`usb-a`, `GET /api/capture`; sort `0x37`
  payloads by `seq`, hex→ascii→base64-decode.
- **Rubber Ducky**: connect `rubber-ducky`→`usb-a`, `POST /api/kiosk/hid`
  with `STRING debug.dump(patients)`.

---

## Flag

```
deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}
```

## Artifacts in this folder

- `assets/` — app JS/CSS (index, terminal, kiosk, BLE, HID, external display)
- `brain-scanner.glb` — 3D model (no hidden data)
- `cs9000-field-service-manual.pdf` — Field Service Manual
- `extract_pdf.py`, `inspect_glb.py` — analysis helpers
