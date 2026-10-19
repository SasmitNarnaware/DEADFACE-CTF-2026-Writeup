# Hard Kept Secrets — syyntax Writeup

## Challenge
De Monne Financial has suffered repeated security incidents tied to the latest
release of their Android banking app. They cannot figure out how DEADFACE is
reaching their API, and it is "too early to tell" whether a password was
cracked. Task: **recover the internal API token baked into the APK and submit
it as the flag.**

- **Category:** Mobile / Android
- **Author:** `@syyntax`
- **Points:** 20
- **Format:** `deadface{...}`

## Files
`app-release.apk` (5,324,676 bytes)

| | Value |
|---|---|
| Published SHA256 | `5530926b2e564615285d15674ddb21c316f673d7d240f9fcfa36c6afb99f5c0c` |
| Our copy's SHA256 | `59BB5FCDE89036724D380554046F1DDE1B7B3CDDF87059751E9E02BAE787A793` |

> **Hash mismatch — see [Provenance](#provenance) below.** Our copy has had its
> signature block stripped. This does not affect the flag, which is a plain
> string constant in the DEX, but it is worth knowing about.

### Build metadata
| Field | Value |
|---|---|
| Package | `com.demonne.financial` |
| Version | 2.4.1 (code 5) |
| Build env | `production` |
| Build time | `2026-01-14T09:00:00Z` |
| compileSdk / targetSdk | 35 / 35, minSdk 26 |
| AGP | 8.3.2 |
| Signing | **none** (stripped) |

## Answer
```
deadface{zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR}
```

The bare token, i.e. the value of `ApiClient.INTERNAL_API_TOKEN`:
```
zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR
```

---

## Method

### 1. The APK is a ZIP
No emulator, no Frida, no rooted handset needed. Static analysis is enough:

```
tar -xf app-release.apk -C apk_extract
```

904 entries. The interesting ones: `classes.dex` (9.6 MB), `classes2.dex`
(433 KB), `AndroidManifest.xml` (binary AXML), `resources.arsc`. No native
`.so` libraries, no `assets/` beyond ART baseline profiles — this is a pure
Kotlin/Java app, so everything is recoverable from the DEX.

### 2. Grep the DEX string pool
DEX keeps every string literal in a central `string_ids` table. Rather than
`strings | grep`, parse the pool properly — it gives you *exact* constant
values with no byte-boundary artefacts. See `solve.py` for the parser
(`dex_strings()`), which handles the `uleb128` length prefix and MUTF-8
terminator.

A quick triage pass over the pool for `token|api_key|secret|deadface|
authorization|bearer` immediately surfaced the app's own classes:

```
Authorization
Bearer
INTERNAL_API_TOKEN
InternalTokenInterceptor.java
Lcom/demonne/financial/api/InternalTokenInterceptor;
X-Internal-Token
diagnostic.code : deadface{flaG_ManIfesT3d}
Authorization Code: deadface{Ur_N0t_A110wEd_h3r3}
```

Three `deadface{` strings, but only one is a token. See [Decoys](#decoys).

### 3. Decompile
```
jadx -d apk_src --no-res app-release.apk
```
(jadx 1.5.6, JDK 17. 83 deprecation-level errors, all inside third-party libs —
the `com.demonne.financial` package decompiled cleanly.)

The app is only 26 classes. The networking core is four files.

### 4. The token
`com/demonne/financial/api/ApiClient.java`:

```java
public class ApiClient {
    private static final String INTERNAL_API_TOKEN =
        "zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR";
    private static Retrofit retrofit;

    public static Retrofit getInstance() {
        if (retrofit == null) {
            HttpLoggingInterceptor log = new HttpLoggingInterceptor();
            log.setLevel(HttpLoggingInterceptor.Level.NONE);   // logging off
            retrofit = new Retrofit.Builder()
                .baseUrl("http://dmf.dctf.io:8081/")
                .addConverterFactory(GsonConverterFactory.create())
                .client(new OkHttpClient.Builder()
                    .addInterceptor(new InternalTokenInterceptor(INTERNAL_API_TOKEN))
                    .addInterceptor(new AuthInterceptor())
                    .addInterceptor(log)
                    .build())
                .build();
        }
        return retrofit;
    }
```

And where it is spent — `api/InternalTokenInterceptor.java`:

```java
public class InternalTokenInterceptor implements Interceptor {
    private final String token;

    public InternalTokenInterceptor(String str) { this.token = str; }

    @Override
    public Response intercept(Chain chain) throws IOException {
        return chain.proceed(chain.request().newBuilder()
                .header("X-Internal-Token", this.token)
                .build());
    }
}
```

So **every single API call** the app makes carries the production internal
token in an `X-Internal-Token` header. That is the whole answer to De Monne's
question "how does DEADFACE have access to our API?" — they don't need a
password. The credential ships to every user, in the clear, on every request.

`AuthInterceptor` adds a *second*, separate credential — the user's session
JWT as `Authorization: Bearer ...` — from `SessionManager` (`SharedPreferences`
file `dmf_session`, key `auth_token`). That one is per-user and legitimately
obtained at login; it is **not** the flag.

### 5. Corroborate before submitting
Three checks, because "it looked like a flag in strings output" is not proof:

1. **Raw confirmation.** The value appears verbatim in the parsed DEX string
   pool — it is a real `const-string` target, not a jadx reconstruction.
2. **It decodes.** `base64.b64decode(token, validate=True)` → 48 bytes
   (`cea251955c0103d5e6da513910f8e06e3ff8acec659186600ed91d3fb8d5f34ad9
   980b16b9673849fe540bb7d58290ad1`). High entropy, no structure, no padding —
   consistent with a random 384-bit key, not an encoded message or a mangled
   identifier.
3. **It is unique.** Sweeping all string literals across the 26 app classes
   turns up exactly one hardcoded credential of this shape.

---

## Decoys

The author planted two convincing-but-wrong flags. Both are rendered in UI
strings and neither is ever transmitted to the API.

| Decoy | Location | Presentation |
|---|---|---|
| `deadface{flaG_ManIfesT3d}` | `internal/DiagnosticActivity` | printed under a dashed rule as `diagnostic.code`, in a screen labelled "internal build — not for distribution" |
| `deadface{Ur_N0t_A110wEd_h3r3}` | `SecureVaultActivity` (`VAULT_CONTENT`) | the "Authorization Code" of a forged *Q1 2026 Security Verification* memo, Classification: RESTRICTED |

They are deliberately discoverable — the bait is stronger than the real
answer, which is an opaque base64 blob with no `deadface{}` wrapper. Note that
the real token is the only one of the three that is **not already formatted as
a flag**; you have to add the wrapper yourself, which is exactly what the
prompt's example (`deadface{2GFEwQvPVIMLJmjGYHgKFWkmpuhrjEnSewMrFRyVMEQ=}`)
is telling you.

`SecureVaultActivity` adds theatre on top: it calls
`SecurityUtils.isDeviceRooted()` and shows a "restricted" screen instead of
the memo on rooted devices. Irrelevant to the flag — the string is in the DEX
regardless of what the runtime decides to display. Classic mobile trap: the
root check gates the *view*, never the *data*.

---

## Bonus findings

Worth reporting in a real engagement, even though the challenge only wanted
the token.

### Hardcoded backdoor account
`LoginActivity.java`:
```java
private static final String INTERNAL_ACCOUNT = "audit@demonne-financial.local";
private static final String INTERNAL_PASS     = "demonnefinancial";

...
if (strTrim.equalsIgnoreCase(INTERNAL_ACCOUNT) && string.equals(INTERNAL_PASS)) {
    performInternalLogin(strTrim, string);   // client-side branch ...
} else {
    ApiClient.getService().login(...)        // ... normal path
}
```
Both branches ultimately POST to `api/auth/login`, so the client-side special
case is cosmetic — but it documents a privileged account name and its password
in plaintext, and confirms the account exists server-side.

### `DiagnosticActivity` is exported
`AndroidManifest.xml`:
```xml
<activity android:label="Diagnostics"
          android:name="com.demonne.financial.internal.DiagnosticActivity"
          android:exported="true"/>
```
Every other activity correctly sets `exported="false"`. As it stands, **any
app on the device** can launch it with an explicit `Intent` and read the build
config, endpoint, and device identifiers. This is the delivery mechanism for
the `flaG_ManIfesT3d` decoy.

### Cleartext traffic permitted
```xml
<application android:usesCleartextTraffic="true" ...>
```
paired with `BuildConfig.API_BASE_URL = "http://dmf.dctf.io:8081"`. The API is
plain HTTP, so the internal token *and* user session JWTs traverse the network
unencrypted — trivially harvested by any on-path attacker. This is arguably a
more serious finding than the hardcoded token itself.

### Backup enabled
`android:allowBackup="true"` — `SharedPreferences` (`dmf_session`, holding
`auth_token`) is included in `adb backup` / cloud backup on pre-API-31 devices.

### Log suppression
`HttpLoggingInterceptor` is installed but pinned to `Level.NONE`. Suggests
logging *was* on at some point and was turned off rather than removed — check
crash/analytics reports for leaked headers.

---

## Provenance

Our copy's SHA256 (`59BB5FCD…`) does not match the challenge's published value
(`5530926b…`). Reason: **the APK is unsigned.**

A normally-built APK always ends with a JAR signature block:
`META-INF/MANIFEST.MF`, `META-INF/CERT.SF`, `META-INF/CERT.RSA`. This one has
none — `META-INF` contains only AndroidX `.version` markers, Gradle
`app-metadata.properties`, and two Kotlin service descriptors.
`version-control-info.textproto` reads:

```
generate_error_reason: NO_SUPPORTED_VCS_FOUND
```

So the archive was repacked and the signature stripped, which rewrites every
ZIP local header and changes the hash. Consequences:

- The APK **cannot be installed** on a real device as-is; it would need
  re-signing (`apksigner sign --ks debug.keystore`).
- The `classes.dex` payload is intact, so this does not affect the flag — and
  the token was confirmed straight out of the string pool rather than trusted
  from the decompiler alone.
- If the submission is ever rejected, this is the first thing to re-verify
  against the pristine download.

---

## Remediation

For De Monne, in priority order:

1. **Rotate the internal token immediately.** Treat it as burned — it is in
   every installed copy. `X-Internal-Token` is a shared secret with no
   per-user scoping, so it cannot be revoked selectively.
2. **Stop shipping server credentials to clients.** The server should
   authenticate the *app* through attestation (Play Integrity API / app
   attestation), not a static string.
3. **Enforce TLS.** `usesCleartextTraffic="true"` must go; add a network
   security config that pins the API certificate.
4. **Set `DiagnosticActivity` to `exported="false"`.** No third-party app
   needs it.
5. **Scrub the build.** Remove `INTERNAL_ACCOUNT` / `INTERNAL_PASS`; move any
   remaining constants into `local.properties` / CI secrets so they are never
   compiled into a release `BuildConfig`.
6. **Set `allowBackup="false"`,** or exclude `dmf_session` via a backup rule.
7. **Ship without debug artifacts.** A `com.demonne.financial.internal`
   package with a diagnostics screen has no place in a production build; keep
   it behind a `buildType` gate.

---

## Files here

```
Hard Kept Secrets/
├── WRITEUP.md                      this file
├── solve.py                        standalone solver (stdlib only, no jadx)
├── decompiled/                     jadx output, app package only
│   └── demonne/financial/
│       ├── BuildConfig.java
│       ├── LoginActivity.java      hardcoded backdoor account
│       ├── SecureVaultActivity.java  decoy #2
│       ├── api/
│       │   ├── ApiClient.java      ★ the token
│       │   ├── ApiService.java     endpoint list
│       │   ├── AuthInterceptor.java
│       │   └── InternalTokenInterceptor.java  ★ header injection
│       ├── internal/
│       │   └── DiagnosticActivity.java   decoy #1, exported
│       ├── models/  adapters/  utils/
│       └── ...
└── evidence/
    ├── AndroidManifest.decoded.xml
    ├── app-metadata.properties
    ├── strings_interesting.txt     filtered DEX string-pool dump
    └── version-control-info.textproto
```

### Reproduce
```
python solve.py "E:\Deadface\secerete\app-release.apk"
```

```
[*] DEX files : classes.dex, classes2.dex
[*] strings   : 70739
[*] key-material candidates (after filtering): 1
    zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR  (64 chars -> 48 bytes)  <-- TOKEN

FLAG: deadface{zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR}

[i] ignored decoy: deadface{Ur_N0t_A110wEd_h3r3}
[i] ignored decoy: deadface{flaG_ManIfesT3d}
```

The narrowing from **70,739 strings → 1 candidate** is the whole trick, and it
rests on one observation: key material never parses as a Java identifier.
Long AndroidX method names like
`getContentDescriptionExceedsMaxBadgeNumberStringResource` are technically
valid base64 and decode to plausible-looking bytes, so a naive
"long base64 blob" scan returns ~869 false positives. Filtering out anything
matching `^[A-Za-z_$][A-Za-z0-9_$]*$`, plus the base64 alphabet table itself,
leaves exactly the token. The `/` and `+` characters are what make it
structurally distinct from any identifier.
