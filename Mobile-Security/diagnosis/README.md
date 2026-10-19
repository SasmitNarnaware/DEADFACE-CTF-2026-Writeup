# Writeup — Diagnosis (100 pts)

| | |
|---|---|
| **Event** | Deadface CTF |
| **Category** | Mobile / Android |
| **Author** | @syyntax |
| **Difficulty** | 100 pts (easy) |
| **Artifact** | `app-release.apk` (from "Hard Kept Secrets") |

> *"One of De Monne's developers suspects there is hidden activity occurring in the app,
> possibly due to manifest misconfigurations."*

The prompt is basically telling us where to look: the **AndroidManifest.xml**, hunting for a
component that is reachable when it shouldn't be.

---

## 1. Recon — the APK is just a ZIP

An APK is a standard ZIP archive. Extract it:

```powershell
Copy-Item app-release.apk app.zip
Expand-Archive app.zip -DestinationPath extracted
```

```
extracted/
├── AndroidManifest.xml   (7,324 bytes — binary XML)
├── classes.dex           (9.6 MB — Kotlin/Java bytecode)
├── classes2.dex
├── resources.arsc
├── res/  assets/  kotlin/  META-INF/  okhttp3/
```

Useful observations already:

- `okhttp3/` → the app talks to a network backend.
- Package: `com.demonne.financial`, versionName `2.4.1` (versionCode 5) — a banking app
  ("De Monne Financial").

## 2. Decode the manifest

`AndroidManifest.xml` is stored as **binary AXML**, not plain text. Use the Android SDK
build-tools (`aapt`/`aapt2`):

```powershell
aapt2 dump xmltree --file AndroidManifest.xml app-release.apk
```

Manifest highlights:

```xml
<manifest package="com.demonne.financial" android:versionCode="5" android:versionName="2.4.1">
  <uses-permission android:name="android.permission.INTERNET"/>
  <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
  <application android:name="com.demonne.financial.DeMonnApp"
               android:allowBackup="true"
               android:usesCleartextTraffic="true" ...>
```

Then the activities. The legitimate ones are all locked down:

```xml
<activity android:name=".SplashActivity"              android:exported="true">   <!-- launcher -->
<activity android:name=".LoginActivity"               android:exported="false"/>
<activity android:name=".DashboardActivity"           android:exported="false"/>
<activity android:name=".TransactionsActivity"        android:exported="false"/>
<activity android:name=".StatementActivity"           android:exported="false"/>
<activity android:name=".SecureVaultActivity"         android:exported="false"/>
<activity android:name=".ProfileActivity"             android:exported="false"/>
```

…but at **line 64** there's the odd one out:

```xml
<activity
    android:label="Diagnostics"
    android:name="com.demonne.financial.internal.DiagnosticActivity"
    android:exported="true" />          <!-- 👈 the misconfiguration -->
```

### Why this is the bug

- It lives in an `internal` package with **no launcher icon and no intent-filter**, so it
  never appears in the app drawer or anywhere in the UI — it's "hidden activity", exactly
  as the story hinted.
- But `android:exported="true"` means **any app on the device (or `adb`) can start it**,
  without any permission. This is the classic "exported component with no reason to be
  exported" misconfiguration.
- The `label` is literally *"Diagnostics"* and the challenge is called *"Diagnosis"* —
  strong nudge.

## 3. Get into the hidden activity

**Dynamic (on a device/emulator with the APK installed):**

```bash
adb shell am start -n com.demonne.financial/.internal.DiagnosticActivity
```

**Static (what I did — no device needed):** decompile the DEX and read what `onCreate`
renders. Using `dexdump` from build-tools:

```powershell
dexdump -d classes.dex > classes_dump.txt
```

Locate the class `Lcom/demonne/financial/internal/DiagnosticActivity;` and its
`onCreate:(Landroid/os/Bundle;)V` method. The code:

1. `setContentView(R.layout.activity_diagnostic)`
2. Grabs the TextView `R.id.tvDiagOutput`
3. Builds a diagnostic report string:

```
build.version   : 2.4.1 (5)
build.env       : production
build.timestamp : 2026-01-14T09:00:00Z
api.endpoint    : http://dmf.dctf.io:8081
device.model    : <Build.MODEL>
device.sdk      : <Build.VERSION.SDK_INT>
device.id       : <Build.ID>

████████████████████████████████████████████
diagnostic.code : deadface{flaG_ManIfesT3d}
████████████████████████████████████████████

status          : internal build — not for distribution
```

4. `tvDiagOutput.setText(...)` — and the flag is on screen.

## 4. Flag

```
deadface{flaG_ManIfesT3d}
```

The flag text is a cheeky nod to the vulnerability class itself: the flag was **manifested**
into existence via an exported activity.

---

## Remediation

If De Monne asked for a fix:

```xml
<activity android:name=".internal.DiagnosticActivity"
          android:exported="false" />
```

…and ideally strip debug/diagnostic screens from release builds entirely
(`buildConfig`-gated or via a debug-only source set).

---

## Appendix — another red herring flag

Deep in `SecureVaultActivity` there is a second embedded string:

```
Authorization Code: deadface{Ur_N0t_A110wEd_h3r3}
```

That one belongs to the **"Hard Kept Secrets"** challenge (which is where this APK came
from), *not* to Diagnosis. Don't get baited — for this challenge the answer is the
diagnostic screen flag above.

### Tools used

| Tool | Purpose |
|---|---|
| PowerShell `Expand-Archive` | Unzip the APK |
| `aapt2 dump xmltree` (Android SDK build-tools 36.0.0) | Decode binary `AndroidManifest.xml` |
| `dexdump -d` (build-tools) | Dump `classes.dex` bytecode to read `DiagnosticActivity` |
| *(optional)* `adb shell am start` | Launch the exported activity on-device |
