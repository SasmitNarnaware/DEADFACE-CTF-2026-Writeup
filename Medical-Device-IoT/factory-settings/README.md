# Factory Settings — DeadFace CTF (Challenge #25)

**Category:** Medical Device / Web
**Target:** http://emedra.dctf.io:8080/
**Creator:** @syyntax

## Summary

The Emedra CerebraScan CS-9000 operator console ("ScanWorks") requires technician
credentials. The login page source contains a developer TODO comment left in
before go-live, exposing the temporary QA technician PIN.

## Steps

1. Fetch the kiosk login page:

   ```
   curl http://emedra.dctf.io:8080/api/kiosk/login
   ```

2. Inspect the HTML source. An HTML comment reveals the credentials:

   ```html
   <!-- TODO(dev): REMOVE before go-live — temporary QA technician PIN: deadface{v13w_s0urc3_sav3s_l1v3s} -->
   ```

## Flag

```
deadface{v13w_s0urc3_sav3s_l1v3s}
```

## Lessons

- Never leave credentials or TODO notes in production HTML/JS source.
- "Default credentials" challenges are often solved by reading page source,
  JS bundles, and API responses rather than brute-forcing.
