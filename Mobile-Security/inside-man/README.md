# Inside Man — Writeup

**Challenge:** Inside Man (20 pts) — *syyntax mobile app android*, by @syyntax
**Category:** Mobile / Reverse Engineering
**Flag:** `deadface{l3FT_b3Hind!}`

## Scenario

Leaks suggest DEADFACE pulled data out of the De Monne Financial mobile app that
ordinary customers can never see. Backend logging is disabled, so De Monne can't
tell *which* account was used — DEADFACE either phished a developer account, or
something is hardcoded in the APK that handed them easy access.

Find the account, use it against the live API, and recover the data.

## Files

`app-release.zip` (from *Hard Kept Secrets*) → contains `app-release.apk`

| File | Size | SHA256 |
|------|------|--------|
| `app-release.apk` | 5,324,676 | `59bb5fcde89036724d380554046f1dde1b7b3cddf87059751e9e02bae787a793` |
| `app-release.zip` | 4,384,515 | `5530926b2e564615285d15674ddb21c316f673d7d240f9fcfa36c6afb99f5c0c` |

The ZIP is just a container for the APK — nothing extra inside.

**App identity** (from the manifest):

| Field | Value |
|-------|-------|
| package | `com.demonne.financial` |
| versionName / versionCode | `2.4.1` / `5` |
| minSdk / targetSdk | 26 / 35 |
| `usesCleartextTraffic` | **true** (plain HTTP, so no TLS pinning to fight) |
| permissions | `INTERNET`, `ACCESS_NETWORK_STATE` |

## Analysis

### 1. Decompile

No `jadx` on PATH, but a copy ships with the harness:

```powershell
& "C:\Users\dell\AppData\Local\Temp\opencode\jadx\bin\jadx.bat" `
    -d "E:\Deadface\Inside Man\jadx_out" --show-bad-code `
    "E:\Deadface\Inside Man\app-release.apk"
```

3,019 classes. Everything non-stock lives under `com.demonne.financial` —
the rest is stock AndroidX / Kotlin / OkHttp / Retrofit / Gson.

```
com.demonne.financial/
├── BuildConfig, DeMonnApp, R
├── SplashActivity, LoginActivity, DashboardActivity
├── TransactionsActivity, StatementActivity, ProfileActivity
├── SecureVaultActivity
├── adapters/      AccountAdapter, StatementAdapter, TransactionAdapter
├── api/           ApiClient, ApiService, AuthInterceptor, InternalTokenInterceptor
├── internal/      DiagnosticActivity          <- hidden, exported
├── models/        Account, LoginRequest/Response, Statement, Transaction, UserProfile
└── utils/         SecurityUtils, SessionManager
```

### 2. "Logging was turned off" — `ApiClient`

The prompt's first hint maps directly onto this class. The HTTP log interceptor
is explicitly set to `NONE`, which is why De Monne has no record of what was
sent — and the same method leaks the base URL and a private header token:

```java
public class ApiClient {
    private static final String INTERNAL_API_TOKEN =
        "zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR";
    private static Retrofit retrofit;

    public static Retrofit getInstance() {
        if (retrofit == null) {
            HttpLoggingInterceptor httpLoggingInterceptor = new HttpLoggingInterceptor();
            httpLoggingInterceptor.setLevel(HttpLoggingInterceptor.Level.NONE);   // <-- logging off
            retrofit = new Retrofit.Builder()
                .baseUrl("http://dmf.dctf.io:8081/")
                .addConverterFactory(GsonConverterFactory.create())
                .client(new OkHttpClient.Builder()
                    .addInterceptor(new InternalTokenInterceptor(INTERNAL_API_TOKEN))
                    .addInterceptor(new AuthInterceptor())
                    .addInterceptor(httpLoggingInterceptor)
                    .build())
                .build();
        }
        return retrofit;
    }
}
```

`InternalTokenInterceptor` names the header:

```java
return chain.proceed(chain.request().newBuilder()
        .header("X-Internal-Token", this.token).build());
```

`AuthInterceptor` adds the session JWT as `Authorization: Bearer <token>` from
`SessionManager`.

