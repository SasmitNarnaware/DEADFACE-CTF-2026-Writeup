# No Holding Back — DEADFACE CTF 2026 (mobile app / osint, 210 pts)

> *DEADFACE was able to extract bank data from several of De Monne's customers.
> Something in the app's logic allows DEADFACE to gather details from pretty much any user
> they want. DEADFACE claims they left a flag behind as proof that they have access to
> De Monne's customer data. The problem is, we don't know who the user is (or their password).*

**Flag:** `deadface{IDOR_u_2_f1nD_m0r3_Fl4gz}`

```
deadface{IDOR_u_2_f1nD_m0r3_Fl4gz}
```

## Solution overview

Three pieces, one chain:

| # | Piece | Where |
|---|-------|-------|
| 1 | **OSINT** — find the leaked customer creds | GhostTown → DoomScroll |
| 2 | **Mobile** — API base URL + `X-Internal-Token` | `app-release.apk` (from *Hard Kept Secrets*) |
| 3 | **Exploit** — IDOR on account endpoints | `GET /api/accounts/{id}/…` doesn't check ownership |

---

## 1. OSINT: who is the user, and the password

Scope note from the event brief: everything in-scope lives on `*.dctf.io`, and the
`deadface.io` subdomains (like GhostTown) are info-only. So: start at DEADFACE's own forum.

**GhostTown — `ghosttown.deadface.io`** → category **Havoc** (ongoing campaigns) →

> **"We found a DMF password in a public dump. Also... JOHN DOE IS A REAL PERSON???"**
> (`/t/58/…`, by `lilith`)
>
> lilith: *"I was digging through some publicly circulating credential dumps looking for
> anything connected to De Monne Financial's app. And guess what? Found a DMF account with
> a password sitting right there in one of the dumps… THE ACCOUNT BELONGS TO SOMEONE NAMED
> JOHN DOE… the dump lists a DMF employee and a plaintext password."*
>
> spookyboi: **"Already shared on DoomScroll lol"**

**DoomScroll — `doomscroll.dctf.io`** ("Social media for the digital underworld") →
user **`/spookyboi`** → **`/post/267`** (screenshot, saved to
`evidence/doomscroll_267_screenshot.png`): a DEADFACE channel log titled
*"De Monne Financial (DMF) - Initial Access"* with the dump snippet attached:

```
1045323    john.doe@example.com:Welcome1!      <- highlighted
```

> *"Hit on a credential almost immediately… I logged into the DMF mobile app with the
> creds and got info, linked accounts, transaction history… John Doe is a real person."*

So: **`john.doe@example.com` / `Welcome1!`** — a real De Monne customer, creds from a
public breach dump (password reuse).

## 2. Mobile: talking to the backend

The APK (`com.demonne.financial`, see the *Inside Man* / *Diagnosis* writeups) gives the
API surface:

- base URL: `http://dmf.dctf.io:8081`
- every request carries `X-Internal-Token: zqJRlVwBA9Xm2lE5EPjgbj/…` (`ApiClient.java`)
- routes: `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/accounts`,
  `GET /api/accounts/{id}/transactions`, `GET /api/accounts/{id}/statements`

```
POST /api/auth/login   {"email":"john.doe@example.com","password":"Welcome1!"}
-> 200 {"token":"eyJ…","user":{"id":1,"name":"John Doe",
        "email":"john.doe@example.com","message":"Welcome back, John!"}}
```

John Doe's own data (`user_id` 1) is boring: accounts **1001** (checking) and **1002**
(savings), groceries/rent transactions. No flag there — and his `message` is just a
greeting.

## 3. The "app's logic" = IDOR

`ApiService.getTransactions(int id)` / `getStatements(int id)` take a raw account id from
the caller, and the **server never checks that the account belongs to the logged-in user**
— the IDOR the challenge hints at ("gather details from pretty much any user they want").
Account ids are also predictable: John Doe's start at 1001.

Sweep `GET /api/accounts/{id}/transactions|statements` for `id` around 1000 (with John
Doe's JWT):

| account | content |
|---|---|
| 1001, 1002 | John Doe's own accounts |
| 1003 | someone else's checking (electric company, payroll) |
| 1006 | someone else's (mortgage, payroll) |
| **1007** | **restricted internal-audit statement → the flag** |

```json
GET /api/accounts/1007/statements
[{"account_id":1007,"id":4,"period":"Q1 2026 Internal Audit Summary",
  "reference":"AUD-2026-Q1-99001",
  "summary":"RESTRICTED — De Monne Financial Internal Audit Division | Ref:
             deadface{IDOR_u_2_f1nD_m0r3_Fl4gz} | All ledger entries verified and
             reconciled. No discrepancies found."}]
```

DEADFACE stashed their proof of "access to De Monne's customer data" inside another
customer's (1007's) account statement — readable by anyone with *any* valid session,
because the endpoint trusts the account id instead of the owner. The flag text spells out
the vuln: **IDOR**.

Sweeps of ids 1–29, 990–1249 and 2000/10000 confirm 1007 is the only flag-bearing
account (the server drops connections intermittently — retry on timeout).

## Flag

```
deadface{IDOR_u_2_f1nD_m0r3_Fl4gz}
```

## Files

| file | purpose |
|---|---|
| `solve.py` | end-to-end: login as John Doe + IDOR sweep → flag (with retries) |
| `idor_sweep.py` | the raw 990–1059 sweep that found account 1007 |
| `fetch_text.py` | renders DoomScroll/GhostTown pages to text |
| `evidence/ghosttown_t58.html` | the GhostTown thread that starts the trail |
| `evidence/doomscroll_post267.html` | spookyboi's DoomScroll post |
| `evidence/doomscroll_267_screenshot.png` | the dump-screenshot with the creds |

```
$ python solve.py
[+] logged in as john.doe@example.com (user_id 1)
[*] acct 1007 statements: [... "Ref: deadface{IDOR_u_2_f1nD_m0r3_Fl4gz}" ...]
FLAG: deadface{IDOR_u_2_f1nD_m0r3_Fl4gz}
```