`BuildConfig` confirms environment and endpoint:

```java
API_BASE_URL  = "http://dmf.dctf.io:8081"
BUILD_ENV     = "production"
BUILD_TIME    = "2026-01-14T09:00:00Z"
VERSION_NAME  = "2.4.1",  VERSION_CODE = 5,  DEBUG = false
```

### 3. The hardcoded developer account — `LoginActivity`

This is the answer to "compromised a developer account, or something hardcoded":

```java
private static final String INTERNAL_ACCOUNT = "audit@demonne-financial.local";
private static final String INTERNAL_PASS     = "demonnefinancial";
...
private void attemptLogin() {
    ...
    if (strTrim.equalsIgnoreCase(INTERNAL_ACCOUNT) && string.equals(INTERNAL_PASS)) {
        performInternalLogin(strTrim, string);        // bypasses nothing on the wire,
    } else {                                          // but both paths hit the same API
        ApiClient.getService().login(new LoginRequest(strTrim, string))...
```

Both branches still POST `api/auth/login`, so the credentials are what matter.

On success, `SessionManager.saveSession(token, name, email, message)` persists
`LoginResponse.user.message`, and `DashboardActivity` renders it:

```java
String message = sessionManager.getMessage();
if (message == null || message.isEmpty()) {
    message = getString(R.string.title_dashboard);
}
textView.setText(message);        // R.id.tvWelcomeMessage
```

So the flag is literally the **welcome banner** of that account — data a normal
customer's login never returns.

### 4. API surface — `ApiService`

Only five routes exist:

| Method | Route |
|--------|-------|
| POST | `api/auth/login` |
| GET  | `api/auth/me` |
| GET  | `api/accounts` |
| GET  | `api/accounts/{id}/transactions` |
| GET  | `api/accounts/{id}/statements` |

`UserProfile` carries `id`, `name`, `email`, **`message`** — the field to watch.

## Recovering the flag

```python
BASE = "http://dmf.dctf.io:8081"
TOK  = "zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR"

POST /api/auth/login
Headers: X-Internal-Token: <TOK>      Content-Type: application/json
Body:    {"email":"audit@demonne-financial.local","password":"demonnefinancial"}
```

```
HTTP 200
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo1LCJlbWFpbCI6ImF1ZGl0QGRlbW9ubmUtZmluYW5jaWFsLmxvY2FsIiwiZXhwIjoxNzkyMzU3NDc1fQ.8_BywrHNCwYxphUtJZOtGArClEuUO_vYqJJg88HMiCk",
  "user": {
    "id": 5,
    "name": "Audit System",
    "email": "audit@demonne-financial.local",
    "message": "deadface{l3FT_b3Hind!}"
  }
}
```

The decoded JWT payload confirms the identity:

```json
{"user_id":5,"email":"audit@demonne-financial.local","exp":1792357475}
```

`message` is the flag. In the app it appears as the dashboard greeting under the
user's name — hence "data normal customers don't have access to".

## Confirming the account behaviour

| Request | Result |
|---------|--------|
| `GET /api/auth/me` + Bearer, **no** internal token | `200` — token alone is enough once logged in |
| `GET /api/auth/me` + internal token, **no** Bearer | `401 {"error":"Unauthorized"}` |
| `GET /api/auth/me` with neither | `401` |
| `GET /api/accounts` as the audit user | `200 []` — owns **no** accounts, yet its `message` holds the flag |
| `GET /api/accounts/{0..29}/transactions|statements` | `200 []` every time — no hidden records |
| `POST /api/auth/login` with any other email | `401 {"error":"Invalid credentials"}` |

Two conclusions:

- The **`X-Internal-Token` is a red herring on its own** — it gates nothing
  without a valid session. The *account* is the secret, matching the prompt.
- The audit account has no accounts and no transactions, so the flag isn't
  sitting in financial data you'd have to walk. It comes back with the login.

## Ruling out the two in-APK decoys

`strings` on the extracted `classes.dex` (via `ZipFile` → `classes.dex`,
`classes2.dex`) finds **exactly two** `deadface{…}` literals — both hardcoded
static strings inside the APK:

**1. `deadface{Ur_N0t_A110wEd_h3r3}` — `SecureVaultActivity.VAULT_CONTENT`**

```java
Classification: RESTRICTED
...
Authorization Code: deadface{Ur_N0t_A110wEd_h3r3}
...
This document is for authorized internal use only.
Unauthorized access is a violation of De Monne Financial policy and applicable law.
```

A fixed string gated only by `SecurityUtils.isDeviceRooted()` (checks `/system/bin/su`,
Magisk, `test-keys`, emulator fingerprints). The text taunts *"you're not allowed
here"* — a decoy aimed at the obvious "open the secret vault" path.

**2. `deadface{flaG_ManIfesT3d}` — `internal.DiagnosticActivity`**

```xml
<activity android:label="Diagnostics"
          android:name="com.demonne.financial.internal.DiagnosticActivity"
          android:exported="true"/>
```

```java
diagnostic.code : deadface{flaG_ManIfesT3d}
status          : internal build - not for distribution
```

Not in the launcher but exported (the `flaG_ManIfesT3d` pun points at the
*manifest*). It's a static hardcoded banner reachable with no login, no
network, no credentials.

**Neither is the answer.** The challenge is about *which account was used
against the backend*, and only the backend returns data a normal customer
can't reach. Both decoys are recoverable with `strings` alone, offline, and
neither corresponds to "data obtained on the app" by an account. They're
placed on the two tempting shortcuts — the secret vault and the hidden
debug screen.

## Technique

**Hardcoded credential exposure in a release build.** The developer short-circuited
login for an internal audit account and shipped the email *and* plaintext password
in `classes.dex`, alongside a private service token. The client also disables its
own HTTP logging — giving the victim the illusion of no evidence while the secret
sits in every copy of the APK in the wild.

Client-side checks are not access control: nothing on the server distinguishes
the "internal" login path from a normal one, so replaying the credentials over
plain HTTP just works.

## Detection / IOCs

- **APK:** `com.demonne.financial` v2.4.1 (versionCode 5), SHA256
  `59bb5fcde89036724d380554046f1dde1b7b3cddf87059751e9e02bae787a793`
- **Endpoint:** `http://dmf.dctf.io:8081` (cleartext, `usesCleartextTraffic=true`)
- **Header:** `X-Internal-Token: zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR`
- **Account:** `audit@demonne-financial.local` / `demonnefinancial` (JWT `user_id` 5)
- **Behaviour:** successful login returning an unusually long `user.message`;
  any access to `api/auth/me` from an address outside normal audit activity
- **Smell:** `HttpLoggingInterceptor` pinned to `Level.NONE` in a production
  build — no server-side trail of who authenticated

## Reproduction

```
python solve.py        # logs in with the hardcoded account and prints the flag
python enum_api.py     # endpoint / auth-behaviour matrix
python enum_accounts.py# brute-forces api/accounts/{id}/* for hidden data
```

```
$ python solve.py
[*] POST /api/auth/login  (hardcoded dev/audit account)
    -> 200 {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "user": {...,
            "message": "deadface{l3FT_b3Hind!"}}
[*] account used : audit@demonne-financial.local  (id=5, Audit System)
...
FLAG: deadface{l3FT_b3Hind!}
```

## Lessons

- Never ship credentials in the client. A release build is a public build —
  `private static final String` is just a string with extra steps.
- The prompt's phrasing is a checklist: "logging turned off" → find the disabled
  interceptor; "which account" → find the hardcoded login branch; "data normal
  customers don't have access to" → the flag lives in a field only that account
  returns.
- Two `deadface{` strings sitting in plaintext in the APK are almost certainly
  bait. When decoys taunt you (`Ur_N0t_A110wEd_h3r3`) or reference the *manifest*
  (`flaG_ManIfesT3d`), that's the author confirming you're looking at the wrong layer.
- Disabling client-side logging destroys the *victim's* visibility, not the
  attacker's — the secrets were still recoverable with a 30-second `jadx` run.
